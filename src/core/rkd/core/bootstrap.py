#!/usr/bin/env python3

"""
Bootstrap
=========

Initializes the application, passes arguments and environment variables from operating system
Only this layer can use sys.exit() call to pass exit code to the operating system
"""

import sys
import os
import traceback
from typing import Optional
from dotenv import load_dotenv

from rkd.core.execution.lifecycle import ConfigurationResolver
from .execution.results import ProgressObserver
from .argparsing.parser import CommandlineParsingHelper
from .context import ContextFactory, ApplicationContext
from .resolver import TaskResolver
from .validator import TaskDeclarationValidator
from .execution.executor import OneByOneTaskExecutor
from .exception import TaskNotFoundException, ParsingException, StaticFileParsingException, CommandlineParsingError, \
    HandledExitException, AggregatedResolvingFailure
from .api.inputoutput import SystemIO, LEVEL_DEBUG
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

    @staticmethod
    def increment_depth():
        """
        Note how many RKD we launched inside RKD... RKD->RKD->RKD->...->RKD
        :return:
        """

        os.environ['RKD_DEPTH'] = str(env.rkd_depth() + 1)

    @staticmethod
    def setup_global_io(pre_parsed_args: dict) -> SystemIO:
        """
        SystemIO is the default IO instance that is used BETWEEN tasks.
        Some of its setting are later INHERITED into IO of tasks, it is done explicit using inheritation method.
        :return:
        """

        io = SystemIO()
        io.silent = (pre_parsed_args['log_level'] not in ['debug', 'internal']) and pre_parsed_args['silent']
        io.set_log_level(pre_parsed_args['log_level'])

        if env.rkd_ui() is not None:
            io.set_display_ui(env.rkd_ui())

        if env.rkd_depth() >= 2 or pre_parsed_args['no_ui']:
            io.set_display_ui(False)

        return io

    def main(self, argv: list):
        if not CommandlineParsingHelper.has_any_task(argv) and not CommandlineParsingHelper.was_help_used(argv):
            self.print_banner_and_exit()

        self.increment_depth()

        # parse arguments that are before tasks e.g. rkd --help (in comparison to rkd :task1 --help)
        pre_parsed_args = CommandlineParsingHelper.preparse_global_arguments_before_tasks(argv[1:])

        # system wide IO instance with defaults
        io = self.setup_global_io(pre_parsed_args)

        cmdline_parser = CommandlineParsingHelper(io)

        # load context of components - all tasks, plugins etc.
        try:
            io.internal_lifecycle('Loading all contexts and building an unified context')
            self._ctx = ContextFactory(io).create_unified_context(additional_imports=pre_parsed_args['imports'])

        except ParsingException as e:
            io.silent = False
            io.error_msg('Cannot import tasks/module from RKD_IMPORTS environment variable or --imports switch. '
                         'Details: {}'.format(str(e)))
            sys.exit(1)

        except StaticFileParsingException as e:
            io.silent = False
            io.error_msg('Cannot import tasks/module from one of makefile.yaml files. Details: {}'.format(str(e)))
            sys.exit(1)

        observer = ProgressObserver(io)
        task_resolver = TaskResolver(self._ctx, parse_alias_groups_from_env(os.getenv('RKD_ALIAS_GROUPS', '')))
        executor = OneByOneTaskExecutor(self._ctx, observer)
        config_resolver = ConfigurationResolver(io)

        # iterate over each task, parse commandline arguments
        try:
            requested_tasks = cmdline_parser.create_grouped_arguments(argv[1:])

        except CommandlineParsingError as err:
            io.error_msg(str(err))
            sys.exit(1)

        try:
            io.internal_lifecycle('Resolving tasks')
            resolved_tasks_to_execute = task_resolver.resolve(requested_tasks)

            # resolve configuration
            io.internal_lifecycle('Resolving configurations')
            config_resolver.iterate(resolved_tasks_to_execute)

            # # validate all tasks, it's input arguments
            io.internal_lifecycle('Validating tasks')
            TaskDeclarationValidator(io).iterate(resolved_tasks_to_execute)

            # # execute all tasks
            io.internal_lifecycle('Executing tasks')
            executor.iterate(resolved_tasks_to_execute)

        except AggregatedResolvingFailure as aggregated:
            io.print_opt_line()
            io.error_msg('Cannot resolve, configure or execute tasks, at least one of scheduled tasks has invalid '
                         'initialization, configuration, or it does not exist. '
                         'Try to re-run with RKD_SYS_LOG_LEVEL=debug')

            io.print_separator()

            num = 0

            for err in aggregated.exceptions:
                num += 1
                self.print_err(io, err, num)

            if pre_parsed_args['print_event_history']:
                executor.get_observer().print_event_history()

            sys.exit(1)

        except HandledExitException as err:
            if io.is_log_level_at_least(LEVEL_DEBUG):
                self.print_err(io, err)

            sys.exit(1)

        executor.get_observer().execution_finished()

        if pre_parsed_args['print_event_history']:
            executor.get_observer().print_event_history()

        sys.exit(1 if executor.get_observer().is_at_least_one_task_failing() else 0)

    @staticmethod
    def print_banner_and_exit():
        with open(find_resource_file('banner.txt'), 'rb') as banner_file:
            print(banner_file.read().replace(b'\\x1B', b'\x1B').decode('utf-8'))

        sys.exit(0)

    @staticmethod
    def print_err(io: SystemIO, err: Exception, num: Optional[int] = None):
        msg = str(err)

        if num:
            msg = f'[{num}] {msg}'

        io.error_msg(msg)

        if err.__cause__:
            io.error("HandledExitException occurred, original traceback:\n" +
                     "\n".join(traceback.format_tb(err.__cause__.__traceback__)))

        if io.is_log_level_at_least(LEVEL_DEBUG):
            io.error("\n".join(traceback.format_tb(err.__traceback__)))


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
