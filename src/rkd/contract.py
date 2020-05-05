
import os
from abc import abstractmethod, ABC as AbstractClass
from typing import Dict, List, Union
from argparse import ArgumentParser
from subprocess import check_call, check_output, Popen, DEVNULL
from .inputoutput import IO
from .exception import UndefinedEnvironmentVariableUsageError


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

    def getenv(self, name: str):
        """ Get environment variable value """
        return self.declaration.get_task_to_execute().internal_getenv(name, self.env)


class TaskInterface(AbstractClass):
    _io: IO
    _ctx: ContextInterface
    _executor: ExecutorInterface

    def internal_inject_dependencies(self, io: IO, ctx: ContextInterface, executor: ExecutorInterface):
        """ Internal method to inject services (do not confuse with current execution context) """

        self._io = io
        self._ctx = ctx
        self._executor = executor

    @abstractmethod
    def get_name(self) -> str:
        """ Task name  eg. ":sh" """
        pass

    @abstractmethod
    def get_group_name(self) -> str:
        """ Group name where the task belongs eg. ":publishing", can be empty. """

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

    def internal_getenv(self, env_name: str, envs: Dict[str, str]) -> str:
        declared_envs = self.get_declared_envs()

        if env_name not in declared_envs:
            raise UndefinedEnvironmentVariableUsageError(
                'Attempt to use not declared environment variable. ' +
                'Please report the problem to the maintainers of this task, not to RKD (unless it is a core task)'
            )

        # return default value
        if env_name not in envs:
            return declared_envs[env_name]

        return envs[env_name]

    def sh(self, cmd: str, capture: bool = False, verbose: bool = False, strict: bool = True) -> Union[str, None]:
        """ Executes a shell script in bash. Throws exception on error.
            To capture output set capture=True
        """

        # set strict mode, it can be disabled manually
        if strict:
            cmd = 'set -euo pipefail; ' + cmd

        if verbose:
            cmd = 'set -x; ' + cmd

        bash_script = "#!/bin/bash -eopipefail \n" + cmd
        read, write = os.pipe()
        os.write(write, bash_script.encode('utf-8'))
        os.close(write)

        if not capture:
            check_call('bash', shell=True, stdin=read)
            return

        return check_output('bash', shell=True, stdin=read).decode('utf-8')

    def exec(self, cmd: str, capture: bool = False, background: bool = False) -> Union[str, None]:
        """ Starts a process in shell. Throws exception on error.
            To capture output set capture=True
        """

        if background:
            if capture:
                raise Exception('Cannot capture output from a background process')

            Popen(cmd, shell=True, stdout=DEVNULL, stderr=DEVNULL)
            return

        if not capture:
            check_call(cmd, shell=True)
            return

        return check_output(cmd, shell=True).decode('utf-8')

    def rkd(self, args: list) -> str:
        """ Spawns an RKD subprocess
        """

        args_str = ' '.join(args)
        return self.exec('rkd --silent %s' % args_str, capture=True, background=False)

    def is_silent_in_observer(self) -> bool:
        """ Internally used property """
        return False
