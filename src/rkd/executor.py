
from typing import Union
from .argparsing import CommandlineParsingHelper
from .syntax import TaskDeclaration, GroupDeclaration
from .context import Context
from .contract import ExecutorInterface, ExecutionContext


class OneByOneTaskExecutor(ExecutorInterface):
    """ Executes tasks one-by-one, providing a context that includes eg. parsed arguments """

    _ctx: Context

    def __init__(self, ctx: Context):
        self._ctx = ctx

    def execute(self, task: TaskDeclaration, parent: Union[GroupDeclaration, None] = None, args: list = []):
        print(' >> Executing ' + task.to_full_name())

        task.get_task_to_execute().execute(
            ExecutionContext(
                ctx=self._ctx,
                executor=self,
                declaration=task.to_full_name(),
                parent=parent,
                args=CommandlineParsingHelper.get_parsed_vars_for_task(task, args),
                env=task.get_env()
            )
        )
