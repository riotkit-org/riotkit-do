#!/usr/bin/env python3

import os
import subprocess
import unittest
from tempfile import TemporaryDirectory
from rkd.standardlib import CreateStructureTask
from rkd.test import mock_task, mock_execution_context
from rkd.inputoutput import BufferedSystemIO


class CreateStructureTaskTest(unittest.TestCase):
    @staticmethod
    def _execute_mocked_task(params: dict, envs: dict = {}) -> BufferedSystemIO:
        io = BufferedSystemIO()

        task: CreateStructureTask = CreateStructureTask()
        mock_task(task, io=io)
        task.execute(mock_execution_context(task, params, envs))

        return io

    def test_functional_creates_structure_in_temporary_directory(self):
        """Test a successful case"""

        with TemporaryDirectory() as tempdir:
            cwd = os.getcwd()

            try:
                os.chdir(tempdir)
                self._execute_mocked_task({
                    '--commit': False,
                    '--no-venv': False
                }, {})

                self.assertTrue(os.path.isdir(tempdir + '/.rkd'),
                                msg='Expected that .rkd directory would be created')
                self.assertTrue(os.path.isfile(tempdir + '/requirements.txt'),
                                msg='Expected requirements.txt file to be present')
                self.assertTrue(os.path.isfile(tempdir + '/.venv/bin/activate'),
                                msg='Expected that virtual environment will contain a bin/activate file')

            finally:
                os.chdir(cwd)

    def test_functional_detects_git_is_dirty(self):
        """Verify that GIT workspace is unclean - there are pending working changes not commited"""

        with TemporaryDirectory() as tempdir:
            cwd = os.getcwd()

            try:
                os.chdir(tempdir)

                # ---------------------------
                # Prepare the workspace first
                # ---------------------------
                subprocess.call(['git', 'init'])
                subprocess.call('echo "test-1" > test-file.txt; git add test-file.txt', shell=True)
                subprocess.call('git commit -m "First commit"', shell=True)
                # make the working tree dirty by editing a file without a commit
                subprocess.call('echo "changed" > test-file.txt', shell=True)

                io = self._execute_mocked_task({
                    '--commit': True,
                    '--no-venv': False
                }, {})

                self.assertIn('Current working directory is dirty', io.get_value())
            finally:
                os.chdir(cwd)

    def test_functional_no_virtualenv_environment_is_created_when_a_switch_was_used(self):
        """Verify that --no-venv switch would end with skipped virtual environment creation"""

        with TemporaryDirectory() as tempdir:
            cwd = os.getcwd()

            try:
                os.chdir(tempdir)

                # action
                self._execute_mocked_task({'--commit': False, '--no-venv': True}, {})

                # assertions
                self.assertTrue(os.path.isfile(tempdir + '/requirements.txt'),
                                msg='Expected requirements.txt file to be present')
                self.assertFalse(os.path.isfile(tempdir + '/.venv/bin/activate'))

            finally:
                os.chdir(cwd)
