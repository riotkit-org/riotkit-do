#!/usr/bin/env python3

import os

from rkd.api.testing import BasicTestingCase
from rkd.standardlib.jinja import RenderDirectoryTask

TESTS_DIR = os.path.dirname(os.path.realpath(__file__))


class TestRenderDirectoryTask(BasicTestingCase):
    """Tests for a task that should render JINJA2 files from DIRECTORY "A" to DIRECTORY "B"
    """

    @staticmethod
    def _execute_mocked_task(params: dict, env: dict = {}) -> tuple:
        task: RenderDirectoryTask = RenderDirectoryTask()
        BasicTestingCase.satisfy_task_dependencies(task)

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
        task.execute(
            BasicTestingCase.mock_execution_context(task, params, env)
        )

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
            '--copy-not-matching-files': False,
            '--template-filenames': False
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
            '--copy-not-matching-files': True,
            '--template-filenames': False
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
            '--copy-not-matching-files': False,
            '--template-filenames': False
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
            '--copy-not-matching-files': False,
            '--template-filenames': False
        })

        self.assertEqual([], deletions)

    def test_files_are_called_to_be_deleted(self):
        renderings, deletions = self._execute_mocked_task({
            'source': '../',
            'target': '/tmp',
            'delete_source_files': True,
            'pattern': '(.*)test_standardlib_jinja_render_directory.py$',
            '--exclude-pattern': '',
            '--copy-not-matching-files': False,
            '--template-filenames': False
        })

        self.assertEqual(['../test/test_standardlib_jinja_render_directory.py'], deletions)

    def test_replace_vars_in_filename(self):
        name = RenderDirectoryTask().replace_vars_in_filename({'Word': 'triumph'}, 'that-agony-is-your---Word--.txt')

        self.assertEqual('that-agony-is-your-triumph.txt', name)

    def test_replace_vars_in_filename_multiple_occurrences(self):
        name = RenderDirectoryTask()\
            .replace_vars_in_filename({'word': 'pueblo', 'word2': 'hijos'}, '--word2--_del_--word--(--word--_version)')

        self.assertEqual('hijos_del_pueblo(pueblo_version)', name)

    def test_filename_templating_when_switch_is_on(self):
        """Assert that variables in filenames are also replaced, not only in the content

        Condition: When the "--template-filenames" is used
        """

        renderings, deletions = self._execute_mocked_task({
            'source': TESTS_DIR + '/internal-samples/jinja2-filename-templating',
            'target': '/tmp',
            'delete_source_files': True,
            'pattern': '(.*).j2',
            '--exclude-pattern': '',
            '--copy-not-matching-files': True,
            '--template-filenames': True
        }, env={
            'song_name': 'hijos-del-pueblo',
            'song2_name': 'a-las-barricadas'
        })

        self.assertIn('-> "/tmp//lyrics-hijos-del-pueblo.txt"', ' '.join(renderings),
                      msg='Expected that the matching .j2 file would have changed name')
        self.assertIn('"/tmp//lyrics2-a-las-barricadas.txt"', ' '.join(renderings),
                      msg='Expected that the non-j2 file would have also changed name')

    def test_filename_templating_is_not_replacing_vars_when_switch_is_not_used(self):
        """Checks if the variable replacing in filenames can be turned off by not using
        "--template-filenames" switch"""

        renderings, deletions = self._execute_mocked_task({
            'source': TESTS_DIR + '/internal-samples/jinja2-filename-templating',
            'target': '/tmp',
            'delete_source_files': True,
            'pattern': '(.*).j2',
            '--exclude-pattern': '',
            '--copy-not-matching-files': False,
            '--template-filenames': False
        }, env={
            'song_name': 'hijos-del-pueblo'
        })

        self.assertIn('-> "/tmp//lyrics---song_name--.txt"', ' '.join(renderings))
