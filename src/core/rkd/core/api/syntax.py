
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


def parse_path_into_subproject_prefix(path: str) -> str:
    """
    Logic for concatenating of subproject path from filesystem path as input

    :param path:
    :return:
    """

    return ':' + path.strip().strip('/').replace('/', ':').rstrip(': /')


def merge_workdir(task_workdir: Optional[str], subproject_workdir: Optional[str]) -> str:
    """
    Pure domain method that decides how the workdir merge logic should look like
    :param task_workdir:
    :param subproject_workdir:
    :return:
    """

    if not task_workdir:
        task_workdir = ''

    if not subproject_workdir:
        return task_workdir

    if task_workdir.startswith('/'):
        return task_workdir

    return subproject_workdir + '/' + task_workdir


class TaskDeclaration(TaskDeclarationInterface):
    """
    Task Declaration is a DECLARED USAGE of a Task (instance of TaskInterface)
    """

    _task: TaskInterface
    _env: Dict[str, str]       # environment at all
    _user_defined_env: list    # list of env variables overridden by user
    _args: List[str]
    _block: ArgumentBlock = None
    _unique_id: str
    _workdir: Optional[str]        # current working directory (eg. combination of subproject + task)
    _task_workdir: Optional[str]   # original task working directory as defined in task
    _project_name: str
    _is_internal: Optional[bool]             # task is not listed on :tasks

    def __init__(self, task: TaskInterface, env: Dict[str, str] = None, args: List[str] = None,
                 workdir: str = None, internal: Optional[bool] = None):

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
        self._task_workdir = workdir
        self._user_defined_env = list(env.keys())
        self._project_name = ''
        self._is_internal = internal

    def to_full_name(self):
        if self._project_name:
            return self._project_name + self._task.get_full_name()

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

    def as_part_of_subproject(self, workdir: str, subproject_name: str) -> 'TaskDeclaration':
        copy = self._clone()

        copy._workdir = merge_workdir(copy._task_workdir, workdir)
        copy._project_name = subproject_name

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

    @property
    def is_internal(self) -> bool:
        """
        Is task considered internal? Should it be unlisted on a list of tasks for end-user?
        """

        if self._is_internal is not None:
            return self._is_internal

        return self._task.is_internal

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

    @property
    def is_internal(self) -> bool:
        return False


class TaskAliasDeclaration(object):
    """ Allows to define a custom task name that triggers other tasks in proper order """

    _name: str
    _arguments: List[str]
    _env: Dict[str, str]
    _user_defined_env: list  # list of env variables overridden by user
    _description: str
    _workdir: str
    _project_name: str

    def __init__(self, name: str, to_execute: List[str], env: Dict[str, str] = None, description: str = ''):
        if env is None:
            env = {}

        self._name = name
        self._arguments = to_execute
        self._env = merge_env(env)
        self._user_defined_env = list(env.keys())
        self._description = description
        self._workdir = ''
        self._project_name = ''

    def get_name(self):
        if self._project_name:
            return self._project_name + self._name

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

    def _clone(self) -> 'TaskAliasDeclaration':
        """Clone securely the object. There fields shared across objects as references could be kept"""

        return deepcopy(self)

    def as_part_of_subproject(self, workdir: str, subproject_name: str) -> 'TaskAliasDeclaration':
        copy = self._clone()

        copy._workdir = merge_workdir(copy._workdir, workdir)
        copy._project_name = subproject_name

        return copy

    @property
    def workdir(self) -> str:
        return self._workdir

    @property
    def project_name(self) -> str:
        return self._project_name

    def is_part_of_subproject(self) -> bool:
        return isinstance(self._project_name, str) and len(self._project_name) > 1


def merge_env(env: Dict[str, str]):
    """Merge custom environment variables set per-task with system environment
    """

    merged_dict = deepcopy(env)
    merged_dict.update(get_environment_copy())

    return merged_dict
