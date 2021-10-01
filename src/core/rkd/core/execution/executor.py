
import os
from copy import deepcopy
from pwd import getpwnam
from pickle import dumps as pickle_dumps
from pickle import loads as pickle_loads
from typing import Optional
from rkd.process import switched_workdir
from ..argparsing.model import ArgumentBlock
from ..argparsing.parser import CommandlineParsingHelper
from ..api.syntax import DeclarationScheduledToRun
from ..api.contract import TaskInterface
from ..api.contract import ExecutorInterface
from ..api.contract import ExecutionContext
from ..context import ApplicationContext
from ..inputoutput import IO
from ..inputoutput import SystemIO
from ..inputoutput import output_formatted_exception
from ..exception import InterruptExecution
from .results import ProgressObserver
from ..audit import decide_about_target_log_files
from ..api.temp import TempManager
from .serialization import FORKED_EXECUTOR_TEMPLATE
from .serialization import get_unpicklable
from ..iterator import TaskIterator


class OneByOneTaskExecutor(ExecutorInterface, TaskIterator):
    """
    Executes tasks one-by-one, providing a context that includes eg. parsed arguments
    """

    _ctx: ApplicationContext
    _observer: ProgressObserver
    io: SystemIO

    def __init__(self, ctx: ApplicationContext, observer: ProgressObserver):
        self._ctx = ctx
        self.io = ctx.io
        self._observer = observer

    def fail_fast(self) -> bool:
        return True

    def process_task(self, scheduled: DeclarationScheduledToRun, task_num: int):
        self.execute(scheduled, task_num)

    def execute(self, scheduled_declaration: DeclarationScheduledToRun, task_num: int, inherited: bool = False):
        """
        Prepares all dependencies, then triggers execution
        """

        args = scheduled_declaration.args
        declaration = scheduled_declaration.declaration

        # 1. notify
        self._observer.task_started(scheduled_declaration)

        # 2. parse arguments
        parsed_args, defined_args = CommandlineParsingHelper.parse(scheduled_declaration.declaration, args)
        log_level: str = parsed_args['log_level']
        log_to_file: str = parsed_args['log_to_file']
        is_silent: bool = parsed_args['silent']
        keep_going: bool = parsed_args['keep_going']
        cmdline_become: str = parsed_args['become']
        workdir = parsed_args.get('task_workdir') if parsed_args.get('task_workdir') else declaration.workdir

        # 3. execute
        temp = TempManager()

        try:
            io = IO()
            io.set_log_level(log_level if log_level else self.io.get_log_level())

            if is_silent:
                io.silent = is_silent
            else:
                io.inherit_silent(self.io)  # fallback to system-wide

            where_to_store_logs = decide_about_target_log_files(self._ctx, log_to_file, scheduled_declaration)

            with io.capture_descriptors(target_files=where_to_store_logs):

                task = scheduled_declaration.declaration.get_task_to_execute()
                task.internal_inject_dependencies(io, self._ctx, self, temp)

                with switched_workdir(workdir):
                    result = self._execute_directly_or_forked(cmdline_become, task, temp, ExecutionContext(
                        declaration=scheduled_declaration.declaration,
                        parent=scheduled_declaration.parent,
                        args=parsed_args,
                        env=scheduled_declaration.declaration.get_env(),
                        defined_args=defined_args
                    ))

        # 4. capture result
        except Exception as e:
            #
            # When: Task has a failure
            #
            temp.finally_clean_up()
            self._on_failure(scheduled_declaration, keep_going, task_num, e, inherited=inherited)

            return

        #
        # When: Task did not raise exception
        #
        temp.finally_clean_up()

        if result is True:
            self._observer.task_succeed(scheduled_declaration)
        else:
            self._on_failure(scheduled_declaration, keep_going, task_num, None, inherited=inherited)

    def _on_failure(self, scheduled_declaration: DeclarationScheduledToRun, keep_going: bool, task_num: int,
                    exception: Optional[Exception] = None, inherited: bool = False):
        """
        Executed when task fails: Goes through all nested blocks and tries to rescue the situation or notify an error

        Separated responsibilities:
            - Block: a domain logic, tracks TaskDeclaration execution. Decides if task should be retried, or rescued
              (only those declarations that are declared in that block)
            - Observer: Observes execution RESULTS to notify user, the console (to set exit code for example).
                        Needs also to be notified, when tasks are retried and when those retried tasks are passing
                        eg. second time after failing first time
        """

        blocks = scheduled_declaration.get_blocks_ordered_by_children_to_parent()
        last_block: ArgumentBlock = blocks[0]
        block_num = 0

        self.io.internal(f'declaration={scheduled_declaration}')
        self.io.internal(f'last_block={last_block}')

        if not inherited:
            for block in blocks:
                block_num += 1

                self.io.internal(f'Handling failure of {scheduled_declaration} in block #{block_num} {block}')

                if block.is_default_empty_block:
                    self.io.internal('Skipping default empty block')
                    continue

                # NOTE: we need to mark blocks as resolved to avoid loops, as the execution process is triggered by
                #       upper layer - TaskResolver, that may not be aware of what is done there

                if block.is_already_failed_for(scheduled_declaration.declaration):
                    self.io.internal(f'{scheduled_declaration} already failed in {block}')
                    continue

                is_failure_repaired = self._handle_failure_in_specific_block(
                    scheduled_declaration, exception, block,
                    task_num=task_num
                )

                # if Block modifiers worked, and the Task result is repaired, then do not raise exception at the end
                # also do not process next blocks
                if is_failure_repaired:
                    return

                self.io.internal(f'Marking {scheduled_declaration} as failed in {block}')
                block.mark_as_failed_for(scheduled_declaration)

        # break the whole pipeline only if not --keep-going
        if not keep_going:
            raise InterruptExecution() from exception

    def _handle_failure_in_specific_block(self, scheduled_declaration: DeclarationScheduledToRun,
                                          exception: Exception,
                                          block: ArgumentBlock,
                                          task_num: int) -> bool:

        # ==============================================================================
        #  @retry: Repeat a Task multiple times, until it hits the maximum repeat count
        #          or the repeated Task will end with success
        # ==============================================================================
        while block.should_task_be_retried(scheduled_declaration.declaration):
            block.task_retried(scheduled_declaration.declaration)
            self._observer.task_retried(scheduled_declaration)

            try:
                self.execute(scheduled_declaration, task_num, inherited=True)

            except InterruptExecution:
                continue

            # if not "continue" then it is a success (no exception)
            return True

        # ==============================================================================
        #  @retry-block: Repeat all Tasks in current Block until success, or
        # ==============================================================================
        while block.should_block_be_retried():
            self.io.internal(f'Got block to retry: {block}')
            self._observer.group_of_tasks_retried(block)

            succeed_count = 0
            expected_tasks_to_succeed = len(block.resolved_body_tasks())

            for task_in_block in block.resolved_body_tasks():
                try:
                    self.execute(task_in_block, task_num, inherited=True)

                except InterruptExecution:
                    continue

                # if not raised the exception, then continue not worked
                succeed_count += 1

            if succeed_count == expected_tasks_to_succeed:
                return True

        # regardless of @error & @rescue there should be a visible information that task failed
        self._notify_error(scheduled_declaration, exception)

        # ===================================================================================================
        #  @error: Send an error notification, execute something in case of a failure
        # ===================================================================================================
        if block.has_action_on_error():
            for resolved in block.resolved_error_tasks():
                resolved: DeclarationScheduledToRun

                try:
                    self.execute(resolved, resolved.created_task_num, inherited=True)

                except InterruptExecution:
                    # immediately exit, when any of @on-error Task will fail
                    return False

        # ===================================================================================================
        #  @rescue: Let's execute a Task instead of our original Task in case, when our original Task fails
        # ===================================================================================================
        if block.should_rescue_task():
            self._observer.task_rescue_attempt(scheduled_declaration)

            for resolved in block.resolved_rescue_tasks():
                resolved: DeclarationScheduledToRun

                try:
                    self.execute(resolved, resolved.created_task_num, inherited=True)

                except InterruptExecution:
                    return False  # it is expected, that all @rescue tasks will succeed

            # if there is no any InterruptException, then we rescued the Task!
            return True

        # there were no method that was able to rescue the situation
        self.io.internal('No valid modifier found in Block to change Task result')

        return False

    def _notify_error(self, scheduled_to_run: DeclarationScheduledToRun,
                      exception: Optional[Exception] = None):
        """
        Write to console, notify observers
        """

        # distinct between error and failure, first has a stacktrace, second is a logical task failure
        if not exception:
            self._observer.task_failed(scheduled_to_run)
        else:
            output_formatted_exception(
                exception,
                str(scheduled_to_run.declaration.get_task_to_execute().get_full_name()), self.io
            )
            self._observer.task_errored(scheduled_to_run, exception)

    def _execute_directly_or_forked(self, cmdline_become: str, task: TaskInterface, temp: TempManager,
                                    ctx: ExecutionContext):
        """
        Execute directly or pass to a forked process
        """

        # unset incrementing variables
        ctx.env.pop('RKD_DEPTH') if 'RKD_DEPTH' in ctx.env else None

        env_backup = deepcopy(os.environ)
        os.environ.update(ctx.env)

        if task.should_fork() or cmdline_become:
            task.io().debug('Executing task as separate process')
            return self._execute_as_forked_process(cmdline_become, task, temp, ctx)

        try:
            result = task.execute(ctx)

        finally:
            if not ctx.can_mutate_globals():
                os.environ = env_backup

        return result

    @staticmethod
    def _execute_as_forked_process(become: str, task: TaskInterface, temp: TempManager, ctx: ExecutionContext):
        """
        Execute task code as a separate Python process

        The communication between processes is with serialized data and text files.
        One text file is a script, the task code is passed with stdin together with a whole context
        Second text file is a return from executed task - it can be a boolean or exeception.

        When an exception is returned by a task, then it is reraised there - so the original exception is shown
        without any proxies.
        """

        if not become:
            become = task.get_become_as()

        # prepare file with source code and context
        communication_file = temp.assign_temporary_file()
        task.io().debug('Assigning communication temporary file at "%s"' % communication_file)

        context_to_pickle = {'task': task, 'ctx': ctx, 'communication_file': communication_file}

        try:
            task.io().debug('Serializing context')
            with open(communication_file, 'wb') as f:
                f.write(pickle_dumps(context_to_pickle))

        except (AttributeError, TypeError) as e:
            task.io().error('Cannot fork, serialization failed. ' +
                            'Hint: Tasks that are using internally inner-methods and ' +
                            'lambdas cannot be used with become/fork')
            task.io().error(str(e))

            if task.io().is_log_level_at_least('debug'):
                task.io().error('Pickle trace: ' + str(get_unpicklable(context_to_pickle)))

            return False

        # set permissions to temporary file
        if become:
            task.io().debug('Setting temporary file permissions')
            os.chmod(communication_file, 0o777)

            try:
                getpwnam(become)
            except KeyError:
                task.io().error('Unknown user "%s"' % become)
                return False

        task.io().debug('Executing python code')
        task.py(code=FORKED_EXECUTOR_TEMPLATE, become=become, capture=False, arguments=communication_file)

        # collect, process and pass result
        task.io().debug('Parsing subprocess results from a serialized data')
        with open(communication_file, 'rb') as conn_file:
            task_return = pickle_loads(conn_file.read())

        if isinstance(task_return, Exception):
            task.io().debug('Exception was raised in subprocess, re-raising')
            raise task_return

        return task_return

    def get_observer(self) -> ProgressObserver:
        return self._observer
