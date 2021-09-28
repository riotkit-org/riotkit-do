from typing import List, Optional, Tuple, Union
from .argparsing.model import TaskArguments, ArgumentBlock
from .api.syntax import TaskDeclaration, GroupDeclaration, DeclarationBelongingToPipeline
from .context import ApplicationContext
from .exception import TaskNotFoundException
from .aliasgroups import AliasGroup
from .resolver_result import ResolvedTaskBag


class TaskResolver(object):
    """
    Responsible for finding all tasks and:
        - expanding groups (flatten tasks)
        - connecting each task to parent
        - preserve valid order of task validation/execution
    """

    _ctx: ApplicationContext
    _alias_groups: List[AliasGroup]

    # allows to not resolve Blocks twice
    _cache_resolved_blocks: List[ArgumentBlock]

    def __init__(self, ctx: ApplicationContext, alias_groups: List[AliasGroup]):
        self._ctx = ctx
        self._alias_groups = alias_groups
        self._cache_resolved_blocks = []

    def resolve(self, requested_blocks: List[ArgumentBlock]) -> ResolvedTaskBag:
        """
        Resolve selected blocks-of-tasks into TaskDeclaration and filled up ArgumentBlock with TaskDeclaration objects

        :param requested_blocks:

        :return:
        """

        resolved_tasks = ResolvedTaskBag()

        for block in requested_blocks:
            self._resolve_block_details(block)

            for task_request in block.tasks():
                self._resolve_element(task_request, block, resolved_tasks)

        return resolved_tasks

    def _resolve_block_details(self, block: ArgumentBlock):
        """
        Resolve Tasks in @error and @rescue modifiers in Block

        :param block:
        :return:
        """

        if block in self._cache_resolved_blocks:
            return

        # @rescue
        rescue_bag = ResolvedTaskBag()
        self._resolve_elements(block.on_rescue, ArgumentBlock.from_empty(), rescue_bag)
        block.set_resolved_on_rescue(rescue_bag.scheduled_declarations_to_run)

        # @error
        error_bag = ResolvedTaskBag()
        self._resolve_elements(block.on_error, ArgumentBlock.from_empty(), error_bag)
        block.set_resolved_on_error(error_bag.scheduled_declarations_to_run)

        self._cache_resolved_blocks.append(block)

    def _resolve_name_from_alias(self, task_name: str) -> Optional[str]:
        """
        Resolves task group's shortcuts eg. :hb -> :harbor
        """

        for alias in self._alias_groups:
            resolved = alias.append_alias_to_task(task_name)

            if resolved:
                return resolved

    def _resolve_elements(self, requests: List[TaskArguments], block: ArgumentBlock, bag: ResolvedTaskBag):
        for request in requests:
            self._resolve_element(request, block, bag)

    def _resolve_element(self, task_request: TaskArguments, block: ArgumentBlock, bag: ResolvedTaskBag) -> list:
        """
        Checks task by name if it was defined in context, if yes then unpacks declarations and prepares callbacks
        """

        self._ctx.io.internal('Resolving {}'.format(task_request))

        declarations, parent = self._find_tasks_by_name(task_request.name())

        # connect TaskDeclaration to blocks for context
        for declaration in declarations:
            declaration: Union[TaskDeclaration, DeclarationBelongingToPipeline]

            self._ctx.io.internal(f'Attaching declaration={declaration} to block={block}')

            if isinstance(declaration, TaskDeclaration):
                scheduled = bag.add(declaration.clone(), task_request.args(), block, parent)
            else:
                scheduled = bag.add(declaration, task_request.args(), block, parent)

            for block in scheduled.blocks:
                self._resolve_block_details(block)

            self._ctx.io.internal(f'Created {scheduled.debug()}')

        return declarations

    def _find_tasks_by_name(self, name: str) \
            -> Tuple[List[Union[TaskDeclaration, DeclarationBelongingToPipeline]], Optional[TaskDeclaration]]:
        """
        Find a Task - regardless if it is a Pipeline (GroupDeclaration) or just a TaskDeclaration

        :param name:
        :return:
        """

        try:
            ctx_declaration = self._ctx.find_task_by_name(name)

        # maybe a task name is an alias to other task defined by alias groups
        except TaskNotFoundException:
            task_from_alias = self._resolve_name_from_alias(name)

            if not task_from_alias:
                raise

            ctx_declaration = self._ctx.find_task_by_name(task_from_alias)

        self._ctx.io.internal('Resolved as {}'.format(ctx_declaration))

        if isinstance(ctx_declaration, TaskDeclaration):
            declarations: List[TaskDeclaration] = ctx_declaration.to_list()
            parent = None

        # Pipeline support: unpack multiple TaskDeclaration from GroupDeclaration
        elif isinstance(ctx_declaration, GroupDeclaration):
            declarations: List[DeclarationBelongingToPipeline] = ctx_declaration.get_declarations()
            parent = ctx_declaration
        else:
            raise Exception('Cannot resolve task - unknown type "%s"' % str(ctx_declaration))

        return declarations, parent

