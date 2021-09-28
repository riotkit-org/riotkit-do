from datetime import datetime
from typing import Union, Dict, List
from ..api.syntax import DeclarationScheduledToRun
from ..api.syntax import GroupDeclaration
from ..argparsing.model import ArgumentBlock
from ..inputoutput import SystemIO


STATUS_STARTED = 'started'
STATUS_RETRIED = 'retried'
STATUS_ERRORED = 'errored'
STATUS_FAILURE = 'failure'
STATUS_SUCCEED = 'succeed'

"""
Can be treated as "succeed" because "in-rescue" means that we don't check task status, instead we start a new task
and check that new rescue-task status instead of failed task status
"""
STATUS_RESCUE_STATE = 'in-rescue'


class TaskResult(object):
    task: DeclarationScheduledToRun
    status: str
    time: datetime

    def __init__(self, task: DeclarationScheduledToRun, status: str):
        self.task = task
        self.status = status
        self.time = datetime.now()

    def has_succeed(self) -> bool:
        return self.status in [STATUS_SUCCEED, STATUS_RESCUE_STATE]


class ProgressObserver(object):
    """
    Carefuly tracks tasks execution progress, have answers to questions such as:
        - were there any tasks failed?

    This service is a REGISTRY.
    """

    _io: SystemIO
    __executed_tasks: Dict[str, TaskResult]
    __history: List[TaskResult]
    __task_numbers: Dict[DeclarationScheduledToRun, int]

    def __init__(self, io: SystemIO):
        self._io = io
        self.__executed_tasks = {}
        self.__history = []
        self.__task_numbers = {}

    @staticmethod
    def _format_parent_task(parent: Union[GroupDeclaration, None]) -> str:
        return ('[part of ' + parent.get_name() + ']') if parent else ''

    def task_started(self, scheduled_declaration: DeclarationScheduledToRun):
        """
        When task is just started
        """

        is_retry = scheduled_declaration.unique_id() in self.__executed_tasks

        self._set_status(scheduled_declaration, STATUS_STARTED)

        self._io.info_msg(' >> [{task_num}] {action} `{full_name}` {parent}'.format(
            task_num=self.task_num(scheduled_declaration),
            action='Retrying' if is_retry else 'Executing',
            full_name=scheduled_declaration.repr_as_invoked_task,
            parent=self._format_parent_task(scheduled_declaration.parent)
        ))

    def task_errored(self, scheduled_declaration: DeclarationScheduledToRun, exception: Exception):
        """ On exception catched in task execution """

        self._set_status(scheduled_declaration, STATUS_ERRORED)

        self._io.print_opt_line()
        self._io.error_msg('The task "%s" was interrupted with an %s' % (
            scheduled_declaration.repr_as_invoked_task,
            str(exception.__class__)
        ))
        self._io.print_separator(status=False)
        self._io.print_opt_line()

    def task_failed(self, scheduled_to_run: DeclarationScheduledToRun):
        """ When task returns False """

        self._set_status(scheduled_to_run, STATUS_FAILURE)

        if not scheduled_to_run.declaration.get_task_to_execute().is_silent_in_observer():
            self._io.print_opt_line()
            self._io.error_msg('The task `{name}` {parent} ended with a failure'.format(
                name=scheduled_to_run.repr_as_invoked_task,
                parent=self._format_parent_task(scheduled_to_run.parent)
            ))
            self._io.print_separator(status=False)
            self._io.print_opt_line()
            self._io.print_opt_line()

    def task_succeed(self, scheduled_to_run: DeclarationScheduledToRun):
        """ When task success """

        self._set_status(scheduled_to_run, STATUS_SUCCEED)

        if not scheduled_to_run.declaration.get_task_to_execute().is_silent_in_observer():
            self._io.print_opt_line()
            self._io.success_msg('The task `{current}`{parent} succeed.'.format(
                current=scheduled_to_run.repr_as_invoked_task,
                parent=(' ' + self._format_parent_task(scheduled_to_run.parent)).rstrip()
            ))
            self._io.print_separator()
            self._io.print_opt_line()
            self._io.print_opt_line()

    def execution_finished(self):
        """
        When all tasks were executed - the TaskExecutor finished its job
        """

        if self.is_at_least_one_task_failing():
            self._io.error_msg('Execution failed with %i failed tasks of %i total tasks scheduled for execution' % (
                self.count_failed_tasks(), len(self.__executed_tasks)
            ))
        else:
            self._io.success_msg('Successfully executed %i tasks.' % len(self.__executed_tasks))

        self._io.print_opt_line()

    def _set_status(self, scheduled_to_run: DeclarationScheduledToRun, status: str):
        """
        Internally mark given task as done + save status
        """

        self._io.internal('{} task, unique_id={}, status={}'.format(str(scheduled_to_run),
                                                                    scheduled_to_run.unique_id(), status))
        self.__executed_tasks[scheduled_to_run.unique_id()] = TaskResult(scheduled_to_run, status)
        self.__history.append(self.__executed_tasks[scheduled_to_run.unique_id()])

        # collect tasks numbering - only when task is ran first time (not a retry)
        if status == STATUS_STARTED and scheduled_to_run not in self.__task_numbers:
            self.__task_numbers[scheduled_to_run] = len(self.__task_numbers) + 1

    def is_at_least_one_task_failing(self) -> bool:
        return self.count_failed_tasks() >= 1

    def count_failed_tasks(self) -> int:
        return len({
            k: v for k, v in self.__executed_tasks.items() if not v.has_succeed()
        }.values())

    def group_of_tasks_retried(self, block: ArgumentBlock):
        """
        When a block failed and needs to be retried (even intermediate success steps)
        """

        self._io.info_msg(f' >> Retrying block of tasks (retry {block.how_many_times_retried_block + 1})')
        block.whole_block_retried()

    def task_retried(self, scheduled_to_run: DeclarationScheduledToRun):
        self._set_status(scheduled_to_run, STATUS_RETRIED)

    def task_rescue_attempt(self, scheduled_to_run: DeclarationScheduledToRun):
        self._io.info_msg(' >> [{num}] Task "{name}" rescue attempt started'.format(
            num=self.task_num(scheduled_to_run),
            name=scheduled_to_run.repr_as_invoked_task
        ))
        self._set_status(scheduled_to_run, STATUS_RESCUE_STATE)

    @property
    def history(self) -> List[TaskResult]:
        """
        Shows a list of all performed actions

        :return:
        """

        return self.__history

    def print_event_history(self):
        body = []
        event_num = 0

        for element in self.history:
            event_num += 1
            body.append([
                event_num,
                element.time,
                self.task_num(element.task),
                element.task.repr_as_invoked_task,
                element.status,
                element.task.count_non_empty_blocks()
            ])

        self._io.outln(
            self._io.format_table(
                ['Event', 'Time', 'Runtime ID', 'Callable string', 'Status', 'Blocks count'],
                body
            )
        )

    def task_num(self, scheduled_to_run: DeclarationScheduledToRun) -> int:
        return self.__task_numbers[scheduled_to_run]
