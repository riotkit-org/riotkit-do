
"""
CONTRACT (part of API)
======================

Core interfaces that should be changed WITH CAREFUL as those are parts of API.
Any breaking change there requires to bump RKD major version (see: Semantic Versioning)
"""
from tabulate import tabulate
from abc import abstractmethod, ABC as AbstractClass, ABC
from typing import Dict, List, Union, Optional, Type
from argparse import ArgumentParser

from ..inputoutput import IO
from ..exception import UndefinedEnvironmentVariableUsageError
from ..exception import EnvironmentVariableNotUsed
from ..exception import MissingInputException
from ..exception import EnvironmentVariableNameNotAllowed
from ..taskutil import TaskUtilities
from .temp import TempManager
from .inputoutput import SystemIO, ReadableStreamType


def env_to_switch(env_name: str) -> str:
    return '--' + env_name.replace('_', '-').lower()


class ArgumentEnv(object):
    """Represents an environment variable that should provide a value to an argparse switch

    Note: There is a list of reserved environment variables, that cannot be used. See ArgumentEnv.RESERVED_VARS
    """

    RESERVED_VARS = ['PATH', 'PWD', 'LANG', 'DISPLAY', 'SHELL', 'SHLVL', 'HOME', 'EDITOR']
    name: str
    default: str
    switch: str

    def __init__(self, name: str, switch: str = '', default: str = ''):
        self.name = name
        self.default = default
        self.switch = switch if switch else env_to_switch(name)

        self._validate()

    def _validate(self):
        if self.name in self.RESERVED_VARS:
            raise EnvironmentVariableNameNotAllowed(self.name)


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

    @abstractmethod
    def get_full_description(self) -> str:
        pass

    @abstractmethod
    def format_task_name(self, name: str) -> str:
        pass

    @property
    def is_internal(self) -> bool:
        return False

    @abstractmethod
    def get_input(self) -> ReadableStreamType:
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

    @abstractmethod
    def format_task_name(self, name: str) -> str:
        pass


class ContextInterface(AbstractClass):
    directories: []
    io: SystemIO

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
    def execute(self, scheduled_declaration, task_num: int):
        pass


class ExecutionContext(object):
    """
    Defines which objects could be accessed by Task. It's a scope of a single task execution.
    """

    __declaration: TaskDeclarationInterface
    parent: Union[GroupDeclarationInterface, None]
    args: Dict[str, str]
    env: Dict[str, str]
    __ctx: ContextInterface
    executor: ExecutorInterface
    _allow_mutating_globals: bool

    # List of arguments definitions populated by Argparse (with limited parameters supported)
    # Read about "traced arguments"
    defined_args: Dict[str, dict]

    def __init__(self, declaration: TaskDeclarationInterface,
                 parent: Union[GroupDeclarationInterface, None] = None, args: Dict[str, str] = {},
                 env: Dict[str, str] = {},
                 defined_args: Dict[str, dict] = {}):

        self.__declaration = declaration
        self.parent = parent
        self.args = args
        self.env = env
        self.defined_args = defined_args
        self._allow_mutating_globals = declaration.to_full_name() == ':init'

    def get_env(self, name: str, switch: str = '', error_on_not_used: bool = False):
        """Get environment variable value"""
        return self.__declaration.get_task_to_execute().internal_getenv(name, self.env, switch=switch,
                                                                        error_on_not_used=error_on_not_used)

    def get_arg_or_env(self, name: str) -> Union[str, None]:
        """Provides value of user input

        Usage:
            get_arg_or_env('--file-path') resolves into FILE_PATH env variable, and --file-path switch
            (file_path in argparse)

        Behavior:
            When user provided explicitly switch eg. --history-id, then it's value will be taken in priority.
            If switch --history-id was not used, but user provided HISTORY_ID environment variable,
            then it will be considered.

            If no switch provided and no environment variable provided, but a switch has
            default value - it would be returned.

            If no switch provided and no environment variable provided, the switch does not have default,
            but environment variable has a default value defined, it would be returned.

            When the --switch has default value (user does not use it, or user sets it explicitly to default value),
            and environment variable SWITCH is defined, then environment variable would be taken.

            Explicit environment variables definitions
            ------------------------------------------

            From RKD 2.1 the environment variable names can be mapped to any ArgParse switch.

            Below example maps "COMMAND" environment variable to "--cmd" switch.

            .. code:: python

                def get_declared_envs(self) -> Dict[str, Union[str, ArgumentEnv]]:
                    return {
                        'COMMAND': ArgumentEnv(name='COMMAND', switch='--cmd', default='')
                    }

        Raises:
            MissingInputException: When no switch and no environment variable was provided, then an exception is thrown.
        """
        env_name = name[2:].replace('-', '_').upper()
        env_value = None

        try:
            env_value = self.get_env(env_name, switch=name, error_on_not_used=True)
            is_env_variable_defined = True

        except EnvironmentVariableNotUsed:
            is_env_variable_defined = False

        # case 1: a --switch was used
        # case 2: --switch as default value set, environment variable is set, then pick env
        try:
            value = self.get_arg(name)

            # https://github.com/riotkit-org/riotkit-do/issues/23
            # When --switch has same value as default, and environment variable is not empty, then env has priority
            if self.defined_args[name]['default'] == value and is_env_variable_defined:
                return env_value

            if value is not None:
                return value

        except KeyError:
            pass

        # case: No --switch defined, no ENV defined
        if not is_env_variable_defined:
            raise MissingInputException(name, env_name)

        # case: No --switch defined, ENV defined
        return env_value

    def get_arg(self, name: str) -> Optional[str]:
        """Get argument or option

        Usage:
            ctx.get_arg('--name')  # for options
            ctx.get_arg('name')    # for arguments

        Raises:
            KeyError when argument/option was not defined

        Returns:
            Actual value or default value
        """

        try:
            arg_name = name[2:].replace('-', '_')

            return self.args[arg_name]
        except KeyError:
            try:
                return self.args[name]
            except KeyError:
                raise MissingInputException(name, '')

    def get_input(self) -> Optional[ReadableStreamType]:
        return self.__declaration.get_input()

    def can_mutate_globals(self) -> bool:
        """
        Is task having a special permissions to mutate globals such as OS environment
        :return:
        """

        return self._allow_mutating_globals

    def get_args(self) -> Dict[str, str]:
        return self.args


