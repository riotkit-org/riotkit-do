import os
import pytest
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
