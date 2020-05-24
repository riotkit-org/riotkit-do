
import os
from typing import List, Dict
from copy import deepcopy
from .contract import TaskDeclarationInterface, GroupDeclarationInterface, TaskInterface
from .exception import DeclarationException


class TaskDeclaration(TaskDeclarationInterface):
    _task: TaskInterface
    _env: Dict[str, str]       # environment at all
    _user_defined_env: list    # list of env variables overridden by user
    _args: List[str]

    def __init__(self, task: TaskInterface, env: Dict[str, str] = {}, args: List[str] = []):
        if not isinstance(task, TaskInterface):
            raise DeclarationException('Invalid class: TaskDeclaration needs to take TaskInterface as task argument')

        merged_env = dict(os.environ)
        merged_env.update(env)

        self._task = task
        self._env = merged_env
        self._args = args
        self._user_defined_env = list(env.keys())

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

    def with_user_overridden_env(self, env_list: list):
        """ Immutable arguments setter. Produces new object each time """

        copy = deepcopy(self)
        copy._user_defined_env = env_list

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

        return task.__doc__.strip().split("\n")[0]

    @staticmethod
    def parse_name(name: str) -> tuple:
        split = name.split(':')
        task_name = ":" + split[-1]
        group = ":".join(split[:-1])

        return task_name, group

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


class TaskAliasDeclaration:
    """ Allows to define a custom task name that triggers other tasks in proper order """

    _name: str
    _arguments: List[str]
    _env: Dict[str, str]
    _user_defined_env: list  # list of env variables overridden by user
    _description: str

    def __init__(self, name: str, to_execute: List[str], env: Dict[str, str] = {}, description: str = ''):
        merged_env = dict(os.environ)
        merged_env.update(env)

        self._name = name
        self._arguments = to_execute
        self._env = merged_env
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