class TaskInterface(TaskUtilities):
    _io: IO
    _ctx: ContextInterface
    _executor: ExecutorInterface
    temp: TempManager
    _internal: bool
    _extended_from: Type['TaskInterface']

    def internal_inject_dependencies(self, io: IO, ctx: ContextInterface = None,
                                     executor: ExecutorInterface = None, temp_manager: TempManager = None):
        """"""  # sphinx: skip

        self._io = io
        self._ctx = ctx
        self._executor = executor
        self.temp = temp_manager

    def copy_internal_dependencies(self, task):
        """
        Allows to execute a task-in-task, by copying dependent services from one task to other task
        """

        task.internal_inject_dependencies(self._io, self._ctx, self._executor, self.temp)

    @abstractmethod
    def get_name(self) -> str:
        """
        Task name  eg. ":sh"
        """
        pass

    @abstractmethod
    def get_group_name(self) -> str:
        """
        Group name where the task belongs eg. ":publishing", can be empty.
        """

        pass

    def get_become_as(self) -> str:
        """
        User name in UNIX/Linux system, optional.
        When defined, then current task will be executed as this user (WARNING: a forked process would be started)
        """

        return ''

    def should_fork(self) -> bool:
        """
        Decides if task should be ran in a separate Python process (be careful with it)
        """

        return self.get_become_as() != ''

    def get_description(self) -> str:
        return ''

    # ====== LIFECYCLE METHODS

    @abstractmethod
    def execute(self, context: ExecutionContext) -> bool:
        """
        Executes a task. True/False should be returned as return
        """
        pass

    @abstractmethod
    def configure_argparse(self, parser: ArgumentParser):
        """
        Allows a task to configure ArgumentParser (argparse)

        .. code:: python

            def configure_argparse(self, parser: ArgumentParser):
                parser.add_argument('--php', help='PHP version ("php" docker image tag)', default='8.0-alpine')
                parser.add_argument('--image', help='Docker image name', default='php')
        """

        pass

    # ====== LIFECYCLE METHODS ENDS

    def get_full_name(self):
        """
        Returns task full name, including group name
        """

        return self.get_group_name() + self.get_name()

    @classmethod
    def get_declared_envs(cls) -> Dict[str, Union[str, ArgumentEnv]]:
        """
        Dictionary of allowed envs to override: KEY -> DEFAULT VALUE

        All environment variables fetched from the ExecutionContext needs to be defined there.
        Declared values there are automatically documented in --help

        .. code:: python

            @classmethod
            def get_declared_envs(cls) -> Dict[str, Union[str, ArgumentEnv]]:
                return {
                    'PHP': ArgumentEnv('PHP', '--php', '8.0-alpine'),
                    'IMAGE': ArgumentEnv('IMAGE', '--image', 'php')
                }
        """
        return {}

    def internal_normalized_get_declared_envs(self) -> Dict[str, ArgumentEnv]:
        """"""  # sphinx: ignore

        # Method used internally, supports conversion of values from primitives to ArgumentEnv
        # as developers can specify env variables in get_declared_envs() as primitives or as ArgumentEnv
        # so, there we normalize everything
        #
        # WRAPPER OVER INTERFACE METHOD: get_declared_envs() should be defined by developer

        envs = {}

        for name, value in self.get_declared_envs().items():
            if not isinstance(value, ArgumentEnv):
                value = ArgumentEnv(name=name, default=value)

            envs[name] = value

        return envs

    def internal_getenv(self, env_name: str, envs: Dict[str, str], switch: str = '',
                        error_on_not_used: bool = False) -> str:
        """"""  # sphinx: ignore

        declared_envs = self.internal_normalized_get_declared_envs()

        # find env by switch, when env was defined to be non-standard name
        if switch:
            for env in declared_envs.values():
                if env.switch == switch:
                    self.io().debug('Resolved environment "%s" from switch "%s"' % (env_name, env.switch))
                    env_name = env.name

        if env_name not in declared_envs:
            raise UndefinedEnvironmentVariableUsageError(
                (
                    'Attempt to use not declared environment variable "%s". ' +
                    'Please report the problem to the maintainers of this task, not to RKD (unless it is a core task)'
                )
                % env_name
            )

        # return default value
        if env_name not in envs:
            if error_on_not_used:
                raise EnvironmentVariableNotUsed(env_name)

            return declared_envs[env_name].default

        return envs[env_name]

    def is_silent_in_observer(self) -> bool:
        """"""  # sphinx: skip
        return False

    def io(self) -> IO:
        """Gives access to Input/Output object"""

        return self._io

    def format_task_name(self, name: str) -> str:
        """Allows to add a fancy formatting to the task name, when the task is displayed eg. on the :tasks list"""

        return name

    def py(self, code: str = '', become: str = None, capture: bool = False,
           script_path: str = None, arguments: str = '') -> Union[str, None]:

        """Executes a Python code in a separate process

        NOTICE: Use instead of subprocess. Raw subprocess is less supported and output from raw subprocess
                may be not catch properly into the logs
        """

        return super().py(
            code=code, become=become, capture=capture, script_path=script_path, arguments=arguments
        )

    def sh(self, cmd: str, capture: bool = False, verbose: bool = False, strict: bool = True,
           env: dict = None, use_subprocess: bool = False) -> Union[str, None]:
        """Executes a shell script in bash. Throws exception on error.
        To capture output set capture=True

        NOTICE: Use instead of subprocess. Raw subprocess is less supported and output from raw subprocess
                may be not catch properly into the logs
        """
        return super().sh(
            cmd=cmd, capture=capture, verbose=verbose, strict=strict, env=env
        )

    def exec(self, cmd: str, capture: bool = False, background: bool = False) -> Union[str, None]:
        """Starts a process in shell. Throws exception on error.
        To capture output set capture=True

        NOTICE: Use instead of subprocess. Raw subprocess is less supported and output from raw subprocess
                may be not catch properly into the logs
        """
        return super().exec(cmd=cmd, capture=capture, background=background)

    def rkd(self, args: list, verbose: bool = False, capture: bool = False) -> str:
        """Spawns an RKD subprocess

        NOTICE: Use instead of subprocess. Raw subprocess is less supported and output from raw subprocess
                may be not catch properly into the logs
        """
        return super().rkd(args=args, verbose=verbose, capture=capture)

    def silent_sh(self, cmd: str, verbose: bool = False, strict: bool = True,
                  env: dict = None) -> bool:
        """sh() shortcut that catches errors and displays using IO().error_msg()

        NOTICE: Use instead of subprocess. Raw subprocess is less supported and output from raw subprocess
                may be not catch properly into the logs
        """
        return super().silent_sh(cmd=cmd, verbose=verbose, strict=strict, env=env)

    def __str__(self):
        return 'Task<{name}, object_id={id}, extended_from={extends}>'.format(
            name=self.get_full_name(),
            id=id(self),
            extends=self.extends_task()
        )

    @property
    def is_internal(self) -> bool:
        return False

    def extends_task(self):
        """
        Provides information if this Task has a Parent Task

        :return:
        """

        try:
            extends_from = self._extended_from.__module__ + '.' + self._extended_from.__name__
        except AttributeError:
            extends_from = 'TaskInterface'

        return extends_from

    def __deepcopy__(self, memodict={}):
        """
        Do not allow copy.deepcopy() to copy this object. Declaration can be doubled, TaskInterface implementation not.

        :param memodict:
        :return:
        """

        return self


