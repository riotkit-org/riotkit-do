
"""
Test data for RKD automatic tests
=================================

For internal usage only.
"""


from typing import Dict, Union
from argparse import ArgumentParser
from .api.syntax import TaskDeclaration
from .api.contract import TaskInterface, ArgumentEnv
from .api.contract import ExecutionContext
from .standardlib import CallableTask
from .api.inputoutput import NullSystemIO


TEST_CONSTANT = 'this is an example constant'


class TaskForTesting(CallableTask):
    _description = 'Test task for automated tests'
    _become: str = False
    _internal: bool

    def __init__(self, internal: bool = False):
        self._io = NullSystemIO()
        self._internal = internal
        super().__init__(':test', None)

    def get_name(self) -> str:
        return ':test'

    def get_group_name(self) -> str:
        return ':rkd'

    def execute(self, context: ExecutionContext) -> bool:
        print('Hello world from :test task')
        return True

    def configure_argparse(self, parser: ArgumentParser):
        pass

    @classmethod
    def get_declared_envs(cls) -> Dict[str, Union[str, ArgumentEnv]]:
        return {
            'ORG_NAME': 'International Workers Association'
        }

    @property
    def is_internal(self) -> bool:
        return self._internal


class TaskForTestingWithRKDCallInside(TaskForTesting):
    def execute(self, context: ExecutionContext) -> bool:
        self.rkd([':sh', '-c', '"echo \'9 Aug 2014 Michael Brown, an unarmed Black teenager, was killed by a white police officer in Ferguson, Missouri, sparking mass protests across the US.\'"'])
        return True


def get_test_declaration(task: TaskInterface = None, internal: bool = False) -> TaskDeclaration:
    if not task:
        task = TaskForTesting(internal=internal)

    return TaskDeclaration(task, {}, [])


def ret_true() -> bool:
    return True


def ret_root() -> str:
    return 'root'


def ret_invalid_user() -> str:
    return 'invalid-user-there'

