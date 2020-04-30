
from argparse import ArgumentParser
from ..contract import TaskInterface, ExecutionContext
from typing import Callable


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

    def execute(self, context: ExecutionContext) -> bool:
        context.ctx.io.silent = context.args['silent']

        return True


class TasksListingTask(TaskInterface):
    def get_name(self) -> str:
        return ':tasks'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def execute(self, context: ExecutionContext) -> bool:
        io = context.io
        groups = {}

        for name, declaration in context.ctx.find_all_tasks().items():
            group_name = declaration.get_group_name()

            if group_name not in groups:
                groups[group_name] = {}

            groups[group_name][declaration.to_full_name()] = declaration

        for group_name, tasks in groups.items():
            if not group_name:
                group_name = 'global'

            io.print_group(group_name)

            for task_name, declaration in tasks.items():
                io.outln(task_name)

            io.print_opt_line()

        return True


class CallableTask(TaskInterface):
    _callable: Callable[[ExecutionContext], any]
    _name: str

    def __init__(self, name: str, callback: Callable[[ExecutionContext], any]):
        self._name = name
        self._callable = callback

    def get_name(self) -> str:
        return self._name

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def execute(self, context: ExecutionContext) -> bool:
        return self._callable(context)
