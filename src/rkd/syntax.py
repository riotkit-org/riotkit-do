
from typing import List, Dict
from copy import deepcopy
from .contract import TaskDeclarationInterface, GroupDeclarationInterface, TaskInterface


class TaskDeclaration(TaskDeclarationInterface):
    _task: TaskInterface
    _env: Dict[str, str]
    _args: List[str]

    def __init__(self, task: TaskInterface, env: Dict[str, str] = [], args: List[str] = []):
        self._task = task
        self._env = env
        self._args = args

    def to_full_name(self):
        return self._task.get_full_name()

    def with_env(self, envs: Dict[str, str]):
        """ Immutable environment setter. Produces new object each time. """

        copy = deepcopy(self)
        copy._env = envs

        return copy

    def with_args(self, args: List[str]):
        """ Immutable arguments setter. Produces new object each time """

        copy = deepcopy(self)
        copy._args = args

        return copy

    def get_args(self) -> List[str]:
        return self._args

    def get_task_to_execute(self) -> TaskInterface:
        return self._task

    def to_dict(self) -> dict:
        return {self.to_full_name(): self}

    def get_env(self):
        return self._env

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


class GroupDeclaration(GroupDeclarationInterface):
    _name: str
    _declarations: Dict[str, TaskDeclaration]

    def __init__(self, name: str, declarations: Dict[str, TaskDeclaration]):
        self._name = name
        self._declarations = declarations

    def get_declarations(self) -> Dict[str, TaskDeclaration]:
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


class TaskAliasDeclaration:
    _name: str
    _arguments: List[str]
    _env: Dict[str, str]

    def __init__(self, name: str, to_execute: List[str], env: Dict[str, str] = []):
        self._name = name
        self._arguments = to_execute
        self._env = env

    def get_name(self):
        return self._name

    def get_arguments(self) -> List[str]:
        return self._arguments

    def get_env(self) -> Dict[str, str]:
        return self._env
