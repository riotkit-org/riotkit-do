

from abc import abstractmethod, ABC as AbstractClass
from typing import Dict, List, Union, Optional
from argparse import ArgumentParser
from .inputoutput import IO
from .exception import UndefinedEnvironmentVariableUsageError
from .exception import EnvironmentVariableNotUsed
from .exception import MissingInputException
from .taskutil import TaskUtilities


class TaskDeclarationInterface(AbstractClass):
    @abstractmethod
    def to_full_name(self):
        pass

    @abstractmethod
    def get_args(self) -> List[str]:
        pass

    @abstractmethod
    def get_task_to_execute(self):  # -> TaskInterface:
        pass

    @abstractmethod
    def to_list(self) -> list:
        pass

    @abstractmethod
    def get_env(self):
        pass

    @abstractmethod
    def get_group_name(self) -> str:
        pass

    @abstractmethod
    def get_task_name(self) -> str:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass


class GroupDeclarationInterface(AbstractClass):
    @abstractmethod
    def get_declarations(self) -> Dict[str, TaskDeclarationInterface]:
        pass

    @abstractmethod
    def get_group_name(self) -> str:
        pass

    @abstractmethod
    def get_task_name(self) -> str:
        pass

    @abstractmethod
    def to_full_name(self):
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass


class ContextInterface(AbstractClass):
    @abstractmethod
    def merge(cls, first, second):
        pass

    @abstractmethod
    def compile(self) -> None:
        pass

    def find_task_by_name(self, name: str) -> Union[TaskDeclarationInterface, GroupDeclarationInterface]:
        pass

    def find_all_tasks(self) -> Dict[str, Union[TaskDeclarationInterface, GroupDeclarationInterface]]:
        pass


class ExecutorInterface(AbstractClass):
    @abstractmethod
    def execute(self, task: TaskDeclarationInterface, parent: Union[GroupDeclarationInterface, None] = None, args: list = []):
        pass


class ExecutionContext:
    """
    Defines which objects could be accessed by Task. It's a scope of a single task execution.
    """

    declaration: TaskDeclarationInterface
    parent: Union[GroupDeclarationInterface, None]
    args: Dict[str, str]
    env: Dict[str, str]
    ctx: ContextInterface
    executor: ExecutorInterface

    def __init__(self, declaration: TaskDeclarationInterface,
                 parent: Union[GroupDeclarationInterface, None] = None, args: Dict[str, str] = {},
                 env: Dict[str, str] = {}):
        self.declaration = declaration
        self.parent = parent
        self.args = args
        self.env = env

    def get_env(self, name: str, error_on_not_used: bool = False):
        """ Get environment variable value """
        return self.declaration.get_task_to_execute().internal_getenv(name, self.env,
                                                                      error_on_not_used=error_on_not_used)

    # @todo: Coverage + static analysis in validator?
    def get_arg_or_env(self, name: str) -> Union[str, None]:
        """Provides value of user input

        Usage:
            get_arg_or_env('--file-path') resolves into FILE_PATH env variable, and --file-path switch (file_path in argparse)

        Behavior:
            When user provided explicitly switch eg. --history-id, then it's value will be taken in priority.
            If switch --history-id was not used, but user provided HISTORY_ID environment variable,
            then it will be considered.

            If no switch provided and no environment variable provided, but a switch has default value - it would be returned.
            If no switch provided and no environment variable provided, the switch does not have default, but environment variable has a default value defined, it would be returned.

        Raises:
            MissingInputException: When no switch and no environment variable was provided, then an exception is thrown.
        """
        env_name = name[2:].replace('-', '_').upper()

        # --some-switch was used
        try:
            value = self.get_arg(name)

            if value is not None:
                return value

        except KeyError:
            pass

        try:
            return self.get_env(env_name, error_on_not_used=True)
        except EnvironmentVariableNotUsed:
            raise MissingInputException(name, env_name)

    def get_arg(self, name: str) -> Optional[str]:
        arg_name = name[2:].replace('-', '_')

        return self.args[arg_name]


class TaskInterface(TaskUtilities):
    _io: IO
    _ctx: ContextInterface
    _executor: ExecutorInterface

    def internal_inject_dependencies(self, io: IO, ctx: ContextInterface, executor: ExecutorInterface):
        """"""  # sphinx: skip

        self._io = io
        self._ctx = ctx
        self._executor = executor

    def copy_internal_dependencies(self, task):
        """Allows to execute a task-in-task, by copying dependent services from one task to other task
        :api 0.2
        """

        task.internal_inject_dependencies(self._io, self._ctx, self._executor)

    @abstractmethod
    def get_name(self) -> str:
        """Task name  eg. ":sh"
        :api 0.2
        """
        pass

    @abstractmethod
    def get_group_name(self) -> str:
        """
        Group name where the task belongs eg. ":publishing", can be empty.
        :api 0.2
        """

        pass

    def get_description(self) -> str:
        return ''

    @abstractmethod
    def execute(self, context: ExecutionContext) -> bool:
        """ Executes a task. True/False should be returned as return """
        pass

    @abstractmethod
    def configure_argparse(self, parser: ArgumentParser):
        """ Allows a task to configure ArgumentParser (argparse) """

        pass

    def get_full_name(self):
        """ Returns task full name, including group name """

        return self.get_group_name() + self.get_name()

    def get_declared_envs(self) -> Dict[str, str]:
        """ Dictionary of allowed envs to override: KEY -> DEFAULT VALUE """
        return {}

    def internal_getenv(self, env_name: str, envs: Dict[str, str], error_on_not_used: bool = False) -> str:
        """"""
        declared_envs = self.get_declared_envs()

        if env_name not in declared_envs:
            raise UndefinedEnvironmentVariableUsageError(
                'Attempt to use not declared environment variable. ' +
                'Please report the problem to the maintainers of this task, not to RKD (unless it is a core task)'
            )

        # return default value
        if env_name not in envs:
            if error_on_not_used:
                raise EnvironmentVariableNotUsed(env_name)

            return declared_envs[env_name]

        return envs[env_name]

    def is_silent_in_observer(self) -> bool:
        """ Internally used property """
        return False

    def io(self):
        return self._io

    def __str__(self):
        return 'Task<' + self.get_full_name() + '>'


