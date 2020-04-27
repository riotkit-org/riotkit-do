
from ..task import TaskInterface


class PyPublishTask(TaskInterface):
    def get_name(self) -> str:
        return ':publish'

    def get_group_name(self) -> str:
        return ':py'
