
from argparse import ArgumentParser
from ..task import TaskInterface


class PyPublishTask(TaskInterface):
    def get_name(self) -> str:
        return ':publish'

    def get_group_name(self) -> str:
        return ':py'

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def execute(self, task_name: str, options: dict, env: dict):
        pass
