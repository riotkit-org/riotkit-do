#!/usr/bin/env python3

import unittest
import os
from io import StringIO
from rkd.contract import ExecutionContext
from rkd.executor import OneByOneTaskExecutor
from rkd.context import ApplicationContext
from rkd.test import get_test_declaration
from rkd.test import ret_true
from rkd.temp import TempManager
from rkd.inputoutput import BufferedSystemIO
from rkd.inputoutput import IO

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class TestOneByOneExecutor(unittest.TestCase):
    def test_execute_directly_or_forked_asks_task_for_forking(self):
        """Check that decision of forking or not forking belongs to the Task"""

        temp = TempManager()
        container = ApplicationContext([], [], '')
        container.io = BufferedSystemIO()
        executor = OneByOneTaskExecutor(container)
        expectations = []

        # dependencies
        declaration = get_test_declaration()
        ctx = ExecutionContext(declaration)
        task = declaration.get_task_to_execute()

        # mock to get results instead of real action
        executor._execute_as_forked_process = lambda *args, **kwargs: expectations.append('executor::_execute_as_forked_process')
        task.execute = lambda *args, **kwargs: expectations.append('task::execute')

        with self.subTest('Will fork'):
            expectations = []
            task.should_fork = lambda: True
            executor._execute_directly_or_forked(task, temp, ctx)

            self.assertEqual(['executor::_execute_as_forked_process'], expectations)

        with self.subTest('Will not fork'):
            expectations = []
            task.should_fork = lambda: False
            executor._execute_directly_or_forked(task, temp, ctx)

            self.assertEqual(['task::execute'], expectations)

    def test_execute_as_forked_process_executes_tasks_listing_task_in_a_separate_python_process(self):
        """Simply, successful case - execute a Hello World task code in a separate process and capture output"""

        io = IO()
        string_io = StringIO()

        temp = TempManager(chdir='/tmp/')
        container = ApplicationContext([], [], '')
        container.io = BufferedSystemIO()
        executor = OneByOneTaskExecutor(container)

        declaration = get_test_declaration()
        task = declaration.get_task_to_execute()
        task._io = io
        task._io.set_log_level('debug')
        ctx = ExecutionContext(declaration)

        # mock
        task.should_fork = ret_true

        with io.capture_descriptors(stream=string_io, enable_standard_out=False):
            executor._execute_as_forked_process(task, temp, ctx)

        self.assertIn('Hello world from :test task', string_io.getvalue())

    def _mock_should_fork_true(self):
        """Method used instead of lambda"""

        return True
