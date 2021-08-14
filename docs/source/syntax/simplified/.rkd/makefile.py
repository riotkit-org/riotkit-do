from argparse import ArgumentParser
from rkd.core.api.contract import ExecutionContext
from rkd.core.api.decorators import extends
from rkd.core.api.syntax import ExtendedTaskDeclaration
from rkd.core.standardlib.syntax import PythonSyntaxTask


@extends(PythonSyntaxTask)
def hello_task():
    """
    Prints your name
    """

    def configure_argparse(task: PythonSyntaxTask, parser: ArgumentParser):
        parser.add_argument('--name', required=True, help='Allows to specify a name')

    def execute(task: PythonSyntaxTask, ctx: ExecutionContext):
        task.io().info_msg(f'Hello {ctx.get_arg("--name")}, I\'m talking in Python, and you?')
        return True

    return [configure_argparse, execute]


IMPORTS = [
    ExtendedTaskDeclaration(hello_task, name=':hello2')
]
