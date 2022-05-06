from copy import deepcopy
from typing import List, Dict


class TaskArguments(object):
    """
    Task name + commandline switches model
    """

    _name: str
    _args: list

    def __init__(self, task_name: str, args: list):
        self._name = task_name
        self._args = args

    def __repr__(self):
        return 'TaskCall<%s (%s)>' % (self._name, str(self._args))

    def name(self):
        return self._name

    def args(self):
        return self._args

    def with_args(self, new_args: list) -> 'TaskArguments':
        clone = deepcopy(self)
        clone._args = new_args

        return clone


class ArgumentBlock(object):
    """
    ArgumentBlock
    =============

    Stores information about construction of blocks:
        {@block @error :notify @retry 2}:task1 --param1=value1 :task2{/@block}

    Lifetime:
        - Initially could store *body* (raw string, from example: ":task1 --param1=value1 :task2")
        - Later parsers are filling up the *_tasks* attribute with parsed TaskArguments
        - At last stage the *RKD's Executor component* is reading from ArgumentBlock and deciding if task should be
          retried, if there should be any error handling. The *_retry_counter_per_task* and *_retry_counter_on_whole_block*
          fields are mutable to track the progress of error handling

    Notice: Fields like on_error, on_rescue are filled up after block creation ex. in CommandlineParsingHelper class
            See usages of set_parsed_error_handler(), set_parsed_rescue()
    """

    body: List[str]
    on_rescue: List[TaskArguments]
    on_error: List[TaskArguments]
    retry_per_task: int = 0

    _tasks: List[TaskArguments]
    _raw_attributes: dict
    _retry_counter_per_task: Dict['TaskDeclaration', int]
    _retry_counter_on_whole_block: int

    def __init__(self, body: List[str] = None, rescue: str = '', error: str = '', retry: int = 0,
                 retry_block: int = 0):
        """
        :param body Can be empty - it means that block will have tasks filled up later
        """

        if body is None:
            body = []

        self.body = body
        try:
            self.retry_per_task = int(retry)
        except ValueError:
            self.retry_per_task = 0

        try:
            self.retry_whole_block = int(retry_block)
        except ValueError:
            self.retry_whole_block = 0

        # lazy-filled by parser on later stage
        self.on_rescue = []
        self.on_error = []
        self._retry_counter_per_task = {}
        self._retry_counter_on_whole_block = 0

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

    def clone_with_tasks(self, tasks_arguments: List[TaskArguments]):
        cloned = deepcopy(self)
        cloned._tasks = tasks_arguments

        return cloned

    def tasks(self) -> List[TaskArguments]:
        return self._tasks

    def with_tasks_from_first_block(self, blocks: List['ArgumentBlock']):
        try:
            return self.clone_with_tasks(blocks[0]._tasks)
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
        if self.retry_per_task < 1:
            return False

        # has to retry, but it is a first time
        if declaration not in self._retry_counter_per_task:
            return True

        return self._retry_counter_per_task[declaration] < self.retry_per_task

    def task_retried(self, declaration):
        """Takes notification from external source to internally note that given task was retried"""

        if declaration not in self._retry_counter_per_task:
            self._retry_counter_per_task[declaration] = 0

        self._retry_counter_per_task[declaration] += 1

    def whole_block_retried(self, declaration):
        pass

    def should_rescue_task(self):
        """
        Decides if given task should have executed a rescue set of tasks
        """

        return len(self.on_rescue) > 0

    def has_action_on_error(self):
        """
        Answers if there is a set of tasks that should be notified on error
        """

        return len(self.on_error) > 0

    def should_block_be_retried(self) -> bool:
        """
        Can the whole block of tasks be repeated from scratch?
        """

        if self.retry_whole_block < 1:
            return False

        # actual state < declared maximum
        return self._retry_counter_on_whole_block < self.retry_whole_block

    def __str__(self):
        text = str(self.body)

        try:
            text += ', ' + str(self.tasks())
        except AttributeError:
            pass

        return 'ArgumentBlock<' + text + '>'
