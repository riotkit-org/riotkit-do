from typing import List, Union

from rkd.api.syntax import TaskAliasDeclaration, TaskDeclaration

from rkd.api.contract import TaskInterface


class MakefileProjectDefiner(object):
    _projects: List[str]
    _tasks: List[Union[TaskAliasDeclaration, TaskDeclaration]]

    def load_projects(self, projects: List[str]) -> None:
        self._projects = projects

    def define_task(self, task: Union[TaskInterface, TaskAliasDeclaration, TaskDeclaration, any]) -> None:
        if isinstance(task, TaskInterface):
            self._tasks.append(TaskDeclaration(task))

        elif isinstance(task, TaskAliasDeclaration) or isinstance(task, TaskDeclaration):
            self._tasks.append(task)

        else:
            raise Exception('Unknown task type. Must be one of: TaskInterface, TaskAliasDeclaration, TaskDeclaration')
