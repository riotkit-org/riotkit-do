
import os
from typing import Union
from traceback import print_exc
from .argparsing import CommandlineParsingHelper
from .syntax import TaskDeclaration, GroupDeclaration
from .context import ApplicationContext
from .contract import ExecutorInterface, ExecutionContext
from .inputoutput import IO, SystemIO
from .results import ProgressObserver
from .exception import InterruptExecution
from .audit import decide_about_target_log_files


class OneByOneTaskExecutor(ExecutorInterface):
    """ Executes tasks one-by-one, providing a context that includes eg. parsed arguments """

    _ctx: ApplicationContext
    _observer: ProgressObserver
    io: SystemIO

    def __init__(self, ctx: ApplicationContext):
        self._ctx = ctx
        self.io = ctx.io
        self._observer = ProgressObserver(ctx.io)

    def execute(self, declaration: TaskDeclaration, task_num: int, parent: Union[GroupDeclaration, None] = None, args: list = []):
        """ Executes a single task passing the arguments, redirecting/capturing the output and handling the errors """

        result = False
        is_exception = False

        # 1. notify
        self._observer.task_started(declaration, parent, args)

        # 2. parse arguments
        parsed_args = CommandlineParsingHelper.parse(declaration, args)
        log_level: str = parsed_args['log_level']
        log_to_file: str = parsed_args['log_to_file']
        is_silent: bool = parsed_args['silent']
        keep_going: bool = parsed_args['keep_going']
        session_log: bool = os.getenv('RKD_AUDIT_SESSION_LOG', '').lower() in ['true', '1', 'yes']

        # 3. execute
        try:
            io = IO()
            io.set_log_level(log_level if log_level else self.io.get_log_level())

            if is_silent:
                io.silent = is_silent
            else:
                io.inherit_silent(self.io)  # fallback to system-wide

            with io.capture_descriptors(
                    target_files=decide_about_target_log_files(self._ctx, log_to_file, session_log, declaration, task_num)):

                task = declaration.get_task_to_execute()
                task.internal_inject_dependencies(io, self._ctx, self)

                result = task.execute(
                    ExecutionContext(
                        declaration=declaration,
                        parent=parent,
                        args=parsed_args,
                        env=declaration.get_env()
                    )
                )

        # 4. capture result
        except Exception as e:
            # allows to keep going on, even if task fails
            if not keep_going:
                print_exc()
                raise InterruptExecution()

            self._observer.task_errored(declaration, e)
            is_exception = True

        finally:
            if result is True:
                self._observer.task_succeed(declaration, parent)
            else:
                if not is_exception:  # do not do double summary
                    self._observer.task_failed(declaration, parent)

                # break the whole pipeline only if not --keep-going
                if not keep_going:
                    raise InterruptExecution()

    def get_observer(self) -> ProgressObserver:
        return self._observer
