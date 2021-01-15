from copy import deepcopy
from typing import List


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
    body: str
    on_rescue: str = ''
    on_error: str = ''
    retry: int = 0
    _tasks: List[TaskArguments]

    def __init__(self, body: str = '', rescue: str = '', error: str = '', retry: int = 0):
        """
        :param body Can be empty - it means that block will have tasks filled up later
        """

        self.body = body
        self.on_rescue = rescue
        self.on_error = error
        self.retry = retry

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
