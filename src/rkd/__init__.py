#!/usr/bin/env python3

import sys
import os
from dotenv import load_dotenv
from .argparsing import CommandlineParsingHelper
from .context import ContextFactory, ApplicationContext
from .resolver import TaskResolver
from .validator import TaskDeclarationValidator
from .execution.executor import OneByOneTaskExecutor
from .exception import TaskNotFoundException
from .api.inputoutput import SystemIO, LEVEL_INFO as LOG_LEVEL_INFO
from .api.inputoutput import UnbufferedStdout
from .aliasgroups import parse_alias_groups_from_env


class RiotKitDoApplication:
    _ctx: ApplicationContext
    _tasks_to_execute = []

    @staticmethod
    def load_environment():
        paths = os.getenv('RKD_PATH', '').split(':')

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
        if not argv[1:]:
            self.print_banner_and_exit()

        # system wide IO instance with defaults, the :init task should override those settings
        io = SystemIO()
        io.silent = True
        io.log_level = LOG_LEVEL_INFO

        # load context of components
        self._ctx = ContextFactory(io).create_unified_context()

        resolver = TaskResolver(self._ctx, parse_alias_groups_from_env(os.getenv('RKD_ALIAS_GROUPS', '')))
        executor = OneByOneTaskExecutor(self._ctx)

        # iterate over each task, parse commandline arguments
        requested_tasks = CommandlineParsingHelper.create_grouped_arguments([':init'] + argv[1:])

        # validate all tasks
        resolver.resolve(requested_tasks, TaskDeclarationValidator.assert_declaration_is_valid)

        # execute all tasks
        resolver.resolve(requested_tasks, executor.execute)

        executor.get_observer().execution_finished()

        sys.exit(1 if executor.get_observer().has_at_least_one_failed_task() else 0)

    @staticmethod
    def print_banner_and_exit():
        with open(os.path.dirname(os.path.realpath(__file__)) + '/misc/banner.txt', 'rb') as banner_file:
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
