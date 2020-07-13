#!/usr/bin/env python3

import os
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
