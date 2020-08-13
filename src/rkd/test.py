from typing import Dict
from argparse import ArgumentParser
from .api.syntax import TaskDeclaration
from .api.contract import TaskInterface
from .api.contract import ExecutionContext
from .standardlib import CallableTask
from .api.inputoutput import NullSystemIO
from .api.inputoutput import IO
from .context import ApplicationContext
from .execution.executor import OneByOneTaskExecutor
from .api.temp import TempManager


class TestTask(CallableTask):
    _description = 'Test task for automated tests'
    _become: str = False

    def __init__(self):
        self._io = NullSystemIO()

    def get_name(self) -> str:
        return ':test'

    def get_group_name(self) -> str:
        return ':rkd'

    def execute(self, context: ExecutionContext) -> bool:
        print('Hello world from :test task')
        return True

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def get_declared_envs(self) -> Dict[str, str]:
        return {
            'ORG_NAME': 'International Workers Association'
        }


class TestTaskWithRKDCallInside(TestTask):
    def execute(self, context: ExecutionContext) -> bool:
        self.rkd([':sh', '-c', '"echo \'9 Aug 2014 Michael Brown, an unarmed Black teenager, was killed by a white police officer in Ferguson, Missouri, sparking mass protests across the US.\'"'])
        return True


def get_test_declaration(task: TaskInterface = None) -> TaskDeclaration:
    if not task:
        task = TestTask()

    return TaskDeclaration(task, {}, [])


def mock_task(task: TaskInterface, io: IO = None) -> TaskInterface:
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


def mock_execution_context(task: TaskInterface, args: Dict[str, str] = None, env: Dict[str, str] = None,
                           defined_args: Dict[str, dict] = None) -> ExecutionContext:
    if args is None: args = {}
    if env is None: env = {}
    if defined_args is None: defined_args = {}

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


def ret_true() -> bool:
    return True


def ret_root() -> str:
    return 'root'


def ret_invalid_user() -> str:
    return 'invalid-user-there'

