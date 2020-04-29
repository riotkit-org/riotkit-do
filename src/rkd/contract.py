
from abc import abstractmethod, ABC as AbstractClass
from typing import Dict, List, Union
from argparse import ArgumentParser


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
    def to_dict(self) -> dict:
        pass

    @abstractmethod
    def get_env(self):
        pass


class GroupDeclarationInterface(AbstractClass):
    @abstractmethod
    def get_declarations(self) -> Dict[str, TaskDeclarationInterface]:
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

    def __init__(self, ctx: ContextInterface, executor: ExecutorInterface, declaration: TaskDeclarationInterface,
                 parent: Union[GroupDeclarationInterface, None] = None, args: Dict[str, str] = {},
                 env: Dict[str, str] = {}):
        self.ctx = ctx
        self.executor = executor
        self.declaration = declaration
        self.parent = parent
        self.args = args
        self.env = env


class TaskInterface(AbstractClass):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_group_name(self) -> str:
        pass

    @abstractmethod
    def execute(self, context: ExecutionContext):
        pass

    @abstractmethod
    def configure_argparse(self, parser: ArgumentParser):
        pass

    def get_full_name(self):
        return self.get_group_name() + self.get_name()
