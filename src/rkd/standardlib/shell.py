
from argparse import ArgumentParser
from ..task import TaskInterface


class ShellCommand(TaskInterface):
    def get_name(self) -> str:
        return ':sh'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def execute(self, task_name: str, options: dict, env: dict):
        pass
