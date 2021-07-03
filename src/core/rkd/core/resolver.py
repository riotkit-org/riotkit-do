
from typing import List, Callable, Union, Optional
from .argparsing.model import TaskArguments, ArgumentBlock
from .api.syntax import TaskDeclaration, GroupDeclaration
from .context import ApplicationContext
# todo: verfiy if ExecutionErrorActionException and ExecutionRescueException were properly implemented/handled
#       and if we have tests for that case
from .exception import InterruptExecution, \
    ExecutionRetryException, \
    ExecutionErrorActionException, \
    TaskNotFoundException, ExecutionRescueException, ExecutionRescheduleException, AggregatedResolvingFailure
from .aliasgroups import AliasGroup


CALLBACK_DEF = Callable[[TaskDeclaration, int, Union[GroupDeclaration, None], list], None]


class TaskResolver(object):
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

    def resolve(self, requested_blocks: List[ArgumentBlock], callback: CALLBACK_DEF, fail_fast: bool = True):
        """
        Iterate over flatten list of tasks, one by one and call a callback for each task

        :param requested_blocks:
        :param callback:
        :param fail_fast: Fail immediately - throw exception? Or throw an aggregated exception later?

        :return:
        """

        task_num = 0
        aggregated_exceptions = []

        for block in requested_blocks:
            for task_request in block.tasks():
                task_num += 1

                try:
                    self._resolve_element(task_request, callback, task_num, block)
                except InterruptExecution:
                    return
                except Exception as err:
                    if fail_fast is False:
                        aggregated_exceptions.append(err)
                    else:
                        raise err

        if aggregated_exceptions:
            raise AggregatedResolvingFailure(aggregated_exceptions)

    def _resolve_name_from_alias(self, task_name: str) -> Optional[str]:
        """Resolves task group's shortcuts eg. :hb -> :harbor"""

        for alias in self._alias_groups:
            resolved = alias.append_alias_to_task(task_name)

            if resolved:
                return resolved

    def _resolve_elements(self, requests: List[TaskArguments], callback: CALLBACK_DEF, task_num: int,
                          block: ArgumentBlock) -> None:

        for request in requests:
            self._resolve_element(request, callback, task_num, block)

    def _resolve_element(self, task_request: TaskArguments, callback: CALLBACK_DEF, task_num: int,
                         block: ArgumentBlock) -> None:

        """Checks task by name if it was defined in context, if yes then unpacks declarations and prepares callbacks"""

        self._ctx.io.internal('Resolving {}'.format(task_request))

        try:
            # @todo: Possibly clone required - shell summary shows only 2 tasks executed, when there were executed more but of same type
            ctx_declaration = self._ctx.find_task_by_name(task_request.name())

        # maybe a task name is an alias to other task defined by alias groups
        except TaskNotFoundException:
            task_from_alias = self._resolve_name_from_alias(task_request.name())

            if not task_from_alias:
                raise

            ctx_declaration = self._ctx.find_task_by_name(task_from_alias)

        self._ctx.io.internal('Resolved as {}'.format(ctx_declaration))

        if isinstance(ctx_declaration, TaskDeclaration):
            declarations: List[TaskDeclaration] = ctx_declaration.to_list()
            parent = None
        elif isinstance(ctx_declaration, GroupDeclaration):
            declarations: List[TaskDeclaration] = ctx_declaration.get_declarations()
            parent = ctx_declaration
        else:
            raise Exception('Cannot resolve task - unknown type "%s"' % str(ctx_declaration))

        # connect TaskDeclaration to blocks for context
        declaration_num = 0
        for declaration in declarations:
            declaration: TaskDeclaration
            declarations[declaration_num] = declaration.with_connected_block(block)
            declaration_num += 1

        self._iterate_over_declarations(callback, declarations, task_num, parent, task_request)

    def _iterate_over_declarations(self, callback: CALLBACK_DEF, declarations: list, task_num: int,
                                   parent: Optional[GroupDeclaration], task_request: TaskArguments):

        """Recursively go through all tasks in correct order, executing a callable on each"""

        for declaration in declarations:
            declaration: TaskDeclaration

            if isinstance(declaration, GroupDeclaration):
                self._iterate_over_declarations(
                    callback, declaration.get_declarations(),
                    task_num, declaration, task_request
                )
                continue

            try:
                callback(
                    declaration,
                    task_num,
                    parent,
                    # the arguments there will be mixed in order:
                    #  - first: defined in Makefile
                    #  - second: commandline arguments
                    #
                    #  The argparse in Python will take the second one as priority.
                    #  We do not try to remove duplications there to not increase complexity
                    #  of the solution - it works now.
                    declaration.get_args() + task_request.args()
                )

            #
            # Resolver is able to resolve dynamically additional fallback tasks on-demand
            # The status of the overall pipeline depends on decision of ProgressObserver, the resolver is only
            # resolving and scheduling tasks, not deciding about results
            #

            except ExecutionRetryException as exc:
                # multiple tasks to resolve, then retry
                if exc.args:
                    self._resolve_elements(
                        requests=exc.args,
                        callback=callback,
                        task_num=task_num,
                        block=ArgumentBlock.from_empty()
                    )
                    return

                # single task to retry
                self._iterate_over_declarations(
                    callback=callback,
                    declarations=[declaration],
                    task_num=task_num,
                    parent=parent,
                    task_request=task_request
                )

            except ExecutionRescheduleException as reschedule_action:
                self._resolve_elements(
                    requests=reschedule_action.tasks_to_schedule,
                    callback=callback,
                    task_num=task_num,
                    block=ArgumentBlock.from_empty()
                )
