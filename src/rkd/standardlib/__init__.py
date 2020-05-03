
import pkg_resources
import os
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

        self._ctx.io  # type: SystemIO
        self._ctx.io.silent = context.args['silent']

        # log level is optional to be set
        if context.args['log_level']:
            self._ctx.io.set_log_level(context.args['log_level'])

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
        io = self._io
        groups = {}

        # collect into groups
        for name, declaration in self._ctx.find_all_tasks().items():
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


class VersionTask(TaskInterface):
    """ Shows version of RKD and of all loaded tasks """

    def get_name(self) -> str:
        return ':version'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def execute(self, context: ExecutionContext) -> bool:
        self._io.outln('RKD version %s' % pkg_resources.get_distribution("rkd").version)
        self._io.print_opt_line()
        self._io.print_separator()

        for name, declaration in self._ctx.find_all_tasks().items():
            if not isinstance(declaration, TaskDeclarationInterface):
                continue

            task = declaration.get_task_to_execute()
            module = task.__class__.__module__
            parts = module.split('.')

            for num in range(0, len(parts) + 1):
                try_module_name = ".".join(parts)

                try:
                    version = pkg_resources.get_distribution(try_module_name).version
                    self._io.outln('- %s version %s' % (name, version))

                    break
                except pkg_resources.DistributionNotFound:
                    parts = parts[:-1]

        return True


class CreateStructureTask(TaskInterface):
    """ Creates a file structure in current directory """

    def get_name(self) -> str:
        return ':create-structure'

    def get_group_name(self) -> str:
        return ':rkd'

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def execute(self, context: ExecutionContext) -> bool:
        if os.path.isdir('.rkd'):
            self._io.error_msg('Structure already created - ".rkd" directory is present')
            return False

        self._io.info_msg('Creating a folder structure at %s' % os.getcwd())
        template_structure_path = os.path.dirname(os.path.realpath(__file__)) + '/../misc/initial-structure'
        self.sh('cp -pr %s/.rkd ./' % template_structure_path, verbose=True)

        return True
