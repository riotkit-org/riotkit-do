from copy import deepcopy
from typing import List, Dict


class TaskArguments(object):
    _name: str
    _args: list

    def __init__(self, task_name: str, args: list):
        self._name = task_name
        self._args = args

    def __repr__(self):
        return 'Task<%s (%s)>' % (self._name, str(self._args))

    def name(self):
        return self._name

    def args(self):
        return self._args

    def with_args(self, new_args: list) -> 'TaskArguments':
        clone = deepcopy(self)
        clone._args = new_args

        return clone


class ArgumentBlock(object):
    body: List[str]
    on_rescue: List[TaskArguments]
    on_error: List[TaskArguments]
    retry: int = 0

    _tasks: List[TaskArguments]
    _raw_attributes: dict
    _retry_counter: Dict['TaskDeclaration', int]

    def __init__(self, body: List[str] = None, rescue: str = '', error: str = '', retry: int = 0):
        """
        :param body Can be empty - it means that block will have tasks filled up later
        """

        if body is None:
            body = []

        self.body = body
        try:
            self.retry = int(retry)
        except ValueError:
            self.retry = 0

        self.on_rescue = []
        self.on_error = []
        self._retry_counter = {}

        # those attributes will be lazy-parsed on later processing stage
        self._raw_attributes = {
            'rescue': rescue,
            'error': error,
        }

    @staticmethod
    def from_empty() -> 'ArgumentBlock':
        """Dummy instance"""

        instance = ArgumentBlock(
            body=[], rescue='', error='', retry=0
        )

        instance.set_parsed_rescue([])
        instance.set_parsed_error_handler([])

        return instance

    def with_tasks(self, tasks_arguments: List[TaskArguments]):
        cloned = deepcopy(self)
        cloned._tasks = tasks_arguments

        return cloned

    def tasks(self) -> List[TaskArguments]:
        return self._tasks

    def with_tasks_from_first_block(self, blocks: List['ArgumentBlock']):
        try:
            return self.with_tasks(blocks[0]._tasks)
        except IndexError:
            return self

    def raw_attributes(self) -> dict:
        return self._raw_attributes

    def set_parsed_error_handler(self, tasks_arguments: List[TaskArguments]) -> None:
        self.on_error = tasks_arguments

    def set_parsed_rescue(self, tasks_arguments: List[TaskArguments]) -> None:
        self.on_rescue = tasks_arguments

    def should_task_be_retried(self, declaration):
        # no retry available at all
        if self.retry < 1:
            return False

        # has to retry, but it is a first time
        if declaration not in self._retry_counter:
            return True

        return self._retry_counter[declaration] < self.retry

    def task_retried(self, declaration):
        """Takes notification from external source to internally note that given task was retried"""

        if declaration not in self._retry_counter:
            self._retry_counter[declaration] = 0

        self._retry_counter[declaration] += 1

    def should_rescue(self):
        """Decides if given task should have executed a rescue set of tasks"""

        return len(self.on_rescue) > 0

    def has_action_on_error(self):
        """Asks if there is a set of tasks that should be notified on error"""

        return len(self.on_error) > 0
