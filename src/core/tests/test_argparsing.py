#!/usr/bin/env python3
import os
import pytest
from argparse import ArgumentParser
from unittest import mock

from rkd.core.api.inputoutput import IO, BufferedSystemIO
from rkd.core.api.testing import BasicTestingCase
from rkd.core.argparsing.parser import CommandlineParsingHelper
from rkd.core.exception import CommandlineParsingError
from rkd.core.test import get_test_declaration


@pytest.mark.argparsing
class ArgParsingTest(BasicTestingCase):
    should_backup_env = False

    def test_creates_grouped_arguments_into_tasks__task_after_flag(self):
        """ Test parsing arguments """

        parsed = CommandlineParsingHelper(IO()).create_grouped_arguments([
            ':harbor:start', '--profile=test', '--fast-fail', ':status'
        ])

        self.assertEqual("[\"ArgumentBlock<[':harbor:start', '--profile=test', '--fast-fail'], "
                         "[TaskCall<:harbor:start (['--profile=test', '--fast-fail'])>]>\", "
                         "\"ArgumentBlock<[':status'], [TaskCall<:status ([])>]>\"]",
                         str(self.list_to_str(parsed)))

    def test_creates_grouped_arguments_into_tasks__tasks_only(self):
        parsed = CommandlineParsingHelper(IO()).create_grouped_arguments([
            ':harbor:start', ':harbor:status', ':harbor:stop'
        ])

        self.assertEqual("[\"ArgumentBlock<[':harbor:start'], [TaskCall<:harbor:start ([])>]>\", "
                         "\"ArgumentBlock<[':harbor:status'], [TaskCall<:harbor:status ([])>]>\", "
                         "\"ArgumentBlock<[':harbor:stop'], [TaskCall<:harbor:stop ([])>]>\"]",
                         str(list(map(lambda a: str(a), parsed))))

    def test_add_env_variables_to_argparse(self):
        parser = ArgumentParser(':test')
        task = get_test_declaration()

        CommandlineParsingHelper.add_env_variables_to_argparse_description(parser, task)
        self.assertIn('ORG_NAME (default: International Workers Association)', parser.description)

    def test_add_env_variables_to_argparse__no_envs(self):
        parser = ArgumentParser(':test')
        task = get_test_declaration()

        # empty the values
        task.get_task_to_execute().get_declared_envs = lambda: {}

        CommandlineParsingHelper.add_env_variables_to_argparse_description(parser, task)
        self.assertNotIn('ORG_NAME (default: International Workers Association)', parser.description)
        self.assertIn('-- No environment variables declared --', parser.description)

    def test_arguments_usage(self):
        """Check that arguments are recognized"""

        parsed = CommandlineParsingHelper(IO()).create_grouped_arguments([
            ':strike:start', 'now'
        ])

        self.assertEqual("[\"ArgumentBlock<[':strike:start', 'now'], [TaskCall<:strike:start (['now'])>]>\"]",
                         str(self.list_to_str(parsed)))

    def test_arguments_usage_with_switch_before(self):
        """Check that arguments are recognized - variant with an additional switch"""

        parsed = CommandlineParsingHelper(IO()).create_grouped_arguments([
            ':strike:start', '--general', 'now'
        ])

        self.assertEqual(
            "[\"ArgumentBlock<[':strike:start', '--general', 'now'], "
            "[TaskCall<:strike:start (['--general', 'now'])>]>\"]",
            str(self.list_to_str(parsed)))

    def test_global_arguments_are_shared_for_all_tasks(self):
        """When we define a "@" task, then it is not present as a task (removed from tasks list), but its arguments
        are inherited to next tasks
        """

        parsed = CommandlineParsingHelper(IO()).create_grouped_arguments([
            '@', '--grassroot',
            ':strike:start', '--general', 'now',
            ':picket:start', '--at', 'exploiters-shop'
        ])

        self.assertEqual(
            "[\"ArgumentBlock<[':strike:start', '--general', 'now'], [TaskCall<:strike:start (['--general', 'now', '--grassroot'])>]>\", "
            "\"ArgumentBlock<[':picket:start', '--at', 'exploiters-shop'], [TaskCall<:picket:start (['--at', 'exploiters-shop', '--grassroot'])>]>\"]",
            str(self.list_to_str(parsed))
        )

    def test_global_arguments_are_cleared_after_inserting_alone_at_symbol(self):
        """When we define a "@" task, then it is not present as a task (removed from tasks list), but its arguments
        are inherited to next tasks.

        When we define a "@" again later, then any next tasks do not inherit previous "@" arguments (clearing)
        """

        parsed = CommandlineParsingHelper(IO()).create_grouped_arguments([
            '@', '--duration=30d',
            ':strike:start', '--general', 'now',
            '@',  # expecting: --duration will be cleared and not applied to :picket:start
            ':picket:start', '--at', 'exploiters-shop'
        ])

        self.assertEqual(
            "[\"ArgumentBlock<[':strike:start', '--general', 'now'], [TaskCall<:strike:start (['--general', 'now', '--duration=30d'])>]>\", "
            "\"ArgumentBlock<[':picket:start', '--at', 'exploiters-shop'], [TaskCall<:picket:start (['--at', 'exploiters-shop'])>]>\"]",
            str(self.list_to_str(parsed))
        )

    def test_global_arguments_are_changed_when_using_at_symbol_twice(self):
        """When we define a "@" task, then it is not present as a task (removed from tasks list), but its arguments
        are inherited to next tasks.

        When we define a "@" again later, then any next tasks do not inherit previous "@" arguments (clearing).

        What we can expect:
            - Output of create_grouped_arguments() will not return any tasks and blocks with "@" tasks
            - Arguments after "@" task will be propagated to next tasks
        """

        self.maxDiff = None

        parsed = CommandlineParsingHelper(IO()).create_grouped_arguments([
            '@', '--type', 'human-rights',  # this one propagates --type=human-rights to next line
            ':join:activism', '--organization', 'black-lives-matter',
            '@', '--type', 'working-class-rights',  # this one clears previous "@" and sets a new propagation
            ':join:activism', '--organization', 'international-workers-association',
            '@',  # this one clears propagation at all, no any previous arguments will be passed to :send:mail
            ':send:mail'
        ])

        self.assertEqual(
            "[\"ArgumentBlock<[':join:activism', '--organization', 'black-lives-matter'], "
            "[TaskCall<:join:activism (['--organization', 'black-lives-matter', '--type', 'human-rights'])>]>\", "
            "\"ArgumentBlock<[':join:activism', '--organization', 'international-workers-association'], "
            "[TaskCall<:join:activism (['--organization', 'international-workers-association', '--type', 'working-class-rights'])>]>\", "
            "\"ArgumentBlock<[':send:mail'], [TaskCall<:send:mail ([])>]>\"]",
            str(self.list_to_str(parsed))
        )

    def test_preparse_args_tolerates_not_recognized_args(self):
        """
        Normally argparse would break the test. If it returns a value EVEN if there are unrecognized arguments,
        then it works
        """

        args = CommandlineParsingHelper.preparse_global_arguments_before_tasks(['--imports', 'rkd.pythonic', ':sh'])

        self.assertIn('imports', args)
        self.assertEqual(['rkd.pythonic'], args['imports'])

    def test_preparse_ignores_arguments_after_tasks(self):
        """
        Arguments that could be preparsed should be placed behind any task
        """

        args = CommandlineParsingHelper.preparse_global_arguments_before_tasks([':sh', '--imports', 'rkd_python'])

        self.assertEqual([], args['imports'])

    def test_has_any_task(self):
        """
        Checks if a commandline string has any task
        """

        with self.subTest(':task'):
            self.assertTrue(CommandlineParsingHelper.has_any_task([':task']))

        with self.subTest('--help :task'):
            self.assertTrue(CommandlineParsingHelper.has_any_task(['--help', ':task']))

        with self.subTest(':task --test'):
            self.assertTrue(CommandlineParsingHelper.has_any_task([':task', '--test']))

        with self.subTest('--imports rkd.pythonic --help'):
            self.assertFalse(CommandlineParsingHelper.has_any_task(['--imports', 'rkd.pythonic', '--help']))

    def test_was_help_used(self):
        """
        Checks if "--help" switch was used at all
        :return:
        """

        with self.subTest('--help'):
            self.assertTrue(CommandlineParsingHelper.was_help_used(['--help']))

        with self.subTest('-h'):
            self.assertTrue(CommandlineParsingHelper.was_help_used(['-h']))

        with self.subTest('Not used - empty string'):
            self.assertFalse(CommandlineParsingHelper.was_help_used([]))

        with self.subTest('Not used - non empty string - :tasks --print'):
            self.assertFalse(CommandlineParsingHelper.was_help_used([':tasks', '--print']))

    def test_pre_parse_arguments_parses_arguments_before_first_task(self):
        result = CommandlineParsingHelper.preparse_global_arguments_before_tasks([
            '--log-level=debug', ':task1', '--something'
        ])

        self.assertEqual(
            {'imports': [], 'log_level': 'debug', 'silent': False, 'no_ui': False},
            result
        )

    def test_preparse_global_arguments_before_tasks_parses_imports_from_switch(self):
        result = CommandlineParsingHelper.preparse_global_arguments_before_tasks([
            '--imports', 'rkd.core.something1:something2'
        ])

        self.assertEqual(
            ['rkd.core.something1', 'something2'],
            result['imports']
        )

    @mock.patch.dict(os.environ, {"RKD_IMPORTS": "bakunin:malatesta"}, clear=False)
    def test_preparse_global_arguments_before_tasks_parses_imports_from_env(self):
        result = CommandlineParsingHelper.preparse_global_arguments_before_tasks([])

        self.assertEqual(
            ['bakunin', 'malatesta'],
            result['imports']
        )

    @mock.patch.dict(os.environ, {"RKD_SYS_LOG_LEVEL": "internal"}, clear=True)
    def test_preparse_global_arguments_before_tasks_reacts_on_sys_log_level_env(self):
        result = CommandlineParsingHelper.preparse_global_arguments_before_tasks([])

        self.assertEqual(
            'internal',
            result['log_level']
        )

    def test_pre_parse_arguments_parses_arguments_before_first_block(self):
        result = CommandlineParsingHelper.preparse_global_arguments_before_tasks([
            '--log-level=debug', '{@retry 3}', '--something', '{/@}'
        ])

        self.assertEqual(
            {'imports': [], 'log_level': 'debug', 'silent': False, 'no_ui': False},
            result
        )

    def test_parse_blocks_when_at_least_two_tasks_in_block_and_at_least_one_outside(self):
        io = BufferedSystemIO()
        result = CommandlineParsingHelper(io).create_grouped_arguments(
            [
                ':db:dump', '--file', 'db.sql',  # block 1
                '{@retry 3 @rescue :db:rollback}', ':db:upgrade', ':db:test', '{/@}',  # block 2
                ':db:restart'  # block 3
            ]
        )

        self.assertEqual(3, len(result), msg='Expected 3 blocks')
        self.assertEqual(':db:rollback', result[1].on_rescue[0].name())

        self.assertEqual(
            ["ArgumentBlock<[':db:dump', '--file', 'db.sql'], [TaskCall<:db:dump (['--file', 'db.sql'])>]>",
             "ArgumentBlock<[':db:upgrade', ':db:test'], [TaskCall<:db:upgrade ([])>, TaskCall<:db:test ([])>]>",
             "ArgumentBlock<[':db:restart'], [TaskCall<:db:restart ([])>]>"],
            list(map(str, result)),
            msg='Expected 3 blocks with scheduled tasks in order'
        )

    def test_create_grouped_arguments_keeps_commandline_switches_in_rescue_block(self):
        """
        Checks that commandline switches are not lost - e.g. {@rescue :db:rollback --version 1 --debug}
        """

        io = BufferedSystemIO()
        result = CommandlineParsingHelper(io).create_grouped_arguments(
            [
                '{@retry 3 @rescue :db:rollback --version 1 --debug}', ':db:upgrade', '{/@}'
            ]
        )

        self.assertEqual("TaskCall<:db:rollback (['--version', '1', '--debug'])>", str(result[0].on_rescue[0]))

    def test_create_grouped_arguments_keeps_retry(self):
        io = BufferedSystemIO()
        result = CommandlineParsingHelper(io).create_grouped_arguments(
            [
                '{@retry 3}', ':flaky:task', '{/@}'
            ]
        )

        self.assertEqual(0, result[0].retry_whole_block)
        self.assertEqual(3, result[0].retry_per_task)

    def test_create_grouped_arguments_keeps_retry_per_block(self):
        io = BufferedSystemIO()
        result = CommandlineParsingHelper(io).create_grouped_arguments(
            [
                '{@retry-block 3}', ':flaky:task', '{/@}'
            ]
        )

        self.assertEqual(3, result[0].retry_whole_block)
        self.assertEqual(0, result[0].retry_per_task)

    def test_create_grouped_arguments_has_defined_unknown_modifier(self):
        with self.assertRaises(CommandlineParsingError) as exc:
            CommandlineParsingHelper(BufferedSystemIO()).create_grouped_arguments(
                [
                    '{@unknown :hehe}', ':flaky:task', '{/@}'
                ]
            )

        self.assertEqual(
            'Block "{@unknown :hehe" contains invalid modifier, raised error: Unknown modifier "unknown"',
            str(exc.exception)
         )
