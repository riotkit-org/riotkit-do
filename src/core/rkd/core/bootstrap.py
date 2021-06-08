#!/usr/bin/env python3

"""
Bootstrap
=========

Initializes the application, passes arguments and environment variables from operating system
Only this layer can use sys.exit() call to pass exit code to the operating system
"""

import sys
import os
from dotenv import load_dotenv
from .execution.results import ProgressObserver
from .argparsing.parser import CommandlineParsingHelper
from .context import ContextFactory, ApplicationContext
from .resolver import TaskResolver
from .validator import TaskDeclarationValidator
from .execution.executor import OneByOneTaskExecutor
from .exception import TaskNotFoundException, ParsingException, YamlParsingException, CommandlineParsingError
from .api.inputoutput import SystemIO
from .api.inputoutput import UnbufferedStdout
from .aliasgroups import parse_alias_groups_from_env
from .packaging import find_resource_file
from . import env


class RiotKitDoApplication(object):
    _ctx: ApplicationContext
    _tasks_to_execute = []

    @staticmethod
    def load_environment():
        paths = env.rkd_paths()

        for path in paths:
            if os.path.isfile(path + '/.env'):
                load_dotenv(path + '/.env')

        load_dotenv(dotenv_path=os.getcwd() + '/.env')

    @staticmethod
    def make_stdout_unbuffered():
        sys.stdout = UnbufferedStdout(sys.stdout)

    @staticmethod
    def prepend_development_paths():
        """Add ./src at the beginning of PYTHONPATH - very useful for development"""

        sys.path = [os.getcwd() + '/src'] + sys.path

    def main(self, argv: list):
        if not CommandlineParsingHelper.has_any_task(argv) and not CommandlineParsingHelper.was_help_used(argv):
            self.print_banner_and_exit()

        # system wide IO instance with defaults, the :init task should override those settings
        io = SystemIO()
        io.silent = env.system_log_level() not in ['debug', 'internal']
        io.set_log_level(env.system_log_level())

        cmdline_parser = CommandlineParsingHelper(io)

        # preparse arguments that are before tasks
        preparsed_args = CommandlineParsingHelper.preparse_args(argv)

        # load context of components - all tasks, plugins etc.
        try:
            self._ctx = ContextFactory(io).create_unified_context(additional_imports=preparsed_args['imports'])

        except ParsingException as e:
            io.silent = False
            io.error_msg('Cannot import tasks/module from RKD_IMPORTS environment variable or --imports switch. '
                         'Details: {}'.format(str(e)))
            sys.exit(1)

        except YamlParsingException as e:
            io.silent = False
            io.error_msg('Cannot import tasks/module from one of makefile.yaml files. Details: {}'.format(str(e)))
            sys.exit(1)

        observer = ProgressObserver(io)
        task_resolver = TaskResolver(self._ctx, parse_alias_groups_from_env(os.getenv('RKD_ALIAS_GROUPS', '')))
        executor = OneByOneTaskExecutor(self._ctx, observer)

        # iterate over each task, parse commandline arguments
        try:
            requested_tasks = cmdline_parser.create_grouped_arguments([':init'] + argv[1:])
        except CommandlineParsingError as err:
            io.error_msg(str(err))
            sys.exit(1)

        # validate all tasks
        task_resolver.resolve(requested_tasks, TaskDeclarationValidator.assert_declaration_is_valid)

        # execute all tasks
        task_resolver.resolve(requested_tasks, executor.execute)

        executor.get_observer().execution_finished()

        sys.exit(1 if executor.get_observer().is_at_least_one_task_failing() else 0)

    @staticmethod
    def print_banner_and_exit():
        with open(find_resource_file('banner.txt'), 'rb') as banner_file:
            print(banner_file.read().replace(b'\\x1B', b'\x1B').decode('utf-8'))

        sys.exit(0)


def main():
    app = RiotKitDoApplication()
    app.make_stdout_unbuffered()
    app.prepend_development_paths()
    app.load_environment()

    try:
        app.main(argv=sys.argv)

    except TaskNotFoundException as e:
        print(e)
        sys.exit(127)


if __name__ == '__main__':
    main()
