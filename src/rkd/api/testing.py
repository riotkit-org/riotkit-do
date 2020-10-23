
"""
Testing (part of API)
=====================

Provides tools for easier testing of RKD-based workflows, tasks, plugins.

"""

import os
import sys
from typing import Tuple, Dict
from unittest import TestCase
from io import StringIO
from copy import deepcopy
from contextlib import contextmanager
from rkd import RiotKitDoApplication, ApplicationContext
from rkd.execution.executor import OneByOneTaskExecutor
from rkd.api.contract import ExecutionContext
from rkd.api.contract import TaskInterface
from rkd.api.syntax import TaskDeclaration
from rkd.api.temp import TempManager
from rkd.api.inputoutput import IO
from rkd.api.inputoutput import NullSystemIO
from rkd.api.inputoutput import BufferedSystemIO


class OutputCapturingSafeTestCase(TestCase):
    """
    Output capturing safe test case
    ===============================

    Provides hooks for keeping stdout/stderr immutable between tests.
    """

    _stdout = None
    _stderr = None

    def setUp(self) -> None:
        os.environ['RKD_DEPTH'] = '0'
        self._stdout = sys.stdout
        self._stderr = sys.stderr

        super().setUp()

    def tearDown(self) -> None:
        self._restore_standard_out()

        super().tearDown()

    def _restore_standard_out(self):
        if not self._stderr or not self._stderr:
            return

        if sys.stderr != self._stderr or sys.stdout != self._stdout:
            print('!!! Test ' + self.id() + ' is not cleaning up stdout/stderr')

        sys.stdout = self._stdout
        sys.stderr = self._stderr


class BasicTestingCase(TestCase):
    """
    Basic test case
    ===============

    Provides minimum of:
      - Doing backup of environment and cwd
      - Methods for mocking task dependencies (RKD-specific like ExecutionContext)

    """

    _envs = None
    _cwd = None

    def setUp(self) -> None:
        self._envs = deepcopy(os.environ)
        self._cwd = os.getcwd()

        super().setUp()

    def tearDown(self) -> None:
        os.environ = self._envs
        os.chdir(self._cwd)

        super().tearDown()

    @contextmanager
    def environment(self, environ: dict):
        """
        Mocks environment

        Example usage:
            with self.environment({'RKD_PATH': SCRIPT_DIR_PATH + '/../docs/examples/env-in-yaml/.rkd'}):
                ...

        :param environ:
        :return:
        """

        backup = deepcopy(os.environ)

        try:
            os.environ.update(environ)
            yield
        finally:
            os.environ = backup

    @staticmethod
    def satisfy_task_dependencies(task: TaskInterface, io: IO = None) -> TaskInterface:
        """
        Inserts required dependencies to your task that implements rkd.api.contract.TaskInterface

        :param task:
        :param io:
        :return:
        """

        if io is None:
            io = NullSystemIO()

        ctx = ApplicationContext([], [], '')
        ctx.io = io

        task.internal_inject_dependencies(
            io=io,
            ctx=ctx,
            executor=OneByOneTaskExecutor(ctx),
            temp_manager=TempManager()
        )

        return task

    @staticmethod
    def mock_execution_context(task: TaskInterface, args: Dict[str, str] = None, env: Dict[str, str] = None,
                               defined_args: Dict[str, dict] = None) -> ExecutionContext:

        """
        Prepares a simplified rkd.api.contract.ExecutionContext instance

        :param task:
        :param args:
        :param env:
        :param defined_args:
        :return:
        """

        if args is None:
            args = {}

        if env is None:
            env = {}

        if defined_args is None:
            defined_args = {}

        if args and not defined_args:
            for name, passed_value in args.items():
                defined_args[name] = {'default': ''}

        return ExecutionContext(
            TaskDeclaration(task),
            parent=None,
            args=args,
            env=env,
            defined_args=defined_args
        )


class FunctionalTestingCase(BasicTestingCase, OutputCapturingSafeTestCase):
    """
        Functional testing case
        =======================

        Provides methods for running RKD task or multiple tasks with output and exit code capturing.
        Inherits OutputCapturingSafeTestCase.
    """

    def run_and_capture_output(self, argv: list, verbose: bool = False) -> Tuple[str, int]:
        """
        Run task(s) and capture output + exit code.
        Whole RKD from scratch will be bootstrapped there.

        Example usage:
            full_output, exit_code = self.run_and_capture_output([':tasks'])

        :param list argv: List of tasks, arguments, commandline switches
        :param bool verbose: Print all output also to stdout

        :return:
        """

        io = IO()
        out = StringIO()
        exit_code = 0

        try:
            with io.capture_descriptors(stream=out, enable_standard_out=verbose):
                app = RiotKitDoApplication()
                app.main(['test_functional.py'] + argv)

        except SystemExit as e:
            self._restore_standard_out()
            exit_code = e.code

        return out.getvalue(), exit_code

    def execute_mocked_task_and_get_output(self, task: TaskInterface, args=None, env=None) -> str:
        """
        Run a single task, capturing it's output in a simplified way.
        There is no whole RKD bootstrapped in this operation.

        :param TaskInterface task:
        :param dict args:
        :param dict env:
        :return:
        """

        if args is None:
            args = {}

        if env is None:
            env = {}

        ctx = ApplicationContext([], [], '')
        ctx.io = BufferedSystemIO()

        task.internal_inject_dependencies(
            io=ctx.io,
            ctx=ctx,
            executor=OneByOneTaskExecutor(ctx=ctx),
            temp_manager=TempManager()
        )

        merged_env = deepcopy(os.environ)
        merged_env.update(env)

        r_io = IO()
        str_io = StringIO()

        defined_args = {}

        for arg, arg_value in args.items():
            defined_args[arg] = {'default': ''}

        with r_io.capture_descriptors(enable_standard_out=True, stream=str_io):
            try:
                result = task.execute(ExecutionContext(
                    TaskDeclaration(task),
                    args=args,
                    env=merged_env,
                    defined_args=defined_args
                ))
            except Exception:
                self._restore_standard_out()
                print(ctx.io.get_value() + "\n" + str_io.getvalue())
                raise

        return ctx.io.get_value() + "\n" + str_io.getvalue() + "\nTASK_EXIT_RESULT=" + str(result)
