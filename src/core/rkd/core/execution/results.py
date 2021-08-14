
from typing import Union, Dict
from ..api.syntax import TaskDeclaration
from ..api.syntax import GroupDeclaration
from ..argparsing.model import ArgumentBlock
from ..inputoutput import SystemIO


STATUS_STARTED = 'started'
STATUS_ERRORED = 'errored'
STATUS_FAILURE = 'failure'
STATUS_SUCCEED = 'succeed'

"""
Can be treated as "succeed" because "in-rescue" means that we don't check task status, instead we start a new task
and check that new rescue-task status instead of failed task status
"""
STATUS_RESCUE_STATE = 'in-rescue'


class TaskResult(object):
    task: TaskDeclaration
    status: str

    def __init__(self, task: TaskDeclaration, status: str):
        self.task = task
        self.status = status

    def has_succeed(self) -> bool:
        return self.status in [STATUS_SUCCEED, STATUS_RESCUE_STATE]


class ProgressObserver(object):
    """
    Carefuly tracks tasks execution progress, have answers to questions such as:
        - were there any tasks failed?

    This service is a REGISTRY.
    """

    _io: SystemIO
    _executed_tasks: Dict[str, TaskResult]

    def __init__(self, io: SystemIO):
        self._io = io
        self._executed_tasks = {}

    @staticmethod
    def _format_parent_task(parent: Union[GroupDeclaration, None]) -> str:
        return ('[part of ' + parent.get_name() + ']') if parent else ''

    def task_started(self, declaration: TaskDeclaration, parent: Union[GroupDeclaration, None], args: list):
        """ When task is just started """

        self._executed_tasks[declaration.get_unique_id()] = TaskResult(declaration, STATUS_STARTED)

        self._io.info_msg(' >> Executing %s %s %s' % (
            declaration.to_full_name(),
            ' '.join(args),
            self._format_parent_task(parent)
        ))

    def task_errored(self, declaration: TaskDeclaration, exception: Exception):
        """ On exception catched in task execution """

        self._set_status(declaration, STATUS_ERRORED)

        self._io.print_opt_line()
        self._io.error_msg('The task "%s" was interrupted with an %s' % (
            declaration.to_full_name(),
            str(exception.__class__)
        ))
        self._io.print_separator()
        self._io.print_opt_line()

    def task_failed(self, declaration: TaskDeclaration, parent: Union[GroupDeclaration, None]):
        """ When task returns False """

        self._set_status(declaration, STATUS_FAILURE)

        if not declaration.get_task_to_execute().is_silent_in_observer():
            self._io.print_opt_line()
            self._io.error_msg('The task "%s" %s ended with a failure' % (
                declaration.to_full_name(),
                self._format_parent_task(parent)
            ))
            self._io.print_separator()
            self._io.print_opt_line()

    def task_succeed(self, declaration: TaskDeclaration, parent: Union[GroupDeclaration, None]):
        """ When task success """

        self._set_status(declaration, STATUS_SUCCEED)

        if not declaration.get_task_to_execute().is_silent_in_observer():
            self._io.print_opt_line()
            self._io.success_msg('The task "%s" %s succeed.' % (
                declaration.to_full_name(),
                self._format_parent_task(parent)
            ))
            self._io.print_separator()
            self._io.print_opt_line()

    def execution_finished(self):
        """
        When all tasks were executed - the TaskExecutor finished its job
        """

        if self.is_at_least_one_task_failing():
            self._io.error_msg('Execution failed with %i failed tasks of %i total tasks scheduled for execution' % (
                self.count_failed_tasks(), len(self._executed_tasks)
            ))
        else:
            self._io.success_msg('Successfully executed %i tasks.' % len(self._executed_tasks))

        self._io.print_opt_line()

    def _set_status(self, declaration: TaskDeclaration, status: str):
        """Internally mark given task as done + save status"""

        self._io.internal('{} task, unique_id={}, status={}'.format(str(declaration), declaration.get_unique_id(), status))
        self._executed_tasks[declaration.get_unique_id()] = TaskResult(declaration, status)

    def is_at_least_one_task_failing(self) -> bool:
        return self.count_failed_tasks() >= 1

    def count_failed_tasks(self) -> int:
        return len({
            k: v for k, v in self._executed_tasks.items() if not v.has_succeed()
        }.values())

    def group_of_tasks_retried(self, block: ArgumentBlock):
        """
        When a block failed and needs to be retried (even intermediate success steps)
        """

        executed_tasks_that_belongs_to_block = {
            k: v for k, v in self._executed_tasks.items() if v.task.block() is block
        }

        for declaration in executed_tasks_that_belongs_to_block.values():
            self.task_retried(declaration)

    def task_retried(self, declaration: TaskDeclaration):
        self._io.warn_msg('Task "{}" was retried'.format(declaration.to_full_name()))
        self._set_status(declaration, STATUS_STARTED)

    def task_rescue_attempt(self, declaration: TaskDeclaration):
        self._io.warn_msg('Task "{}" rescue attempt started'.format(declaration.to_full_name()))
        self._set_status(declaration, STATUS_RESCUE_STATE)
