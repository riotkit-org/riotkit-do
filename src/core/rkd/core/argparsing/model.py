from copy import deepcopy
from typing import List, Dict
from uuid import uuid4


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

    # Tasks ready to be used, resolved on the TaskResolver stage
    _on_rescue_tasks: List['TaskDeclaration']
    _on_error_tasks: List['TaskDeclaration']
    _body_tasks: List['TaskDeclaration']

    # the state
    _raw_attributes: dict
    _retry_counter_per_task: Dict['TaskDeclaration', int]
    _retry_counter_on_whole_block: int
    _debug_id: str
    _failed_tasks: List['TaskDeclaration']
    _is_default_block: bool

    def __init__(self, body: List[str] = None, rescue: str = '', error: str = '', retry: int = 0,
                 retry_block: int = 0):
        """
        :param body Can be empty - it means that block will have tasks filled up later
        """

        self._debug_id = uuid4().hex

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
        self._failed_tasks = []
        self._is_default_block = False

        # lazy-filled by TaskResolver on later stage
        self._body_tasks = []

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
        # instance._is_default_block = True

        return instance

    @classmethod
    def create_default_block(cls, body: List[str], tasks: List[TaskArguments]) -> 'ArgumentBlock':
        new_block = cls(body).clone_with_tasks(tasks)
        new_block._is_default_block = True

        return new_block

    def clone_with_tasks(self, tasks_arguments: List[TaskArguments]):
        cloned = deepcopy(self)
        cloned._tasks = tasks_arguments

        return cloned

    def tasks(self) -> List[TaskArguments]:
        """
        Tasks as text arguments - e.g. :sh -c "test 123"
        :return:
        """

        return self._tasks

    def resolved_body_tasks(self) -> List['DeclarationScheduledToRun']:
        """
        Resolved tasks - instances of TaskDeclaration as a fact of resolved relation between Block <=> TaskDeclaration
        by TaskResolver
        :return:
        """

        return self._body_tasks

    def resolved_error_tasks(self) -> List['DeclarationScheduledToRun']:
        return self._on_error_tasks

    def resolved_rescue_tasks(self) -> List['DeclarationScheduledToRun']:
        return self._on_rescue_tasks

    def get_remaining_tasks(self, after) -> List['DeclarationScheduledToRun']:
        """
        Gets all tasks that are after "starting_from" declaration on the list in the block

        Given: A, B, C, D
        We want all tasks after B
        We expect to get C, D

        :param after:
        :return:
        """

        remaining = []
        found = False

        for declaration in self.resolved_body_tasks():
            if declaration == after:
                found = True
                continue

            if found:
                remaining.append(declaration)

        return remaining

    def with_tasks_from_first_block(self, blocks: List['ArgumentBlock']):
        try:
            return self.clone_with_tasks(blocks[0]._tasks)
        except IndexError:
            return self

    def raw_attributes(self) -> dict:
        return self._raw_attributes

    def register_resolved_task(self, task: 'DeclarationScheduledToRun'):
        """
        Internal use only - TaskResolver needs this method to apply relation between Block and TaskDeclaration
                            through DeclarationScheduledToRun
        :return:
        """

        if task in self._body_tasks:
            return

        self._body_tasks.append(task)

    def should_task_be_retried(self, declaration):
        # no retry available at all
        if self.retry_per_task < 1:
            return False

        # has to retry, but it is a first time
        if declaration not in self._retry_counter_per_task:
            return True

        return self._retry_counter_per_task[declaration] < self.retry_per_task

    def task_retried(self, declaration):
        """
        Takes notification from external source to internally note that given task was retried
        """

        if declaration not in self._retry_counter_per_task:
            self._retry_counter_per_task[declaration] = 0

        self._retry_counter_per_task[declaration] += 1

    def whole_block_retried(self):
        """
        When all tasks from this block should be retried
        :return:
        """
        self._retry_counter_on_whole_block += 1

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

    @property
    def how_many_times_retried_block(self):
        return self._retry_counter_on_whole_block

    def __str__(self):
        text = str(self.body)

        try:
            text += ', ' + str(self.tasks())
        except AttributeError:
            pass

        return f'ArgumentBlock<{text}, unique_id={self._debug_id}>'

    def id(self) -> str:
        return self._debug_id

    def mark_as_failed_for(self, declaration):
        """
        Marks that Task already failed for this block, after all retries, etc.

        :param declaration:
        :return:
        """

        self._failed_tasks.append(declaration)

    def set_parsed_error_handler(self, tasks_arguments: List[TaskArguments]) -> None:
        """
        Stage 1: Parsing

        :param tasks_arguments:
        :return:
        """

        self.on_error = tasks_arguments

    def set_parsed_rescue(self, tasks_arguments: List[TaskArguments]) -> None:
        """
        Stage 1: Parsing

        :param tasks_arguments:
        :return:
        """

        self.on_rescue = tasks_arguments

    def set_resolved_on_rescue(self, on_rescue: List['TaskDeclaration']):
        """
        Stage 2: Execution

        :param on_rescue:
        :return:
        """

        self._on_rescue_tasks = on_rescue

    def set_resolved_on_error(self, on_error: List['TaskDeclaration']):
        """
        Stage 2: Execution

        :param on_error:
        :return:
        """

        self._on_error_tasks = on_error

    def is_already_failed_for(self, declaration):
        return declaration in self._failed_tasks

    @property
    def is_default_empty_block(self):
        return self._is_default_block
