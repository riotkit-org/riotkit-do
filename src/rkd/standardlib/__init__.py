
from argparse import ArgumentParser
from typing import Callable
from ..contract import TaskInterface, ExecutionContext, TaskDeclarationInterface
from ..inputoutput import SystemIO


class InitTask(TaskInterface):
    """
    :init task is executing ALWAYS. That's a technical, core task.

    The purpose of this task is to handle global settings
    """

    def get_name(self) -> str:
        return ':init'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def execute(self, context: ExecutionContext) -> bool:
        """
        :init task is setting user-defined global defaults on runtime
        It allows user to call eg. rkd --log-level debug :task1 :task2
        to set global settings such as log level

        :param context:
        :return:
        """

        context.ctx.io  # type: SystemIO
        context.ctx.io.silent = context.args['silent']

        # log level is optional to be set
        if context.args['log_level']:
            context.ctx.io.set_log_level(context.args['log_level'])

        return True

    def is_silent_in_observer(self) -> bool:
        return True


class TasksListingTask(TaskInterface):
    """ Lists all enabled tasks """

    def get_name(self) -> str:
        return ':tasks'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def execute(self, context: ExecutionContext) -> bool:
        io = context.io
        groups = {}

        # collect into groups
        for name, declaration in context.ctx.find_all_tasks().items():
            group_name = declaration.get_group_name()

            if group_name not in groups:
                groups[group_name] = {}

            groups[group_name][declaration.to_full_name()] = declaration

        # iterate over groups and list tasks under groups
        for group_name, tasks in groups.items():
            if not group_name:
                group_name = 'global'

            io.print_group(group_name)

            for task_name, declaration in tasks.items():
                declaration: TaskDeclarationInterface

                try:
                    description = declaration.get_description()
                    text_description = "\t\t\t# " + description if description else ""
                except AttributeError:
                    text_description = ""

                io.outln(task_name + text_description)

            io.print_opt_line()

        return True


class CallableTask(TaskInterface):
    """ Executes a custom callback - allows to quickly define a short task """

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
