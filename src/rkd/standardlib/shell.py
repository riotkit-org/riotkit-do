
from argparse import ArgumentParser
from ..contract import TaskInterface, ExecutionContext


class ShellCommand(TaskInterface):
    def get_name(self) -> str:
        return ':sh'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def execute(self, context: ExecutionContext) -> bool:
        pass
