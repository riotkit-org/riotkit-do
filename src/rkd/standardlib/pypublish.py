
from argparse import ArgumentParser
from ..contract import TaskInterface, ExecutionContext


class PyPublishTask(TaskInterface):
    def get_name(self) -> str:
        return ':publish'

    def get_group_name(self) -> str:
        return ':py'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--username', help='Username')
        parser.add_argument('--password', help='Password')

    def execute(self, context: ExecutionContext) -> bool:
        context.io.info('LOG test')
        context.io.outln('STDOUT test')

        return True
