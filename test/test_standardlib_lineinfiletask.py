#!/usr/bin/env python3

import unittest
from tempfile import NamedTemporaryFile
from rkd.standardlib import LineInFileTask
from rkd.test import mock_task, mock_execution_context
from rkd.api.inputoutput import BufferedSystemIO


class TestLineInFileTask(unittest.TestCase):
    @staticmethod
    def _execute_mocked_task(params: dict, envs: dict = {}) -> BufferedSystemIO:
        io = BufferedSystemIO()

        task: LineInFileTask = LineInFileTask()
        mock_task(task, io=io)
        task.execute(mock_execution_context(task, params, envs))

        return io

    def test_simply_appends_line_if_it_does_not_exists(self):
        with NamedTemporaryFile() as tmp_file:
            self._execute_mocked_task({
                'file': tmp_file.name,
                '--regexp': 'Linux ([0-9.]+)',
                '--insert': 'Linux 4.16.1',
                '--fail-on-no-occurrence': False,
                '--only-first-occurrence': False
            })

            self.assertIn("Linux 4.16.1\n", tmp_file.read().decode('utf-8'))

    def test_simply_replaces_found_one_matched_line(self):
        with NamedTemporaryFile() as tmp_file:
            # at first add initial file content
            with open(tmp_file.name, 'w') as fw:
                fw.write('Text: Hello')

            # then modify it
            self._execute_mocked_task({
                'file': tmp_file.name,
                '--regexp': 'Text: (.*)',
                '--insert': 'Text: 14 June 1872 unions were legalised in Canada through the Trade Unions Act after a' +
                            ' wave of illegal strikes and protests. Still the law didn\'t compel employers to' +
                            ' recognise or bargain with unions, and picketing remained illegal.',
                '--fail-on-no-occurrence': False,
                '--only-first-occurrence': False
            })

            self.assertIn("14 June 1872 unions were legalised in Canada", tmp_file.read().decode('utf-8'))

    def test_advanced_replaces_using_regexp_pattern(self):
        """Tests usage of regexp groups eg. $match[0], $match[1] etc."""

        with NamedTemporaryFile() as tmp_file:
            # at first add initial file content
            with open(tmp_file.name, 'w') as fw:
                fw.write('Symbol: 1')

            # then modify it
            self._execute_mocked_task({
                'file': tmp_file.name,
                '--regexp': 'Symbol: ([0-9]+)',
                '--insert': 'Symbol: $match[0] + 161',
                '--fail-on-no-occurrence': False,
                '--only-first-occurrence': False
            })

            self.assertIn("Symbol: 1 + 161", tmp_file.read().decode('utf-8'))

    def test_fails_when_no_occurrence_and_flag_is_set(self):
        """Test flag --fail-on-no-occurrence"""

        with NamedTemporaryFile() as tmp_file:
            io = self._execute_mocked_task({
                'file': tmp_file.name,
                '--regexp': 'Knock knock',
                '--insert': 'Who\'s there?',
                '--fail-on-no-occurrence': True,
                '--only-first-occurrence': False
            })

            self.assertIn('No matching line for selected regexp found', io.get_value())

    def test_replaces_only_first_occurrence(self):
        """Test that only one occurrence will be replaced"""

        with NamedTemporaryFile() as tmp_file:
            # at first add initial file content
            with open(tmp_file.name, 'w') as fw:
                fw.write("Symbol: 1\n")
                fw.write("Color: Red\n")
                fw.write("Symbol: 2\n")
                fw.write("\n\n")
                fw.write("Dog or cat: Dog\n")

            # then modify it
            self._execute_mocked_task({
                'file': tmp_file.name,
                '--regexp': 'Symbol: ([0-9]+)',
                '--insert': 'Symbol: 161',
                '--fail-on-no-occurrence': True,
                '--only-first-occurrence': True
            })

            processed_file_content = tmp_file.read().decode('utf-8')

            self.assertIn("Symbol: 161", processed_file_content)
            self.assertNotIn("Symbol: 1\n", processed_file_content)
            self.assertIn("Symbol: 2", processed_file_content)
