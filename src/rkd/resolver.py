
from typing import List, Callable, Union
from .argparsing import TaskArguments
from .syntax import TaskDeclaration, GroupDeclaration
from .context import ApplicationContext
from .exception import InterruptExecution


CALLBACK_DEF = Callable[[TaskDeclaration, Union[GroupDeclaration, None], list], None]


class TaskResolver:
    """
    Responsible for finding all tasks and:
        - expanding groups (flatten tasks)
        - connecting each task to parent
        - preserve valid order of task validation/execution
    """

    _ctx: ApplicationContext

    def __init__(self, ctx: ApplicationContext):
        self._ctx = ctx

    def resolve(self, requested_tasks: List[TaskArguments], callback: CALLBACK_DEF):
        """
        Iterate over flatten list of tasks, one by one and call a callback for each task

        :param requested_tasks:
        :param callback:
        :return:
        """

        for task_request in requested_tasks:
            try:
                self._resolve_element(task_request, callback)
            except InterruptExecution:
                return

    def _resolve_element(self, task_request: TaskArguments, callback: CALLBACK_DEF):
        ctx_declaration = self._ctx.find_task_by_name(task_request.name())

        if isinstance(ctx_declaration, TaskDeclaration):
            declarations = ctx_declaration.to_list()
            parent = None
        elif isinstance(ctx_declaration, GroupDeclaration):
            declarations = ctx_declaration.get_declarations()
            parent = ctx_declaration
        else:
            raise Exception('Cannot resolve task - unknown type "%s"' % str(ctx_declaration))

        for declaration in declarations:
            callback(
                declaration,
                parent,
                # the arguments there will be mixed in order:
                #  - first: defined in Makefile
                #  - second: commandline arguments
                #
                #  The argparse in Python will take the second one as priority.
                #  We do not try to remove duplications there to not increase complexity of the solution - it works now.
                declaration.get_args() + task_request.args()
            )
