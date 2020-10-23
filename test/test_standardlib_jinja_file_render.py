#!/usr/bin/env python3

import os
from rkd.standardlib.jinja import FileRendererTask
from rkd.api.inputoutput import BufferedSystemIO
from rkd.api.testing import BasicTestingCase

SAMPLES_PATH = os.path.dirname(os.path.realpath(__file__)) + '/internal-samples'


class TestFileRendererTask(BasicTestingCase):
    """Tests for a task that should render single JINJA2 file from SOURCE PATH to TARGET PATH
    """

    @staticmethod
    def _execute_mocked_task(params: dict, envs: dict = {}) -> BufferedSystemIO:
        io = BufferedSystemIO()

        task: FileRendererTask = FileRendererTask()

        BasicTestingCase.satisfy_task_dependencies(task, io=io)
        execution_context = BasicTestingCase.mock_execution_context(task, params, envs)

        task.execute(execution_context)

        return io

    def test_naming(self):
        self.assertEqual(':j2:render', FileRendererTask().get_full_name())

    def test_renders_file_considering_environment_variables(self):
        """Test that file is properly rendered
        """

        msg = '22 May 1918 Spanish civil war fighter Dolores Jiménez Alvarez was born. Fought in ' + \
              'the Durruti column until arrested by the Communists. Then escaped and joined French ' + \
              'resistance and underground resistance to Franco'

        io = self._execute_mocked_task(
            # shell arguments
            {
                'source': SAMPLES_PATH + '/jinja2/example.j2',
                'output': '-'
            },
            # env variables
            {
                'MESSAGE': msg
            }
        )

        self.assertEqual('Listen to this important message: `%s`\n' % msg, io.get_value())

    def test_non_existing_source_file_raises_error(self):
        """Test that error message will be printed in case, when source file does not exist
        """

        io = self._execute_mocked_task(
            {
                'source': 'non-existing',
                'output': '-'
            }
        )

        self.assertIn('Source file does not exist at path "non-existing"', io.get_value())

    def test_undefined_variable_raises_error(self):
        """Test that JINJA2 will raise an exception, and it will be formatted properly
        """
        io = self._execute_mocked_task(
            # shell arguments
            {
                'source': SAMPLES_PATH + '/jinja2/example.j2',
                'output': '-'
            },
            # env variables
            {
                # "MESSAGE" variable should be defined, but is not - to test if error will be raised
            }
        )

        self.assertIn("Undefined variable - 'MESSAGE' is undefined", io.get_value())
        self.assertNotIn('Traceback (most recent call last):', io.get_value())

    def test_renders_with_extends_section(self):
        """Test that JINJA2 finds files on disk in current directory when using {% extends "..." %}"""

        cwd_copy = os.getcwd()
        os.chdir('../test/internal-samples/jinja2')

        try:
            io = self._execute_mocked_task(
                # shell arguments
                {
                    'source': SAMPLES_PATH + '/jinja2/example-with-extends.j2',
                    'output': '-'
                },
                # env variables
                {
                }
            )
        finally:
            os.chdir(cwd_copy)

        self.assertIn('Teresa Claramunt was born.', io.get_value())
        self.assertIn('played a leading role in the 1911 Aragon general strike.', io.get_value())
        self.assertIn('When she died 50k workers went to her funeral', io.get_value())
