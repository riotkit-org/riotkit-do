from argparse import ArgumentParser
from .syntax import TaskDeclaration
from .contract import TaskInterface, ExecutionContext


class TestTask(TaskInterface):
    def get_name(self) -> str:
        pass

    def get_group_name(self) -> str:
        pass

    def execute(self, context: ExecutionContext) -> bool:
        pass

    def configure_argparse(self, parser: ArgumentParser):
        pass


def get_test_declaration() -> TaskDeclaration:
    return TaskDeclaration(TestTask(), {}, [])
