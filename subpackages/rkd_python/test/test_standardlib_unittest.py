from typing import List
from rkd.api.testing import BasicTestingCase
from rkd.api.inputoutput import IO
from rkd_python.core import UnitTestTask


class UnitTestTaskTest(BasicTestingCase):

    def _exec_task(self, parameters: dict) -> List[str]:
        parameters_merged = {
            '--src-dir': './',
            '--tests-dir': 'test',
            '--pattern': 'test*.py',
            '--filter': '',
            '--python-bin': ''
        }

        parameters_merged.update(parameters)

        task = UnitTestTask()
        self.satisfy_task_dependencies(task, IO())

        sh_calls = []
        task.sh = lambda *args, **kwargs: sh_calls.append(args[0])

        task.execute(self.mock_execution_context(
            task,
            parameters_merged
        ))

        return sh_calls

    def test_considers_switches_executable(self):
        sh_calls = self._exec_task({'--python-bin': 'custom-python'})
        self.assertIn('custom-python -m unittest', sh_calls[0])

    def test_sets_pythonpath_to_sources_directory(self):
        sh_calls = self._exec_task({'--src-dir': '/opt/src'})
        self.assertIn('export PYTHONPATH="/opt/src:$PYTHONPATH";', sh_calls[0])

    def test_filter_not_present_when_not_used(self):
        sh_calls = self._exec_task({})
        self.assertNotIn(' -k ', sh_calls[0])

    def test_filter_is_present_if_value_set(self):
        sh_calls = self._exec_task({'--filter': 'UnitTestTaskTest'})
        self.assertIn(' -k ', sh_calls[0])

    def test_pattern_present(self):
        sh_calls = self._exec_task({'--pattern': 'functional_test_*.py'})
        self.assertIn(' -p \'functional_test_*.py\' ', sh_calls[0])
