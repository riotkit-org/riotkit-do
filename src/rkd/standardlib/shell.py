
from ..task import TaskInterface


class ShellCommand(TaskInterface):
    def get_name(self) -> str:
        return ':sh'

    def get_group_name(self) -> str:
        return ''
