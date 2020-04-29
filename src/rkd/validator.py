
from typing import Union
from .syntax import TaskDeclaration, GroupDeclaration
from .argparsing import CommandlineParsingHelper


class TaskDeclarationValidator:

    @staticmethod
    def assert_declaration_is_valid(task: TaskDeclaration, parent: Union[GroupDeclaration, None] = None, args: list = []):
        # check if arguments are satisfied
        CommandlineParsingHelper.get_parsed_vars_for_task(task, args)
