
from argparse import ArgumentParser
from subprocess import CalledProcessError
from typing import Callable
from ..api.syntax import TaskDeclaration
from ..api.contract import TaskInterface
from ..api.contract import ExecutionContext


# <sphinx=shell-command>
class ShellCommandTask(TaskInterface):
    """Executes shell scripts"""

    def get_name(self) -> str:
        return ':sh'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--cmd', '-c', help='Shell command', required=True)

    def execute(self, context: ExecutionContext) -> bool:
        # self.sh() and self.io() are part of TaskUtilities via TaskInterface

        try:
            self.sh(context.get_arg('cmd'), capture=False)
        except CalledProcessError as e:
            self.io().error_msg(str(e))
            return False

        return True
# </sphinx=shell-command>


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


class BaseShellCommandWithArgumentParsingTask(TaskInterface):
    """ Shell command with argument parsing. Set "description" parameter to change this description. """

    _name: str
    _command: str
    _group: str
    _arguments_definition: Callable
    _description = ''

    def __init__(self, name: str, command: str, group: str = '', description: str = '',
                 arguments_definition: Callable[[ArgumentParser], None] = None):

        if not name:
            raise Exception('Name cannot be empty')

        if not command:
            raise Exception('Command must be specified')

        self._name = name
        self._command = command
        self._group = group
        self._arguments_definition = arguments_definition
        self._description = description

    def get_name(self) -> str:
        return self._name

    def get_description(self) -> str:
        return self._description

    def get_group_name(self) -> str:
        return self._group

    def configure_argparse(self, parser: ArgumentParser):
        if self._arguments_definition:
            self._arguments_definition(parser)

    def execute(self, context: ExecutionContext) -> bool:
        arguments_exported = ''

        for arg, arg_value in context.args.items():
            arguments_exported += "export ARG_%s='%s';\n" % (
                arg.upper(),
                arg_value.replace("'", "\'") if arg_value else ''
            )

        # would raise an exception on failure
        try:
            self.sh(arguments_exported + "\n" + self._command)
        except CalledProcessError:
            return False

        return True


def imports() -> list:
    return [
        TaskDeclaration(ShellCommandTask()),
        TaskDeclaration(ExecProcessCommand())
    ]
