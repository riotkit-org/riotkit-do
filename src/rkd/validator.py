
from typing import Union
from .syntax import TaskDeclaration, GroupDeclaration
from argparse import ArgumentParser


class TaskDeclarationValidator:

    @staticmethod
    def assert_declaration_is_valid(task: TaskDeclaration, parent: Union[GroupDeclaration, None] = None, args: list = []):
        # check if arguments are satisfied
        argparse = ArgumentParser(task.to_full_name())
        task.get_task_to_execute().configure_argparse(argparse)
        argparse.parse_args(args)
