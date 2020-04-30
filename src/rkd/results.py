
from typing import Union, OrderedDict as OrderedDictType
from collections import OrderedDict
from .syntax import TaskDeclaration, GroupDeclaration
from .inputoutput import SystemIO


STATUS_STARTED = 'started'
STATUS_ERRORED = 'errored'
STATUS_FAILURE = 'failure'
STATUS_SUCCEED = 'succeed'


class QueueItem:
    task: TaskDeclaration
    status: str

    def __init__(self, task: TaskDeclaration, status: str):
        self.task = task
        self.status = status


class ProgressObserver:
    _io: SystemIO
    _tasks: OrderedDictType[str, QueueItem]
    _failed_count: int

    def __init__(self, io: SystemIO):
        self._io = io
        self._tasks = OrderedDict()
        self._failed_count = False

    def task_started(self, declaration: TaskDeclaration, parent: Union[GroupDeclaration, None], args: list):
        """ When task is just started """

        self._tasks[declaration.to_full_name()] = QueueItem(declaration, STATUS_STARTED)

        self._io.info_msg(' >> Executing %s %s %s' % (
            declaration.to_full_name(),
            ' '.join(args),
            ('[parent of ' + parent.get_name() + ']') if parent else ''
        ))

    def task_errored(self, declaration: TaskDeclaration, exception: Exception):
        """ On exception catched in task execution """

        self._tasks[declaration.to_full_name()] = QueueItem(declaration, STATUS_ERRORED)
        self._failed_count += 1

        self._io.print_opt_line()
        self._io.error_msg('The task "%s" was interrupted with an %s' % (
            declaration.to_full_name(),
            str(exception.__class__)
        ))
        self._io.print_separator()
        self._io.print_opt_line()

    def task_failed(self, declaration: TaskDeclaration):
        """ When task returns False """

        self._set_status(declaration, STATUS_FAILURE)
        self._failed_count += 1

        if not declaration.get_task_to_execute().is_silent_in_observer():
            self._io.print_opt_line()
            self._io.error_msg('The task "%s" ended with a failure' % declaration.to_full_name())
            self._io.print_separator()
            self._io.print_opt_line()

    def task_succeed(self, declaration: TaskDeclaration):
        """ When task success """

        self._set_status(declaration, STATUS_SUCCEED)

        if not declaration.get_task_to_execute().is_silent_in_observer():
            self._io.print_opt_line()
            self._io.success_msg('The task "%s" succeed.' % declaration.to_full_name())
            self._io.print_separator()
            self._io.print_opt_line()

    def execution_finished(self):
        """ When all tasks were executed """

        if self.has_at_least_one_failed_task():
            self._io.error_msg('Execution failed with %i/%i failed tasks' % (self._failed_count, len(self._tasks)))
        else:
            self._io.success_msg('Successfully executed %i tasks.' % len(self._tasks))

        self._io.print_opt_line()

    def _set_status(self, declaration: TaskDeclaration, status: str):
        self._tasks[declaration.to_full_name()] = QueueItem(declaration, status)

    def has_at_least_one_failed_task(self) -> bool:
        return self._failed_count > 0
