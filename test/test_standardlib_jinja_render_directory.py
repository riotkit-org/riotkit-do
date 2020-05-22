#!/usr/bin/env python3

import unittest
from rkd.standardlib.jinja import RenderDirectoryTask
from rkd.test import mock_task, mock_execution_context


class TestRenderDirectoryTask(unittest.TestCase):
    """Tests for a task that should render JINJA2 files from DIRECTORY "A" to DIRECTORY "B"
    """

    @staticmethod
    def _execute_mocked_task(params: dict) -> tuple:
        task: RenderDirectoryTask = RenderDirectoryTask()
        mock_task(task)

        calls = []
        deletions = []

        # mocks _render() method
        def mock__render(source_path: str, target_path: str) -> bool:
            calls.append('"%s" -> "%s"' % (source_path, target_path))

            return True

        task._render = mock__render
        task._delete_file = lambda file: deletions.append(file)

        # run task
        task.execute(mock_execution_context(task, params))

        return calls, deletions

    def test_naming(self):
        self.assertEqual(':j2:directory-to-directory', RenderDirectoryTask().get_full_name())

    def test_iterates_over_subdirectories_including_depth_and_pattern(self):
        """Test with pattern, no source files deletion
        """
        renderings, deletions = self._execute_mocked_task({
            'source': '../',
            'target': '/tmp',
            'delete_source_files': False,
            'pattern': '(.*)(src|test)/(.*).py$'
        })

        # example files (please correct if changed in filesystem)
        self.assertIn('"../test/test_standardlib_jinja_render_directory.py" -> "/tmp/test/test_standardlib_jinja_render_directory.py"', renderings)
        self.assertIn('"../src/__init__.py" -> "/tmp/src/__init__.py"', renderings)

        # directories should not be included
        self.assertNotIn('"../src/" -> "/tmp/src/"', renderings)
        self.assertNotIn('"../src" -> "/tmp/src"', renderings)

    def test_without_pattern(self):
        """What happens if we specify no pattern?
        """
        renderings, deletions = self._execute_mocked_task({
            'source': '../',
            'target': '/tmp',
            'delete_source_files': False,
            'pattern': ''
        })

        # example files (please correct if changed in filesystem)
        self.assertIn('README.', str(renderings))
        self.assertIn('requirements.txt', str(renderings))
        self.assertIn('__init__.py', str(renderings))

    def test_no_files_deleted_when_option_disabled(self):
        renderings, deletions = self._execute_mocked_task({
            'source': '../',
            'target': '/tmp',
            'delete_source_files': False,
            'pattern': ''
        })

        self.assertEqual([], deletions)

    def test_files_are_called_to_be_deleted(self):
        renderings, deletions = self._execute_mocked_task({
            'source': '../',
            'target': '/tmp',
            'delete_source_files': True,
            'pattern': '(.*)test_standardlib_jinja_render_directory.py$'
        })

        self.assertEqual(['../test/test_standardlib_jinja_render_directory.py'], deletions)
