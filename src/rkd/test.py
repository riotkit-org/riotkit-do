from typing import Dict
from argparse import ArgumentParser
from .syntax import TaskDeclaration
from .contract import TaskInterface
from .contract import ExecutionContext
from .standardlib import CallableTask
from .inputoutput import NullSystemIO


class TestTask(CallableTask):
    def __init__(self):
        self._io = NullSystemIO()

    def get_name(self) -> str:
        return ':test'

    def get_group_name(self) -> str:
        return ':rkd'

    def execute(self, context: ExecutionContext) -> bool:
        return True

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def get_declared_envs(self) -> Dict[str, str]:
        return {
            'Union': 'International Workers Association'
        }


def get_test_declaration() -> TaskDeclaration:
    return TaskDeclaration(TestTask(), {}, [])
