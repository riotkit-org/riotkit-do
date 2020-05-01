
from typing import Union
from .argparsing import CommandlineParsingHelper
from .syntax import TaskDeclaration, GroupDeclaration
from .context import Context
from .contract import ExecutorInterface, ExecutionContext
from .inputoutput import IO, SystemIO
from .results import ProgressObserver
from traceback import print_exc


class OneByOneTaskExecutor(ExecutorInterface):
    """ Executes tasks one-by-one, providing a context that includes eg. parsed arguments """

    _ctx: Context
    _observer: ProgressObserver
    io: SystemIO

    def __init__(self, ctx: Context):
        self._ctx = ctx
        self.io = ctx.io
        self._observer = ProgressObserver(ctx.io)

    def execute(self, task: TaskDeclaration, parent: Union[GroupDeclaration, None] = None, args: list = []):
        """ Executes a single task """

        result = False
        is_exception = False

        # 1. notify
        self._observer.task_started(task, parent, args)

        # 2. execute
        parsed_args = CommandlineParsingHelper.get_parsed_vars_for_task(task, args)
        try:
            io = IO()
            io.silent = parsed_args['silent'] if parsed_args['silent'] else self.io.silent  # fallback to system-wide

            with io.capture_descriptors(target_file=parsed_args['log_to_file']):
                result = task.get_task_to_execute().execute(
                    ExecutionContext(
                        io=io,
                        ctx=self._ctx,
                        executor=self,
                        declaration=task.to_full_name(),
                        parent=parent,
                        args=parsed_args,
                        env=task.get_env()
                    )
                )

        # 3. capture result
        except Exception as e:
            # allows to keep going on, even if task fails
            if not parsed_args['keep_going']:
                print_exc()

            self._observer.task_errored(task, e)
            is_exception = True

        finally:
            if result is True:
                self._observer.task_succeed(task, parent)
            else:
                if not is_exception:  # do not do double summary
                    self._observer.task_failed(task, parent)

    def get_observer(self) -> ProgressObserver:
        return self._observer
