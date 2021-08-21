import os
import subprocess
import pytest
from tempfile import TemporaryDirectory
from rkd.core.api.inputoutput import BufferedSystemIO
from rkd.core.api.temp import TempManager
from rkd.core.api.testing import FunctionalTestingCase
from rkd.core.standardlib.io import ArchivePackagingBaseTask

TEST_PATH = os.path.realpath(__file__)


@pytest.mark.e2e
class ArchivePackagingTaskTest(FunctionalTestingCase):
    backup_stdout = False

    def test_dry_run_just_prints_messages(self):
        """
        Check two things:
          - Dry run mode should not produce zip file
          - Messages should be printed

        :return:
        """

        io = BufferedSystemIO()
        task = ArchivePackagingBaseTask()
        self.satisfy_task_dependencies(task, io=io)

        # configure
        task.archive_path = '/tmp/something.zip'
        task.archive_type = 'zip'
        task.add('./tests/internal-samples')
        task.add(TEST_PATH, 'test.py')

        # execute
        task.execute(self.mock_execution_context(
            task,
            {
                "--dry-run": True,
                "--allow-overwrite": False
            },
            {}
        ))

        self.assertIn('test_standardlib_io_archivepackagingtask.py" -> "test.py"', io.get_value())
        self.assertIn('subprojects/testsubproject1/.rkd/makefile.yaml" -> "', io.get_value())
        self.assertFalse(os.path.isfile('/tmp/something.zip'))

    def test_archive_overwrite_is_not_allowed_when_switch_not_used(self):
        """
        Create archive TWICE without --allow-overwrite set
        Expected behavior:
            1st time) Just write the archive
            2nd time) Raise an exception that the archive already exists
            3rd time) Overwrite the archive, don't raise an error

        :return:
        """

        tasks = []
        temp = TempManager()
        archive_path = temp.create_tmp_file_path()[0]  # same for two tasks

        try:
            for i in range(0, 3):
                io = BufferedSystemIO()
                task = ArchivePackagingBaseTask()
                self.satisfy_task_dependencies(task, io=io)

                task.archive_path = archive_path
                task.archive_type = 'zip'
                task.add(TEST_PATH, 'test.py')
                tasks.append(task)

            tasks[0].execute(self.mock_execution_context(
                tasks[0],
                {
                    "--dry-run": False,
                    "--allow-overwrite": False
                },
                {}
            ))

            with self.assertRaises(FileExistsError) as exc:
                tasks[1].execute(self.mock_execution_context(
                    tasks[1],
                    {
                        "--dry-run": False,
                        "--allow-overwrite": False
                    },
                    {}
                ))

            tasks[2].execute(self.mock_execution_context(
                tasks[2],
                {
                    "--dry-run": False,
                    "--allow-overwrite": True
                },
                {}
            ))

            self.assertIn('already exists, use --allow-overwrite to enforce recreation', str(exc.exception))
            self.assertIn('-> "test.py"', tasks[2].io().get_value())

        finally:
            temp.finally_clean_up()

    def test_slash_in_src_at_end_results_in_not_including_last_src_directory(self):
        io = BufferedSystemIO()
        task = ArchivePackagingBaseTask()
        self.satisfy_task_dependencies(task, io=io)

        temp = TempManager()
        archive_path = temp.create_tmp_file_path()[0]

        task.archive_path = archive_path
        task.archive_type = 'zip'
        task.add(os.path.dirname(TEST_PATH) + '/internal-samples/', 'examples')

        task.execute(self.mock_execution_context(
            task,
            {
                "--dry-run": True,
                "--allow-overwrite": False
            },
            {}
        ))

        self.assertIn('internal-samples/jinja2/example.j2" -> "examples/jinja2/example.j2"', io.get_value())

    def test_not_having_slash_at_end_of_src_path_results_in_including_last_folder_name(self):
        io = BufferedSystemIO()
        task = ArchivePackagingBaseTask()
        self.satisfy_task_dependencies(task, io=io)

        temp = TempManager()
        archive_path = temp.create_tmp_file_path()[0]

        task.archive_path = archive_path
        task.archive_type = 'zip'
        task.add(os.path.dirname(TEST_PATH) + '/internal-samples', 'examples')

        task.execute(self.mock_execution_context(
            task,
            {
                "--dry-run": True,
                "--allow-overwrite": False
            },
            {}
        ))

        self.assertIn('internal-samples/jinja2/example.j2" -> "internal-samples/examples/jinja2/example.j2"',
                      io.get_value())

    def test_selected_gitignore_is_considered(self):
        """
        Create 3 files - .gitignore, to-be-ignored.txt, example.py
        Add to-be-ignored.txt to be ignored
        Schedule a copy of whole directory containing those 3 files

        Expected:
            To copy: .gitignore, example.py
            To ignore: to-be-ignored.txt

        :return:
        """

        io = BufferedSystemIO()
        io.set_log_level('debug')

        # prepare task
        task = ArchivePackagingBaseTask()
        self.satisfy_task_dependencies(task, io=io)

        # prepare workspace
        with TemporaryDirectory() as sources_path:
            with open(sources_path + '/.gitignore', 'w') as gitignore:
                gitignore.write("to-be-ignored.txt\n")

            with open(sources_path + '/to-be-ignored.txt', 'w') as f:
                f.write("test\n")

            with open(sources_path + '/example.py', 'w') as f:
                f.write("#!/usr/bin/env python3\nprint('Hello anarchism!')\n")

            # consider our gitignore that will ignore "to-be-ignored.txt"
            task.consider_ignore(sources_path + '/.gitignore')

            # add a batch of files
            task.add(sources_path)

        self.assertNotRegex(io.get_value(), f'Ignoring "(.*)/example.py"')
        self.assertRegex(io.get_value(), f'Ignoring "(.*)/to-be-ignored.txt"')

    def test_consider_ignore_recursively(self):
        """
        Test that consider_ignore_recursively() method loads .gitignore files recursively

        Directory structure:
            - /.gitignore
            - /subdir1/second-to-be-ignored.c
            - /subdir1/subdir2/to-be-ignored.txt
            - /subdir1/subdir2/.gitignore
            - /example.py

        :return:
        """

        io = BufferedSystemIO()
        io.set_log_level('debug')

        # prepare task
        task = ArchivePackagingBaseTask()
        self.satisfy_task_dependencies(task, io=io)

        # prepare workspace
        with TemporaryDirectory() as sources_path:
            # create a subdirectory, for the depth
            subprocess.check_call(['mkdir', '-p', sources_path + '/subdir1/subdir2'])

            with open(sources_path + '/.gitignore', 'w') as gitignore:
                gitignore.write("subdir1/second-to-be-ignored.c\n")

            with open(sources_path + '/subdir1/subdir2/.gitignore', 'w') as gitignore:
                gitignore.write("to-be-ignored.txt\n")

            with open(sources_path + '/subdir1/subdir2/to-be-ignored.txt', 'w') as f:
                f.write("test\n")

            with open(sources_path + '/subdir1/second-to-be-ignored.c', 'w') as f:
                f.write("test\n")

            with open(sources_path + '/example.py', 'w') as f:
                f.write("#!/usr/bin/env python3\nprint('Hello anarchism!')\n")

            task.consider_ignore_recursively(sources_path, filename='.gitignore')
            task.add(sources_path)

        self.assertRegex(io.get_value(), 'Ignoring "(.*)/subdir1/second-to-be-ignored.c"')
        self.assertRegex(io.get_value(), 'Ignoring "(.*)/subdir1/subdir2/to-be-ignored.txt"')

        what_should_be = [
            sources_path + '/.gitignore',
            sources_path + '/subdir1/subdir2/.gitignore',
            sources_path + '/example.py'
        ]

        what_should_NOT_be = [
            sources_path + '/subdir1/subdir2/to-be-ignored.txt',
            sources_path + '/subdir1/second-to-be-ignored.c'
        ]

        for item_should_be in what_should_be:
            self.assertIn(item_should_be, task.sources)

        for item_should_not_be in what_should_NOT_be:
            self.assertNotIn(item_should_not_be, task.sources)
