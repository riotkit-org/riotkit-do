
import pkg_resources
import os
from typing import Dict
from typing import List
from argparse import ArgumentParser
from typing import Callable
from copy import deepcopy
from ..contract import TaskInterface, ExecutionContext, TaskDeclarationInterface
from ..inputoutput import SystemIO
from ..aliasgroups import parse_alias_groups_from_env, AliasGroup


class InitTask(TaskInterface):
    """
    :init task is executing ALWAYS. That's a technical, core task.

    The purpose of this task is to handle global settings
    """

    def get_name(self) -> str:
        return ':init'

    def get_group_name(self) -> str:
        return ''

    def get_declared_envs(self) -> Dict[str, str]:
        return {
            'RKD_DEPTH': '0',
            'RKD_PATH': '',
            'RKD_ALIAS_GROUPS': ''
        }

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--no-ui', '-n', action='store_true',
                            help='Do not display RKD interface (similar to --silent, ' +
                                 'but does not inherit --silent into next tasks)')

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

        if int(context.get_env('RKD_DEPTH')) >= 1 or context.args['no_ui']:
            self._ctx.io.set_display_ui(False)

        return True

    def is_silent_in_observer(self) -> bool:
        return True


class TasksListingTask(TaskInterface):
    """Lists all enabled tasks

    Environment:
        - RKD_WHITELIST_GROUPS: Comma separated list of groups that should be only visible, others would be hidden
    """

    def get_name(self) -> str:
        return ':tasks'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def get_declared_envs(self) -> Dict[str, str]:
        return {
            'RKD_WHITELIST_GROUPS': '',
            'RKD_ALIAS_GROUPS': ''
        }

    def execute(self, context: ExecutionContext) -> bool:
        io = self._io
        groups = {}
        aliases = parse_alias_groups_from_env(context.get_env('RKD_ALIAS_GROUPS'))

        # fancy stuff
        whitelisted_groups = context.get_env('RKD_WHITELIST_GROUPS').replace(' ', '').split(',') \
            if context.get_env('RKD_WHITELIST_GROUPS') else []

        # collect into groups
        for name, declaration in self._ctx.find_all_tasks().items():
            group_name = declaration.get_group_name()

            # (optional) whitelists of displayed groups
            if whitelisted_groups:
                group_to_whitelist_check = (':' + group_name) if group_name else ''  # allow empty group ([global])

                if group_to_whitelist_check not in whitelisted_groups:
                    continue

            if group_name not in groups:
                groups[group_name] = {}

            groups[group_name][self.translate_alias(declaration.to_full_name(), aliases)] = declaration

        # iterate over groups and list tasks under groups
        for group_name, tasks in groups.items():
            if not group_name:
                group_name = 'global'

            io.print_group(group_name)

            for task_name, declaration in tasks.items():
                declaration: TaskDeclarationInterface

                try:
                    description = declaration.get_description()
                    text_description = "# " + description if description else ""
                except AttributeError:
                    text_description = ""

                io.outln(task_name.ljust(50, ' ') + text_description)

            io.print_opt_line()

        io.print_opt_line()
        io.opt_outln('Use --help to see task environment variables and switches, eg. rkd :sh --help, rkd --help')

        return True

    @staticmethod
    def translate_alias(full_name: str, aliases: List[AliasGroup]) -> str:
        if not aliases:
            return full_name

        for alias in aliases:
            match = alias.get_aliased_task_name(full_name)

            if match:
                return match

        return full_name


class CallableTask(TaskInterface):
    """ Executes a custom callback - allows to quickly define a short task """

    _callable: Callable[[ExecutionContext, TaskInterface], bool]
    _args_callable: Callable[[ArgumentParser], None]
    _name: str
    _group: str
    _description: str
    _envs: dict

    def __init__(self, name: str, callback: Callable[[ExecutionContext, TaskInterface], bool],
                 args_callback: Callable[[ArgumentParser], None] = None,
                 description: str = '',
                 group: str = ''):
        self._name = name
        self._callable = callback
        self._args_callable = args_callback
        self._description = description
        self._group = group
        self._envs = {}

    def get_name(self) -> str:
        return self._name

    def get_description(self) -> str:
        return self._description

    def get_group_name(self) -> str:
        return self._group

    def configure_argparse(self, parser: ArgumentParser):
        if self._args_callable:
            self._args_callable(parser)

    def execute(self, context: ExecutionContext) -> bool:
        return self._callable(context, self)

    def push_env_variables(self, envs: dict):
        self._envs = deepcopy(envs)

    def get_declared_envs(self) -> Dict[str, str]:
        return self._envs


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
