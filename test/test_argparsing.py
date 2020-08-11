#!/usr/bin/env python3

import unittest
from argparse import ArgumentParser
from rkd.argparsing import CommandlineParsingHelper
from rkd.test import get_test_declaration


class ArgParsingTest(unittest.TestCase):
    def test_creates_grouped_arguments_into_tasks__task_after_flag(self):
        """ Test parsing arguments """

        parsed = CommandlineParsingHelper.create_grouped_arguments([
            ':harbor:start', '--profile=test', '--fast-fail', ':status'
        ])

        self.assertEqual("[Task<:harbor:start (['--profile=test', '--fast-fail'])>, Task<:status ([])>]", str(parsed))

    def test_creates_grouped_arguments_into_tasks__no_task_defined_goes_to_rkd_initialization(self):
        parsed = CommandlineParsingHelper.create_grouped_arguments([
            '--help'
        ])

        self.assertEqual("[Task<rkd:initialize (['--help'])>]", str(parsed))

    def test_creates_grouped_arguments_into_tasks__tasks_only(self):
        parsed = CommandlineParsingHelper.create_grouped_arguments([
            ':harbor:start', ':harbor:status', ':harbor:stop'
        ])

        self.assertEqual("[Task<:harbor:start ([])>, Task<:harbor:status ([])>, Task<:harbor:stop ([])>]", str(parsed))

    def test_add_env_variables_to_argparse(self):
        parser = ArgumentParser(':test')
        task = get_test_declaration()

        CommandlineParsingHelper.add_env_variables_to_argparse(parser, task)
        self.assertIn('ORG_NAME (default: International Workers Association)', parser.description)

    def test_add_env_variables_to_argparse__no_envs(self):
        parser = ArgumentParser(':test')
        task = get_test_declaration()

        # empty the values
        task.get_task_to_execute().get_declared_envs = lambda: {}

        CommandlineParsingHelper.add_env_variables_to_argparse(parser, task)
        self.assertNotIn('ORG_NAME (default: International Workers Association)', parser.description)
        self.assertIn('-- No environment variables declared --', parser.description)

    def test_arguments_usage(self):
        """Check that arguments are recognized"""

        parsed = CommandlineParsingHelper.create_grouped_arguments([
            ':strike:start', 'now'
        ])

        self.assertEqual("[Task<:strike:start (['now'])>]", str(parsed))

    def test_arguments_usage_with_switch_before(self):
        """Check that arguments are recognized - variant with an additional switch"""

        parsed = CommandlineParsingHelper.create_grouped_arguments([
            ':strike:start', '--general', 'now'
        ])

        self.assertEqual("[Task<:strike:start (['--general', 'now'])>]", str(parsed))

    def test_global_arguments_are_shared_for_all_tasks(self):
        """When we define a "@" task, then it is not present as a task (removed from tasks list), but its arguments
        are inherited to next tasks
        """

        parsed = CommandlineParsingHelper.create_grouped_arguments([
            '@', '--grassroot',
            ':strike:start', '--general', 'now',
            ':picket:start', '--at', 'exploiters-shop'
        ])

        self.assertEqual(
            "[Task<:strike:start (['--general', 'now', '--grassroot'])>, " +
            "Task<:picket:start (['--at', 'exploiters-shop', '--grassroot'])>]",
            str(parsed)
        )

    def test_global_arguments_are_cleared_after_inserting_alone_at_symbol(self):
        """When we define a "@" task, then it is not present as a task (removed from tasks list), but its arguments
        are inherited to next tasks.

        When we define a "@" again later, then any next tasks do not inherit previous "@" arguments (clearing)
        """

        parsed = CommandlineParsingHelper.create_grouped_arguments([
            '@', '--duration=30d',
            ':strike:start', '--general', 'now',
            '@',  # expecting: --duration will be cleared and not applied to :picket:start
            ':picket:start', '--at', 'exploiters-shop'
        ])

        self.assertEqual(
            "[Task<:strike:start (['--general', 'now', '--duration=30d'])>, " +
            "Task<:picket:start (['--at', 'exploiters-shop'])>]",
            str(parsed)
        )

    def test_global_arguments_are_changed_when_using_at_symbol_twice(self):
        """When we define a "@" task, then it is not present as a task (removed from tasks list), but its arguments
        are inherited to next tasks.

        When we define a "@" again later, then any next tasks do not inherit previous "@" arguments (clearing)
        """

        self.maxDiff = None

        parsed = CommandlineParsingHelper.create_grouped_arguments([
            '@', '--type', 'human-rights',
            ':join:activism', '--organization', 'black-lives-matter',
            '@', '--type', 'working-class-rights',
            ':join:activism', '--organization', 'international-workers-association',
            '@',
            ':send:mail'
        ])

        self.assertEqual(
            "[Task<:join:activism (['--organization', 'black-lives-matter', '--type', 'human-rights'])>, " +
            "Task<:join:activism (['--organization', 'international-workers-association', '--type', 'working-class-rights'])>, " +
            "Task<:send:mail ([])>]",
            str(parsed)
        )
