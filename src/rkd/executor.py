
from typing import Union
from .syntax import TaskDeclaration, GroupDeclaration


class Executor:
    @staticmethod
    def execute(task: TaskDeclaration, parent: Union[GroupDeclaration, None] = None, args: list = []):
        print(' >> Executing ' + task.to_full_name())
        task.get_task_to_execute().execute(task.to_full_name(), {}, {})
