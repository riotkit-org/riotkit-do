
import os
from pwd import getpwnam
from pickle import dumps as pickle_dumps
from pickle import loads as pickle_loads
from typing import Union, Optional
from rkd.process import switched_workdir
from ..argparsing.parser import CommandlineParsingHelper
from ..api.syntax import TaskDeclaration, GroupDeclaration
from ..api.contract import TaskInterface
from ..api.contract import ExecutorInterface
from ..api.contract import ExecutionContext
from ..context import ApplicationContext
from ..inputoutput import IO
from ..inputoutput import SystemIO
from ..inputoutput import output_formatted_exception
from ..exception import InterruptExecution, \
    ExecutionRetryException, \
    ExecutionRescueException, \
    ExecutionErrorActionException
from .results import ProgressObserver
from ..audit import decide_about_target_log_files
from ..api.temp import TempManager
from .serialization import FORKED_EXECUTOR_TEMPLATE
from .serialization import get_unpicklable


class OneByOneTaskExecutor(ExecutorInterface):
    """ Executes tasks one-by-one, providing a context that includes eg. parsed arguments """

    _ctx: ApplicationContext
    _observer: ProgressObserver
    io: SystemIO

    def __init__(self, ctx: ApplicationContext, observer: ProgressObserver):
        self._ctx = ctx
        self.io = ctx.io
        self._observer = observer

    def execute(self, declaration: TaskDeclaration, task_num: int, parent: Union[GroupDeclaration, None] = None,
                args: list = None):

        """
        Executes a single task passing the arguments, redirecting/capturing the output and handling the errors
        """

        if args is None:
            args = []

        # 1. notify
        self._observer.task_started(declaration, parent, args)

        # 2. parse arguments
        parsed_args, defined_args = CommandlineParsingHelper.parse(declaration, args)
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

            where_to_store_logs = decide_about_target_log_files(self._ctx, log_to_file, declaration, task_num)

            with io.capture_descriptors(target_files=where_to_store_logs):

                task = declaration.get_task_to_execute()
                task.internal_inject_dependencies(io, self._ctx, self, temp)

                with switched_workdir(workdir):
                    result = self._execute_directly_or_forked(cmdline_become, task, temp, ExecutionContext(
                            declaration=declaration,
                            parent=parent,
                            args=parsed_args,
                            env=declaration.get_env(),
                            defined_args=defined_args
                        ))

        # 4. capture result
        except Exception as e:
            #
            # When: Task has a failure
            #
            temp.finally_clean_up()
            self._on_failure(declaration, keep_going, e, parent)

            return

        #
        # When: Task did not raise exception
        #
        temp.finally_clean_up()

        if result is True:
            self._observer.task_succeed(declaration, parent)
        else:
            self._on_failure(declaration, keep_going, None, parent)

    def _on_failure(self, declaration: TaskDeclaration, keep_going: bool,
                    exception: Optional[Exception] = None,
                    parent: Union[GroupDeclaration, None] = None):

        """
        Executed when task fails - regardless of if it is an Exception raised or just a False returned

        Roles:
            - Block: a domain logic, tracks TaskDeclaration execution
              (only those declarations that are declared in that block)
            - Observer: Observes execution RESULTS to notify user, the console (to set exit code for example).
                        Needs also to be notified, when tasks are retried and when those retried tasks are passing
                        eg. second time ater failing first time
        """

        # block modifiers (issue #50): @retry a task up to X times
        if declaration.block().should_task_be_retried(declaration):
            declaration.block().task_retried(declaration)
            self._observer.task_retried(declaration)

            raise ExecutionRetryException() from exception

        elif declaration.block().should_block_be_retried():
            declaration.block().whole_block_retried(declaration)

            self._observer.group_of_tasks_retried(declaration.block())

            raise ExecutionRetryException(declaration.block().tasks()) from exception

        # regardless of @error & @rescue there should be a visible information that task failed
        self._notify_error(declaration, parent, exception)

        # block modifiers (issue #50): @error and @rescue
        if declaration.block().should_rescue_task():
            self._observer.task_rescue_attempt(declaration)

            raise ExecutionRescueException(declaration.block().on_rescue) from exception

        elif declaration.block().has_action_on_error():
            raise ExecutionErrorActionException(declaration.block().on_error) from exception

        # break the whole pipeline only if not --keep-going
        if not keep_going:
            raise InterruptExecution() from exception

    def _notify_error(self, declaration: TaskDeclaration,
                      parent: Union[GroupDeclaration, None] = None,
                      exception: Optional[Exception] = None):

        """Write to console, notify observers"""

        # distinct between error and failure, first has a stacktrace, second is a logical task failure
        if not exception:
            self._observer.task_failed(declaration, parent)
        else:
            output_formatted_exception(exception, str(declaration.get_task_to_execute().get_full_name()), self.io)
            self._observer.task_errored(declaration, exception)

    def _execute_directly_or_forked(self, cmdline_become: str, task: TaskInterface, temp: TempManager, ctx: ExecutionContext):
        """Execute directly or pass to a forked process
        """

        if task.should_fork() or cmdline_become:
            task.io().debug('Executing task as separate process')
            return self._execute_as_forked_process(cmdline_become, task, temp, ctx)

        return task.execute(ctx)

    @staticmethod
    def _execute_as_forked_process(become: str, task: TaskInterface, temp: TempManager, ctx: ExecutionContext):
        """Execute task code as a separate Python process

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
