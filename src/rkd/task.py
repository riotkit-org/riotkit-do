
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

