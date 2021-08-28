
from argparse import ArgumentParser
from copy import copy
from subprocess import CalledProcessError
from typing import Callable, List, Optional

from ..api.syntax import TaskDeclaration
from ..api.contract import TaskInterface, ExtendableTaskInterface, MultiStepLanguageExtensionInterface
from ..api.contract import ExecutionContext


# <sphinx=shell-command>
class ShellCommandTask(ExtendableTaskInterface, MultiStepLanguageExtensionInterface):
    """
    Executes shell commands and scripts

    Extendable in two ways:
      - overwrite stdin()/input to execute a script
      - overwrite execute() to execute a Python code that could contain calls to self.sh()
    """

    # to be overridden in compile()
    is_cmd_required: bool  # Is --cmd switch required to be set?
    code: Optional[str]    # (Optional) Execute script from a variable value
    name: Optional[str]    # (Optional) Task name
    step_num: int

    def __init__(self):
        self.is_cmd_required = True
        self.code = None
        self.name = None
        self.step_num = 0

    def get_name(self) -> str:
        return ':sh' if not self.name else self.name

    def get_group_name(self) -> str:
        return ''

    def get_configuration_attributes(self) -> List[str]:
        return ['is_cmd_required']

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--cmd', '-c', help='Shell command', required=self.is_cmd_required)

    def with_predefined_details(self, code: str, name: str, step_num: int) -> 'ShellCommandTask':
        clone = copy(self)
        clone.code = code
        clone.name = name
        clone.step_num = step_num
        clone.is_cmd_required = False

        return clone

    def execute(self, context: ExecutionContext) -> bool:
        cmd = ''

        if context.get_input():
            cmd = context.get_input().read()

        if context.get_arg('cmd'):
            cmd = context.get_arg('cmd')

        if self.code:
            cmd = self.code

        try:
            # self.sh() and self.io() are part of the base class
            if cmd:
                self.sh(cmd, capture=False)
            self.inner_execute(context)

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
