
"""
Test data for RKD automatic tests
=================================

For internal usage only.
"""


from typing import Dict
from argparse import ArgumentParser
from .api.syntax import TaskDeclaration
from .api.contract import TaskInterface
from .api.contract import ExecutionContext
from .standardlib import CallableTask
from .api.inputoutput import NullSystemIO


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


def ret_true() -> bool:
    return True


def ret_root() -> str:
    return 'root'


def ret_invalid_user() -> str:
    return 'invalid-user-there'

