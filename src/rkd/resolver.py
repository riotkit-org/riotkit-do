
from typing import List, Callable, Union, Optional
from .argparsing import TaskArguments
from .syntax import TaskDeclaration, GroupDeclaration
from .context import ApplicationContext
from .exception import InterruptExecution
from .exception import TaskNotFoundException
from .aliasgroups import AliasGroup


CALLBACK_DEF = Callable[[TaskDeclaration, Union[GroupDeclaration, None], list], None]


class TaskResolver:
    """
    Responsible for finding all tasks and:
        - expanding groups (flatten tasks)
        - connecting each task to parent
        - preserve valid order of task validation/execution
    """

    _ctx: ApplicationContext
    _alias_groups: List[AliasGroup]

    def __init__(self, ctx: ApplicationContext, alias_groups: List[AliasGroup]):
        self._ctx = ctx
        self._alias_groups = alias_groups

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

    def _resolve_name_from_alias(self, task_name: str) -> Optional[str]:
        """Resolves task group's shortcuts eg. :hb -> :harbor"""

        for alias in self._alias_groups:
            resolved = alias.append_alias_to_task(task_name)

            if resolved:
                return resolved

    def _resolve_element(self, task_request: TaskArguments, callback: CALLBACK_DEF):
        """Checks task by name if it was defined in context, if yes then unpacks declarations and prepares callbacks"""

        try:
            ctx_declaration = self._ctx.find_task_by_name(task_request.name())

        # maybe a task name is an alias to other task defined by alias groups
        except TaskNotFoundException:
            task_from_alias = self._resolve_name_from_alias(task_request.name())

            if not task_from_alias:
                raise

            ctx_declaration = self._ctx.find_task_by_name(task_from_alias)

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
