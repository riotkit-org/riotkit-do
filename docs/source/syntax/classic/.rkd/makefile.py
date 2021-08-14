from argparse import ArgumentParser
from rkd.core.api.contract import TaskInterface, ExecutionContext
from rkd.core.api.syntax import TaskDeclaration


class HelloFromPythonTask(TaskInterface):
    """
    Prints your name
    """

    def get_name(self) -> str:
        return ':hello3'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--name', required=True, help='Allows to specify a name')

    def execute(self, ctx: ExecutionContext) -> bool:
        self.io().info_msg(f'Hello {ctx.get_arg("--name")}, I\'m talking classic Python syntax, and you?')
        return True


IMPORTS = [
    TaskDeclaration(HelloFromPythonTask()),
]
