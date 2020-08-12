#!/usr/bin/env python3

import unittest
import os
from io import StringIO
from rkd.contract import ExecutionContext
from rkd.api.inputoutput import BufferedSystemIO
from rkd.api.inputoutput import IO
from rkd.test import get_test_declaration
from rkd.test import mock_task
from rkd.execution.declarative import DeclarativeExecutor
from rkd.execution.declarative import Step

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class TestDeclarativeExecutor(unittest.TestCase):
    @staticmethod
    def _create_callable_tester(code: str, language: str, io: IO = None) -> bool:
        if not io:
            io = IO()

        executor = DeclarativeExecutor()
        declaration = get_test_declaration()
        declaration.get_task_to_execute()._io = io
        ctx = ExecutionContext(declaration)

        step = Step(
            language=language,
            task_name=':test',
            code=code,
            envs={},
            task_num=1,
            rkd_path=''
        )

        if language == 'python':
            return executor.execute_python_step(ctx, declaration.get_task_to_execute(), step)
        else:
            return executor.execute_bash_step(ctx, declaration.get_task_to_execute(), step)

    def test_bash_successful_case(self):
        """ Bash callable test: Successful case """

        io = IO()
        out = StringIO()

        with io.capture_descriptors(stream=out, enable_standard_out=False):
            self._create_callable_tester('python --version', language='bash')

        self.assertIn("Python", out.getvalue())
        self.assertTrue(out.getvalue(), msg='python --version should result with a True')

    def test_bash_failure_case_on_invalid_exit_code(self):
        """ Bash callable test: Check if failures are correctly catched """

        result = self._create_callable_tester('exit 161', language='bash', io=BufferedSystemIO())

        self.assertFalse(result)

    def test_python_case_syntax_error(self):
        result = self._create_callable_tester('''impppport os''', language='python', io=BufferedSystemIO())

        self.assertFalse(result)

    def test_python_case_multiline_with_imports_and_call_to_this(self):
        result = self._create_callable_tester('''
import os


# do a very simple verification of class names, if not defined then it would fail
return "ExecutionContext" in str(ctx) and "Task" in str(this)
    ''', language='python')

        self.assertTrue(result)

    def test_bash_case_verify_env_variables_are_present(self):

        io = IO()
        out = StringIO()

        with io.capture_descriptors(stream=out, enable_standard_out=False):
            self._create_callable_tester('echo "Boolean: ${ARG_TEST}, Text: ${ARG_MESSAGE}"', language='bash')

        self.assertIn('ARG_TEST: unbound variable', out.getvalue())

    def test_executing_multiple_steps_one_by_one_the_order_is_preserved(self):
        """Assert that execution order is preserved - as we register steps"""

        io = IO()
        str_io = StringIO()

        task_declaration = get_test_declaration()
        mock_task(task_declaration.get_task_to_execute(), io=io)

        ctx = ExecutionContext(task_declaration)
        executor = DeclarativeExecutor()
        executor.add_step('python', 'this.io().outln("First"); return True', task_name=':first', rkd_path='', envs={})
        executor.add_step('bash', 'echo "Second"; exit 0', task_name=':second', rkd_path='', envs={})
        executor.add_step('python', 'this.io().outln("Third"); return True', task_name=':third', rkd_path='', envs={})

        with io.capture_descriptors(target_files=[], stream=str_io, enable_standard_out=False):
            executor.execute_steps_one_by_one(ctx, task_declaration.get_task_to_execute())

        self.assertEqual("First\nSecond\nThird\n", str_io.getvalue())

    def test_one_failed_step_is_preventing_next_steps_from_execution_and_result_is_marked_as_failure(self):
        """Check the correctness of error handling"""

        io = IO()
        str_io = StringIO()
        buffered = BufferedSystemIO()

        task_declaration = get_test_declaration()
        mock_task(task_declaration.get_task_to_execute(), io=buffered)

        ctx = ExecutionContext(task_declaration)
        executor = DeclarativeExecutor()
        executor.add_step('python', 'this.io().outln("Peter Kropotkin"); return True', task_name=':first', rkd_path='', envs={})
        executor.add_step('bash', 'echo "Buenaventura Durruti"; exit 1', task_name=':second', rkd_path='', envs={})
        executor.add_step('python', 'this.io().outln("This one will not show"); return True', task_name=':third', rkd_path='', envs={})

        with io.capture_descriptors(target_files=[], stream=str_io, enable_standard_out=False):
            final_result = executor.execute_steps_one_by_one(ctx, task_declaration.get_task_to_execute())

        output = str_io.getvalue() + buffered.get_value()

        self.assertIn('Peter Kropotkin', output)
        self.assertIn('Buenaventura Durruti', output)
        self.assertNotIn('This one will not show', output)
        self.assertEqual(False, final_result)

    def test_return_false_is_added_to_the_code(self):
        """Assert that code in Python without a "return" will have "return false" by default

        Previously, when return was not added automatically there was an error raised (not always - depending on the code), example:
            AttributeError: 'Try' object has no attribute 'value'

        https://github.com/riotkit-org/riotkit-do/issues/37
        :return:
        """

        io = IO()
        out = StringIO()

        with io.capture_descriptors(stream=out, enable_standard_out=False):
            returned_value = self._create_callable_tester(
                '''print('History isn't made by kings and politicians, it is made by us.');''', language='python')

        self.assertIn("History isn't made by kings and politicians, it is made by us.", out.getvalue())
        self.assertFalse(returned_value)
