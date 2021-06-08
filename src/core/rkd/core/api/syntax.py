
"""
SYNTAX (part of API)
====================

Classes used in a declaration syntax in makefile.py

"""

from typing import List, Dict, Optional
from copy import deepcopy
from .contract import TaskDeclarationInterface
from .contract import GroupDeclarationInterface
from .contract import TaskInterface
from .inputoutput import get_environment_copy
from ..argparsing.model import ArgumentBlock
from ..exception import DeclarationException
from uuid import uuid4


class TaskDeclaration(TaskDeclarationInterface):
    _task: TaskInterface
    _env: Dict[str, str]       # environment at all
    _user_defined_env: list    # list of env variables overridden by user
    _args: List[str]
    _block: ArgumentBlock = None
    _unique_id: str
    _workdir: Optional[str]

    def __init__(self, task: TaskInterface, env: Dict[str, str] = None, args: List[str] = None, workdir: str = None):
        if env is None:
            env = {}

        if args is None:
            args = []

        if not isinstance(task, TaskInterface):
            raise DeclarationException('Invalid class: TaskDeclaration needs to take TaskInterface as task argument')

        self._unique_id = uuid4().hex
        self._task = task
        self._env = merge_env(env)
        self._args = args
        self._workdir = workdir
        self._user_defined_env = list(env.keys())

    def to_full_name(self):
        return self._task.get_full_name()

    def with_env(self, envs: Dict[str, str]):
        """ Immutable environment setter. Produces new object each time. """

        copy = self._clone()
        copy._env = envs

        return copy

    def with_args(self, args: List[str]):
        """ Immutable arguments setter. Produces new object each time """

        copy = self._clone()
        copy._args = args

        return copy

    def with_user_overridden_env(self, env_list: list):
        """ Immutable arguments setter. Produces new object each time """

        copy = self._clone()
        copy._user_defined_env = env_list

        return copy

    def with_connected_block(self, block: ArgumentBlock):
        """Immutable arguments setter. Produces new object each time
           Block should be a REFERENCE to an object, not a copy
        """

        copy = self._clone()
        copy._block = block

        return copy

    def _clone(self) -> 'TaskDeclaration':
        """Clone securely the object. There fields shared across objects as references could be kept"""

        copy = deepcopy(self)
        copy._unique_id = uuid4().hex
        copy._block = self._block

        return copy

    def get_args(self) -> List[str]:
        return self._args

    def get_task_to_execute(self) -> TaskInterface:
        return self._task

    def to_list(self) -> list:
        return [self]

    def get_env(self):
        return self._env

    def get_user_overridden_envs(self) -> list:
        """ Lists environment variables which were overridden by user """

        return self._user_defined_env

    def get_group_name(self) -> str:
        split = self.to_full_name().split(':')
        return split[1] if len(split) >= 3 else ''

    def get_task_name(self) -> str:
        split = self.to_full_name().split(':')

        if len(split) >= 3:
            return split[2]

        try:
            return split[1]
        except KeyError:
            return self.to_full_name()

    def get_description(self) -> str:
        task = self.get_task_to_execute()

        if task.get_description():
            return task.get_description()

        return task.__doc__.strip().split("\n")[0] if task.__doc__ else ''

    def get_full_description(self) -> str:
        task = self.get_task_to_execute()

        if task.get_description():
            return task.get_description()

        return task.__doc__.strip() if task.__doc__ else ''

    def block(self) -> ArgumentBlock:
        return self._block

    @staticmethod
    def parse_name(name: str) -> tuple:
        split = name.split(':')
        task_name = ":" + split[-1]
        group = ":".join(split[:-1])

        return task_name, group

    def format_task_name(self, name: str) -> str:
        return self.get_task_to_execute().format_task_name(name)

    def get_unique_id(self) -> str:
        """
        Unique ID of a declaration is a TEMPORARY ID created during runtime to distinct even very similar declarations
        """
        return self._unique_id

    @property
    def workdir(self) -> str:
        if not self._workdir:
            return '.'

        return self._workdir

    def __str__(self):
        return 'TaskDeclaration<%s>' % self.get_task_to_execute().get_full_name()


class GroupDeclaration(GroupDeclarationInterface):
    """ Internal DTO: Processed definition of TaskAliasDeclaration into TaskDeclaration """

    _name: str
    _declarations: List[TaskDeclaration]
    _description: str

    def __init__(self, name: str, declarations: List[TaskDeclaration], description: str):
        self._name = name
        self._declarations = declarations
        self._description = description

    def get_declarations(self) -> List[TaskDeclaration]:
        return self._declarations

    def get_name(self) -> str:
        return self._name

    def get_group_name(self) -> str:
        split = self._name.split(':')
        return split[1] if len(split) >= 3 else ''

    def get_task_name(self) -> str:
        split = self._name.split(':')

        if len(split) >= 3:
            return split[2]

        try:
            return split[1]
        except KeyError:
            return self._name

    def to_full_name(self):
        return self.get_name()

    def get_description(self) -> str:
        return self._description

    def format_task_name(self, name: str) -> str:
        return name


class TaskAliasDeclaration:
    """ Allows to define a custom task name that triggers other tasks in proper order """

    _name: str
    _arguments: List[str]
    _env: Dict[str, str]
    _user_defined_env: list  # list of env variables overridden by user
    _description: str

    def __init__(self, name: str, to_execute: List[str], env: Dict[str, str] = {}, description: str = ''):
        self._name = name
        self._arguments = to_execute
        self._env = merge_env(env)
        self._user_defined_env = list(env.keys())
        self._description = description

    def get_name(self):
        return self._name

    def get_arguments(self) -> List[str]:
        return self._arguments

    def get_env(self) -> Dict[str, str]:
        return self._env

    def get_user_overridden_envs(self) -> list:
        """ Lists environment variables which were overridden by user """

        return self._user_defined_env

    def get_description(self) -> str:
        return self._description


def merge_env(env: Dict[str, str]):
    """Merge custom environment variables set per-task with system environment
    """

    merged_dict = deepcopy(env)
    merged_dict.update(get_environment_copy())

    return merged_dict