class ExtendableTaskInterface(TaskInterface, ABC):
    def inner_execute(self, ctx: ExecutionContext) -> bool:
        """
        Method that can be executed inside execute() - if implemented.

        Use cases:
           - Allow child Task to inject code between e.g. database startup and database shutdown to execute some
             operations on the database

        :param ctx:
        :return:
        """

        pass

    def get_configuration_attributes(self) -> List[str]:
        return []

    def configure(self, event: 'ConfigurationLifecycleEvent') -> None:
        """
        Executes before all tasks are executed. ORDER DOES NOT MATTER, can be executed in parallel.
        """
        pass

    def compile(self, event: 'CompilationLifecycleEvent') -> None:
        """
        Execute code after all tasks were collected into a single context
        """
        pass


class ArgparseArgument(object):
    """Represents a add_argument(*args, **kwargs)"""

    args: list
    kwargs: dict

    def __init__(self, args: list = None, kwargs: dict = None):
        if args is None:
            args = []

        if kwargs is None:
            kwargs = {}

        self.args = args
        self.kwargs = kwargs


class PipelinePartInterface(object):
    """
    Partial element of a Pipeline - string that is being converted to GroupDeclaration
    """

    @abstractmethod
    def to_pipeline_part(self) -> List[str]:
        pass


class MultiStepLanguageExtensionInterface(ABC):
    @abstractmethod
    def with_predefined_details(self, code: str, name: str, step_num: int):
        pass
