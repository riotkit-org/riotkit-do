
from argparse import ArgumentParser
from ..contract import TaskInterface, ExecutionContext


class InitTask(TaskInterface):
    """
    :init task is executing ALWAYS.

    The purpose of this task is to handle global settings
    """

    def get_name(self) -> str:
        return ':init'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def execute(self, context: ExecutionContext):
        context.ctx.io.silent = context.args['silent']
