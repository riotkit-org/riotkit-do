#!/usr/bin/env python3

import unittest
import os
from io import StringIO
from rkd.contract import ExecutionContext
from rkd.execution.executor import OneByOneTaskExecutor
from rkd.context import ApplicationContext
from rkd.test import get_test_declaration
from rkd.test import ret_true
from rkd.test import ret_invalid_user
from rkd.api.temp import TempManager
from rkd.api.inputoutput import BufferedSystemIO
from rkd.api.inputoutput import IO
from rkd.contract import TaskInterface
from rkd.test import TestTask
from rkd.test import TestTaskWithRKDCallInside

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class TestOneByOneExecutor(unittest.TestCase):
    @staticmethod
    def _prepare_test_for_forking_process(task: TaskInterface = None):
        if not task:
            task = TestTask()

        io = IO()
        string_io = StringIO()

        temp = TempManager(chdir='/tmp/')
        container = ApplicationContext([], [], '')
        container.io = BufferedSystemIO()
        executor = OneByOneTaskExecutor(container)

        declaration = get_test_declaration(task)
        task._io = io
        task._io.set_log_level('debug')
        ctx = ExecutionContext(declaration)

        return string_io, task, executor, io, ctx, temp

    def test_execute_directly_or_forked_asks_task_for_forking(self):
        """Check that decision of forking or not forking belongs to the Task"""

        string_io, task, executor, io, ctx, temp = self._prepare_test_for_forking_process()

        # mock to get results instead of real action
        executor._execute_as_forked_process = lambda *args, **kwargs: expectations.append('executor::_execute_as_forked_process')
        task.execute = lambda *args, **kwargs: expectations.append('task::execute')

        with self.subTest('Will fork'):
            expectations = []
            task.should_fork = lambda: True
            executor._execute_directly_or_forked('', task, temp, ctx)

            self.assertEqual(['executor::_execute_as_forked_process'], expectations)

        with self.subTest('Will not fork'):
            expectations = []
            task.should_fork = lambda: False
            executor._execute_directly_or_forked('', task, temp, ctx)

            self.assertEqual(['task::execute'], expectations)

    def test_execute_as_forked_process_executes_tasks_listing_task_in_a_separate_python_process(self):
        """Simply, successful case - execute a Hello World task code in a separate process and capture output"""

        string_io, task, executor, io, ctx, temp = self._prepare_test_for_forking_process()

        # mock
        task.should_fork = ret_true

        with io.capture_descriptors(stream=string_io, enable_standard_out=False):
            executor._execute_as_forked_process('', task, temp, ctx)

        self.assertIn('Hello world from :test task', string_io.getvalue())

    def test_execute_as_forked_process_will_inform_about_invalid_user(self):
        """Test that executing as forked process will abort if user does not exist in system"""

        string_io, task, executor, io, ctx, temp = self._prepare_test_for_forking_process()

        # mock
        task.get_become_as = ret_invalid_user

        with io.capture_descriptors(stream=string_io, enable_standard_out=False):
            executor._execute_as_forked_process('', task, temp, ctx)

        self.assertIn('Unknown user "invalid-user-there"', string_io.getvalue())

    def test_execute_as_forked_process_will_inform_about_unserializable_context(self):
        """Verify that tasks not serializable by pickle will be enough described with a clue,
        so the developer can know what is to correct (eg. a lambda returned as a method return)
        """

        string_io, task, executor, io, ctx, temp = self._prepare_test_for_forking_process()

        # mock: PUT NOT-SERIALIZABLE CALLABLE (LAMBDA)
        task.should_fork = lambda: True

        with io.capture_descriptors(stream=string_io, enable_standard_out=False):
            executor._execute_as_forked_process('', task, temp, ctx)

        self.assertIn('Pickle trace: ["[val type=TestTask].should_fork', string_io.getvalue())
        self.assertIn('Cannot fork, serialization failed. Hint: Tasks that are using internally' +
                      ' inner-methods and lambdas cannot be used with become/fork', string_io.getvalue())

    def test_execute_as_forked_process_will_not_break_rkd_method_inside_task_so_the_interpreter_path_will_be_properly_detected(self):
        """The forked process needs to know how to detect Python binary when using rkd()"""

        #
        # TestTaskWithRKDCallInside() contains a rkd() call inside execute(), that's what we are testing
        # it is invisible in our test. We cannot use lambda to define this in test, because lambdas are not serializable
        #
        string_io, task, executor, io, ctx, temp = self._prepare_test_for_forking_process(TestTaskWithRKDCallInside())
        task.should_fork = ret_true

        with io.capture_descriptors(stream=string_io, enable_standard_out=False):
            executor._execute_as_forked_process('', task, temp, ctx)

        self.assertIn('9 Aug 2014 Michael Brown, an unarmed Black teenager, ' +
                      'was killed by a white police officer in Ferguson, Missouri, ' +
                      'sparking mass protests across the US.',
                      string_io.getvalue())
