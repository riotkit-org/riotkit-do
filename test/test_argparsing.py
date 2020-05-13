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

    def test_creates_grouped_arguments_into_tasks__raises_exception_on_unknown_part(self):
        """ The task name should begin with ':' """

        self.assertRaises(Exception, lambda: CommandlineParsingHelper.create_grouped_arguments([
            'harbor:start'
        ]))

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
        self.assertIn('Union (default: International Workers Association)', parser.description)

    def test_add_env_variables_to_argparse__no_envs(self):
        parser = ArgumentParser(':test')
        task = get_test_declaration()

        # empty the values
        task.get_task_to_execute().get_declared_envs = lambda: {}

        CommandlineParsingHelper.add_env_variables_to_argparse(parser, task)
        self.assertNotIn('Union (default: International Workers Association)', parser.description)
        self.assertIn('-- No environment variables declared --', parser.description)
