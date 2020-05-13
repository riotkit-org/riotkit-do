#!/usr/bin/env python3

import os
import sys
import unittest
from tempfile import NamedTemporaryFile
from typing import Tuple
from io import StringIO
from rkd.inputoutput import IO
from rkd import RiotKitDoApplication


class TestFunctional(unittest.TestCase):
    """
    Functional tests case of the whole application.
    Runs application like from the shell, captures output and performs assertions on the results.
    """

    _stdout = None
    _stderr = None

    def setUp(self) -> None:
        self._stdout = sys.stdout
        self._stderr = sys.stderr

    def _restore_standard_out(self):
        sys.stdout = self._stdout
        sys.stderr = self._stderr

    def _run_and_capture_output(self, argv: list) -> Tuple[str, int]:
        io = IO()
        out = StringIO()
        exit_code = 0

        try:
            with io.capture_descriptors(stream=out, enable_standard_out=False):
                app = RiotKitDoApplication()
                app.main(['test_functional.py'] + argv)

        except SystemExit as e:
            self._restore_standard_out()
            exit_code = e.code

        return out.getvalue(), exit_code

    def test_tasks_listing(self):
        """ :tasks """

        full_output, exit_code = self._run_and_capture_output([':tasks'])

        self.assertIn(' >> Executing :tasks', full_output)
        self.assertIn('[global]', full_output)
        self.assertIn(':version', full_output)
        self.assertIn('succeed.', full_output)
        self.assertEqual(0, exit_code)

    def test_global_help_switch(self):
        """ --help """

        full_output, exit_code = self._run_and_capture_output(['--help'])

        self.assertIn('usage: :init', full_output)
        self.assertIn('--log-to-file', full_output)
        self.assertIn('--log-level', full_output)
        self.assertIn('--keep-going', full_output)
        self.assertIn('--silent', full_output)
        self.assertEqual(0, exit_code)

    def test_silent_switch_makes_tasks_task_to_not_show_headers(self):
        full_output, exit_code = self._run_and_capture_output([':tasks', '--silent'])

        # this is a global header
        self.assertIn(' >> Executing :tasks', full_output)

        # this is a header provided by :tasks
        self.assertNotIn('[global]', full_output)

        # the content is there
        self.assertIn(':exec', full_output)

    def test_global_silent_switch_is_making_silent_all_fancy_output(self):
        full_output, exit_code = self._run_and_capture_output(['--silent', ':tasks'])

        # content is there
        self.assertIn(':exec', full_output)

        # global formatting and per task - :tasks formatting is not there
        self.assertNotIn('>> Executing :tasks', full_output)   # global (SystemIO)
        self.assertNotIn('[global]', full_output)              # per-task (IO)

    def test_logging_tasks_into_separate_files(self):
        """
        Checks if RKD is able to log output to file per task
        :return:
        """

        first = NamedTemporaryFile(delete=False)
        second = NamedTemporaryFile(delete=False)

        try:
            self._run_and_capture_output([
                ':version',
                '--log-to-file=' + first.name,

                ':tasks',
                '--log-to-file=' + second.name
            ])
        finally:
            # assertions
            with open(first.name) as first_handle:
                content = first_handle.read()

                self.assertIn('RKD version', content)  # RKD version globally as a tool
                self.assertIn(':sh version', content)  # one of tasks

            with open(second.name) as second_handle:
                content = second_handle.read()

                self.assertIn(':exec', content)
                self.assertIn(':tasks', content)
                self.assertNotIn('>> Executing', content, msg='Global formatting should not be present')

                # assert that there is no output from previous task
                self.assertNotIn('RKD version', content)
                self.assertNotIn(':sh version', content)

                # clean up
            os.unlink(first.name)
            os.unlink(second.name)

    def test_env_variables_listed_in_help(self):
        full_output, exit_code = self._run_and_capture_output(['--help'])
        self.assertIn('- RKD_DEPTH (default: 0)', full_output)

    def test_env_variables_not_listed_in_tasks_task(self):
        """ :tasks does not define any environment variables """

        full_output, exit_code = self._run_and_capture_output([':tasks', '--help'])
        self.assertNotIn('- RKD_DEPTH (default: 0)', full_output)
        self.assertIn('-- No environment variables declared --', full_output)
