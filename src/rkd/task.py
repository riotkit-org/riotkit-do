
from argparse import ArgumentParser
from abc import ABC as AbstractClass, abstractmethod
from typing import Dict


class TaskInterface(AbstractClass):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_group_name(self) -> str:
        pass

    @abstractmethod
    def execute(self, task_name: str, options: dict, env: dict):
        pass

    @abstractmethod
    def configure_argparse(self, parser: ArgumentParser):
        pass

    def get_full_name(self):
        return self.get_group_name() + self.get_name()


class TaskGroup(TaskInterface):
    _tasks: Dict[str, TaskInterface]

    def __init__(self, tasks: Dict[str, TaskInterface]):
        self._tasks = tasks

    def get_group_name(self) -> str:
        pass

    def execute(self, task_name: str, options: dict, env: dict):
        raise Exception('Incorrect implementation of TaskGroup. TaskGroup is not callable, but expandable')

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def get_name(self) -> str:
        return 'task_group'

    def get_tasks(self) -> Dict[str, TaskInterface]:
        return self._tasks
