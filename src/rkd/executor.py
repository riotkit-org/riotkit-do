
from typing import Union
from .argparsing import CommandlineParsingHelper
from .syntax import TaskDeclaration, GroupDeclaration
from .context import Context
from .contract import ExecutorInterface, ExecutionContext
from .inputoutput import IO, SystemIO


class OneByOneTaskExecutor(ExecutorInterface):
    """ Executes tasks one-by-one, providing a context that includes eg. parsed arguments """

    _ctx: Context
    io: SystemIO

    def __init__(self, ctx: Context):
        self._ctx = ctx
        self.io = ctx.io

    def execute(self, task: TaskDeclaration, parent: Union[GroupDeclaration, None] = None, args: list = []):
        """ Executes a single task """

        self.io.info(' >> Executing %s %s' % (
            task.to_full_name(),
            ('[parent: ' + parent.get_name() + ']') if parent else ''
        ))

        parsed_args = CommandlineParsingHelper.get_parsed_vars_for_task(task, args)
        io = IO()
        io.silent = parsed_args['silent']

        with io.capture_descriptors(target_file=parsed_args['log_to_file']):
            task.get_task_to_execute().execute(
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
