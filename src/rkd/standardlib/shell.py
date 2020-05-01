
from argparse import ArgumentParser
from subprocess import CalledProcessError
from ..contract import TaskInterface, ExecutionContext


class ShellCommand(TaskInterface):
    """
    Executes shell commands
    """

    def get_name(self) -> str:
        return ':sh'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--cmd', '-c', help='Shell command', required=True)

    def execute(self, context: ExecutionContext) -> bool:
        try:
            self.sh(context.args['cmd'], capture=False)
        except CalledProcessError as e:
            context.io.error_msg(str(e))
            return False

        return True
