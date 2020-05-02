
from argparse import ArgumentParser
from subprocess import CalledProcessError
from ..contract import TaskInterface, ExecutionContext


class ShellCommand(TaskInterface):
    """
    Executes shell scripts
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
            self._io.error_msg(str(e))
            return False

        return True


class ExecProcessCommand(TaskInterface):
    """
    Spawns a shell process
    """

    def get_name(self) -> str:
        return ':exec'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--cmd', '-c', help='Shell command', required=True)
        parser.add_argument('--background', '-b', help='Fork to background', action='store_true')

    def execute(self, context: ExecutionContext) -> bool:
        try:
            self.exec(context.args['cmd'], capture=False, background=bool(context.args['background']))
        except CalledProcessError as e:
            self._io.error_msg(str(e))
            return False

        return True
