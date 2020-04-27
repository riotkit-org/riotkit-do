#!/usr/bin/env python3

import unittest
from rkd.argparsing import CommandlineParsingHelper


class ArgParsingTest(unittest.TestCase):
    def test_creates_grouped_arguments_into_tasks__task_after_flag(self):
        """ Test parsing arguments """

        parsed = CommandlineParsingHelper.create_grouped_arguments([
            ':harbor:start', '--profile=test', '--fast-fail', ':status'
        ])

        self.assertEqual("[Task<harbor:start (['--profile=test', '--fast-fail'])>, Task<status ([])>]", str(parsed))

    def test_creates_grouped_arguments_into_tasks__raises_exception_on_unknown_part(self):
        """ The task name should begin with ':' """

        self.assertRaises(Exception, lambda: CommandlineParsingHelper.create_grouped_arguments([
            'harbor:start'
        ]))

    def test_creates_grouped_arguments_into_tasks__no_task_defined_goes_to_rkd_initialization(self):
        parsed = CommandlineParsingHelper.create_grouped_arguments([
            '--help'
        ])

        self.assertEqual("[Task<kd:initialize (['--help'])>]", str(parsed))

    def test_creates_grouped_arguments_into_tasks__tasks_only(self):
        parsed = CommandlineParsingHelper.create_grouped_arguments([
            ':harbor:start', ':harbor:status', ':harbor:stop'
        ])

        self.assertEqual("[Task<harbor:start ([])>, Task<harbor:status ([])>, Task<harbor:stop ([])>]", str(parsed))
