#!/usr/bin/env python3

import os
import subprocess
import pytest
from tempfile import TemporaryDirectory
from rkd.core.api.testing import BasicTestingCase
from rkd.core.standardlib import CreateStructureTask
from rkd.core.api.inputoutput import BufferedSystemIO

TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
NAMESPACE_DIR = TESTS_DIR + '/../../'


@pytest.mark.e2e
@pytest.mark.long
class CreateStructureTaskTest(BasicTestingCase):
    @staticmethod
    def _execute_mocked_task(params: dict, envs: dict = None, task: CreateStructureTask = None) -> BufferedSystemIO:
        if envs is None:
            envs = {}

        io = BufferedSystemIO()

        if not task:
            task: CreateStructureTask = CreateStructureTask()

        BasicTestingCase.satisfy_task_dependencies(task, io=io)
        task.execute(BasicTestingCase.mock_execution_context(task, params, envs))

        return io

    def test_functional_creates_structure_in_temporary_directory(self):
        """Test a successful case"""

        with TemporaryDirectory() as tempdir:
            cwd = os.getcwd()

            try:
                os.chdir(tempdir)
                task = CreateStructureTask()
                task.get_rkd_version_selector = lambda use_latest: ''

                self._execute_mocked_task({
                    '--commit': False,
                    '--no-venv': False,
                    '--pipenv': False,
                    '--latest': False,
                    '--rkd-dev': False
                }, {}, task=task)

                self.assertTrue(os.path.isdir(tempdir + '/.rkd'),
                                msg='Expected that .rkd directory would be created')
                self.assertTrue(os.path.isfile(tempdir + '/requirements.txt'),
                                msg='Expected requirements.txt file to be present')
                self.assertTrue(os.path.isfile(tempdir + '/.venv/bin/activate'),
                                msg='Expected that virtual environment will contain a bin/activate file')
                self.assertFalse(os.path.isfile(tempdir + '/Pipfile'),
                                 msg='Expected that pipenv structure would not be created ' +
                                     'if --pipenv switch not used explicitly')

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

                task = CreateStructureTask()
                task.get_rkd_version_selector = lambda: ''
                io = self._execute_mocked_task(
                    params={
                        '--commit': True,
                        '--no-venv': False,
                        '--pipenv': False,
                        '--latest': False,
                        '--rkd-dev': False
                    },
                    envs={},
                    task=task
                )

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
                self._execute_mocked_task(
                    params={
                        '--commit': False,
                        '--no-venv': True,
                        '--pipenv': False,
                        '--latest': False,
                        '--rkd-dev': False
                    },
                    envs={}
                )

                # assertions
                self.assertTrue(os.path.isfile(tempdir + '/requirements.txt'),
                                msg='Expected requirements.txt file to be present')
                self.assertFalse(os.path.isfile(tempdir + '/.venv/bin/activate'))

            finally:
                os.chdir(cwd)

    def test_functional_interface_methods_are_called(self):
        """Verify that all defined extensible interface methods are called"""

        with TemporaryDirectory() as tempdir:
            cwd = os.getcwd()

            try:
                os.chdir(tempdir)
                subprocess.call(['git', 'init'])

                # verification
                call_history = []

                # mock
                task = CreateStructureTask()
                # do not set fixed version, as on local environment it could be some dev version not released yet
                task.get_rkd_version_selector = lambda use_latest: ''

                task.on_startup = lambda ctx: call_history.append('on_startup')
                task.on_files_copy = lambda ctx: call_history.append('on_files_copy')
                task.on_requirements_txt_write = lambda ctx: call_history.append('on_requirements_txt_write')
                task.on_creating_venv = lambda ctx: call_history.append('on_creating_venv')
                task.on_git_add = lambda ctx: call_history.append('on_git_add')
                task.get_patterns_to_add_to_gitignore = lambda ctx: [
                    'lets-ignore-all-the-opposites-of-fate-and-rise-up',
                    '.venv-setup.log'
                ]

                # action
                self._execute_mocked_task(
                    envs={},
                    task=task,
                    params={
                        '--commit': True,
                        '--no-venv': False,
                        '--pipenv': False,
                        '--latest': False,
                        '--rkd-dev': True
                    }
                )

                # assert that actions will be called in order

                with self.subTest('First time should copy files, create virtual env'):
                    self.assertEqual(
                        ['on_startup', 'on_files_copy', 'on_requirements_txt_write', 'on_creating_venv', 'on_git_add'],
                        call_history
                    )

                #
                # Reset to perform a test checking, that any next same task execution results in skipped files copying
                #
                call_history = []
                subprocess.check_call('echo "new" > new-file.txt; git add new-file.txt', shell=True)

                self._execute_mocked_task(
                    params={
                        '--commit': True,
                        '--no-venv': False,
                        '--pipenv': False,
                        '--latest': False,
                        '--rkd-dev': True
                    },
                    envs={},
                    task=task
                )

                with self.subTest('Any next time should not copy files over and over again'):
                    self.assertEqual(
                        ['on_startup', 'on_requirements_txt_write', 'on_creating_venv', 'on_git_add'],
                        call_history
                    )

            finally:
                os.chdir(cwd)

    def test_pipenv_is_supported(self):
        """Check that pipenv structure is created"""

        with TemporaryDirectory() as tempdir:
            cwd = os.getcwd()

            try:
                os.chdir(tempdir)
                task = CreateStructureTask()
                task.get_rkd_version_selector = lambda use_latest: ''

                io = self._execute_mocked_task({
                    '--commit': False,
                    '--no-venv': False,
                    '--pipenv': True,
                    '--latest': True,
                    '--rkd-dev': NAMESPACE_DIR
                }, {}, task=task)

                self.assertTrue(os.path.isdir(tempdir + '/.rkd'),
                                msg='Expected that .rkd directory would be created')
                self.assertTrue(os.path.isfile(tempdir + '/requirements.txt'),
                                msg='Expected requirements.txt file to be present')
                self.assertFalse(os.path.isfile(tempdir + '/.venv/bin/activate'),
                                 msg='Expected that a normal virtual env will not be created')
                self.assertTrue(os.path.isfile(tempdir + '/Pipfile'),
                                msg='Expected a Pipfile created by pipenv')
                self.assertTrue(os.path.isfile(tempdir + '/Pipfile.lock'),
                                msg='Expected a Pipfile.lock created by pipenv')
                self.assertIn('Structure created, use "pipenv shell" to enter project environment', io.get_value(),
                              msg='Expected a welcome message / instruction')

            finally:
                os.chdir(cwd)

    def test_local_directory_install(self):
        """
        Checks if with pipenv RKD is installed as local package in "editable" mode
        :return:
        """

        with TemporaryDirectory() as tempdir:
            cwd = os.getcwd()

            try:
                os.chdir(tempdir)

                # action
                self._execute_mocked_task(
                    params={
                        '--commit': False,
                        '--no-venv': False,
                        '--pipenv': True,
                        '--latest': True,
                        '--rkd-dev': NAMESPACE_DIR
                    },
                    envs={}
                )

                # assertions
                with open(tempdir + '/Pipfile', 'r') as f:
                    pipfile = f.read()

                self.assertIn('"rkd.process" = {editable = true, path = "', pipfile)
                self.assertIn('"rkd.core" = {editable = true, path = "', pipfile)

            finally:
                os.chdir(cwd)
