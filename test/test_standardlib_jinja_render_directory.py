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

        def mock__render(source_path: str, target_path: str) -> bool:
            calls.append('"%s" -> "%s"' % (source_path, target_path))

            return True

        def mock__sh(*args, **kwargs):
            calls.append('sh(' + ' '.join(args) + ')')

        task._render = mock__render
        task.sh = mock__sh
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
            'pattern': '(.*)(src|test)/(.*).py$',
            '--exclude-pattern': '',
            '--copy-not-matching-files': False
        })

        # example files (please correct if changed in filesystem)
        self.assertIn('"../test/test_standardlib_jinja_render_directory.py" ' +
                      '-> "/tmp/test/test_standardlib_jinja_render_directory.py"', renderings)
        self.assertIn('"../src/__init__.py" -> "/tmp/src/__init__.py"', renderings)

        # directories should not be included
        self.assertNotIn('"../src/" -> "/tmp/src/"', renderings)
        self.assertNotIn('"../src" -> "/tmp/src"', renderings)

    def test_files_are_copied_when_not_matching_pattern_but_switch_was_used(self):
        """Test --copy-not-matching-files switch that adds a possibility to copy all files from SOURCE to DESTINATION
        The difference is that those files that does not match PATTERN will be copied without rendering.

        Additionally uses "--exclude-pattern" to exclude redundant files
        """

        renderings, deletions = self._execute_mocked_task({
            'source': '../test',
            'target': '/tmp',
            'delete_source_files': False,
            'pattern': '(.*).j2',
            '--exclude-pattern': '(.*).pyc',
            '--copy-not-matching-files': True
        })

        flatten_list_as_str = ' '.join(renderings)

        with self.subTest('Check --copy-not-matching-files - the non (.*).j2 files should be just copied ' +
                          'instead of rendered'):

            self.assertIn('sh(cp -p "../test/test_standardlib_jinja_render_directory.py" ' +
                          '"/tmp//test_standardlib_jinja_render_directory.py")', renderings)

        with self.subTest('Check --exclude-pattern'):
            self.assertNotIn('.pyc', flatten_list_as_str)

    def test_without_pattern(self):
        """What happens if we specify no pattern?
        """
        renderings, deletions = self._execute_mocked_task({
            'source': '../',
            'target': '/tmp',
            'delete_source_files': False,
            'pattern': '',
            '--exclude-pattern': '',
            '--copy-not-matching-files': False
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
            'pattern': '',
            '--exclude-pattern': '',
            '--copy-not-matching-files': False
        })

        self.assertEqual([], deletions)

    def test_files_are_called_to_be_deleted(self):
        renderings, deletions = self._execute_mocked_task({
            'source': '../',
            'target': '/tmp',
            'delete_source_files': True,
            'pattern': '(.*)test_standardlib_jinja_render_directory.py$',
            '--exclude-pattern': '',
            '--copy-not-matching-files': False
        })

        self.assertEqual(['../test/test_standardlib_jinja_render_directory.py'], deletions)
