#!/usr/bin/env python3

import os
import sys
import unittest
import tempfile
import subprocess
from copy import deepcopy
from tempfile import NamedTemporaryFile
from typing import Tuple
from contextlib import contextmanager
from io import StringIO
from rkd.api.inputoutput import IO
from rkd import RiotKitDoApplication

SCRIPT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class TestFunctional(unittest.TestCase):
    """
    Functional tests case of the whole application.
    Runs application like from the shell, captures output and performs assertions on the results.
    """

    _stdout = None
    _stderr = None

    def setUp(self) -> None:
        os.environ['RKD_DEPTH'] = '0'
        self._stdout = sys.stdout
        self._stderr = sys.stderr

    def _restore_standard_out(self):
        sys.stdout = self._stdout
        sys.stderr = self._stderr

    @contextmanager
    def environment(self, environ: dict):
        backup = deepcopy(os.environ)

        try:
            os.environ.update(environ)
            yield
        finally:
            os.environ = backup

    def _run_and_capture_output(self, argv: list) -> Tuple[str, int]:
        io = IO()
        out = StringIO()
        exit_code = 0

        try:
            # debug: enable_standard_out=True when debugging tests
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
        self.assertIn('--become', full_output)
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
        """Checks if RKD is able to log output to file per task
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
                self.assertIn(':sh', content)  # one of tasks
                self.assertIn('rkd.standardlib.VersionTask', content)

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

    def test_env_variables_not_listed_in_sh_task(self):
        """ :sh does not define any environment variables """

        full_output, exit_code = self._run_and_capture_output([':sh', '--help'])
        self.assertNotIn('- RKD_DEPTH (default: )', full_output)
        self.assertIn('-- No environment variables declared --', full_output)

    def test_tasks_whitelist_shows_only_selected_groups(self):
        """Test that when we set RKD_WHITELIST_GROUPS=:rkd, then we will see only tasks from [rkd] group"""

        with self.environment({'RKD_WHITELIST_GROUPS': ':rkd'}):
            full_output, exit_code = self._run_and_capture_output([':tasks'])

        self.assertIn(':rkd:create-structure', full_output)
        self.assertNotIn(':exec', full_output)

    def test_task_whitelist_shows_only_global_group(self):
        """Test that when we set RKD_WHITELIST_GROUPS=,, then we will see only tasks from [global] group"""

        with self.environment({'RKD_WHITELIST_GROUPS': ','}):
            full_output, exit_code = self._run_and_capture_output([':tasks'])

        self.assertIn(':tasks', full_output)
        self.assertNotIn(':rkd:create-structure', full_output)

    def test_task_alias_resolves_task(self):
        """Test that with RKD_ALIAS_GROUPS=":py->:class-war" the :class-war:build would be resolved to :py:build"""

        with self.environment({'RKD_ALIAS_GROUPS': ':class-war->:rkd'}):
            full_output, exit_code = self._run_and_capture_output([':class-war:create-structure', '--help'])

        self.assertIn('usage: :rkd:create-structure', full_output)

    def test_env_variables_loaded_from_various_sources(self):
        """:hello task should print variables loaded globally and per-task using "environment" and "env_files"
        """

        with self.environment({'RKD_PATH': SCRIPT_DIR_PATH + '/../docs/examples/env-in-yaml/.rkd'}):
            full_output, exit_code = self._run_and_capture_output([':hello'])

            self.assertIn('Inline defined in this task: 17 May 1972 10,000 schoolchildren in the UK walked out on' +
                          ' strike in protest against corporal punishment. Within two years, London state schools ' +
                          'banned corporal punishment. The rest of the country followed in 1987.', full_output)

            self.assertIn('Inline defined globally: 16 May 1966, seamen across the UK walked out on a nationwide ' +
                          'strike for the first time in half a century. Holding solid for seven weeks, they won a' +
                          ' reduction in working hours from 56 to 48 per week', full_output)

            self.assertIn('Included globally - global.env: Jolanta Brzeska was a social activist against evictions,' +
                          ' she was murdered - burned alive by reprivatization mafia', full_output)

            self.assertIn('Included in task - per-task.env: 24 April 2013, the 8-storey Rana Plaza building in ' +
                          'Bangladesh collapsed, killing over 1,000 garment workers, as bosses in the ' +
                          'country\'s largest industry put profits before people', full_output)

    def test_help_shows_full_task_description(self):
        """:hello --help should show full description, even if it is multiline
        """

        with self.environment({'RKD_PATH': SCRIPT_DIR_PATH + '/../docs/examples/env-in-yaml/.rkd'}):
            full_output, exit_code = self._run_and_capture_output([':hello', '--help'])

            self.assertIn('Italian-American anarchist who was framed & executed', full_output)
            self.assertIn('#2 line: This is his short autobiography:', full_output)
            self.assertIn('#3 line: https://libcom.org/library/story-proletarian-life', full_output)

    def test_depth_increased(self):
        """Test that RKD_DEPTH is increased within next calls
        """

        full_output, exit_code = self._run_and_capture_output(
            [':sh', '-c', '%RKD% :sh -c \'echo "DEPTH: [$RKD_DEPTH]"\'']
        )

        self.assertIn('DEPTH: [2]', full_output)

    def test_depth_above_2_disables_ui(self):
        """Test that RKD in RKD will not show UI (fancy messages like "Executing ...")
        """

        full_output, exit_code = self._run_and_capture_output([
            '--no-ui', ':sh', '-c', '%RKD% :tasks'
        ])

        self.assertIn(':tasks', full_output)
        self.assertNotIn('>> Executing', full_output)

    def test_env_file_is_loaded_from_cwd(self):
        """Assert that .env file is loaded from current working directory
        """

        cwd_backup = os.getcwd()

        try:
            # 1. Create new working directory
            with tempfile.TemporaryDirectory() as tempdir:
                os.chdir(tempdir)

                # 2. Create example .env file
                with open(tempdir + '/.env', 'w') as f:
                    f.write("DURRUTI_BIRTHDAY_DATE=14.07.1896\n")

                # 3. Run
                full_output = subprocess.check_output(
                    sys.executable + " -m rkd :sh -c 'echo \"Durruti was born at $DURRUTI_BIRTHDAY_DATE\"'",
                    env={'PYTHONPATH': SCRIPT_DIR_PATH + '/../src'},
                    shell=True
                )

                # 4. Assert
                self.assertIn('Durruti was born at 14.07.1896', full_output.decode('utf-8'))
        finally:
            os.chdir(cwd_backup)

    def test_aliases_are_resolved_recursively(self):
        """TaskAliasDeclaration can run other TaskAliasDeclaration task

        Example:
        ```bash
        TaskAliasDeclaration(':hello', ['sh', '-c', "Hello world"]),
        TaskAliasDeclaration(':alias-in-alias-test', [':hello'])
        ```
        """

        with self.environment({'RKD_PATH': SCRIPT_DIR_PATH + '/../docs/examples/makefile-like/.rkd'}):
            full_output, exit_code = self._run_and_capture_output([':alias-in-alias-test'])

            self.assertIn('Hello world', full_output)
