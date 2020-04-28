
from typing import List, Dict
from .task import TaskInterface

# @todo: Zmienić nazwę Component -> Task, Task -> TaskAlias i dodać sam Component jako grupę tasków


class Task:
    _task: TaskInterface
    _env: Dict[str, str]
    _args: List[str]

    def __init__(self, task: TaskInterface, env: Dict[str, str] = [], args: List[str] = []):
        self._task = task
        self._env = env
        self._args = args

    def to_full_name(self):
        return self._task.get_full_name()

    def set_env(self, envs: Dict[str, str]):
        self._env = envs

    def set_args(self, args: List[str]):
        self._args = args

    def get_task_to_execute(self) -> TaskInterface:
        return self._task


class TaskAlias:
    _name: str
    _arguments: List[str]
    _env: Dict[str, str]

    def __init__(self, name: str, to_execute: List[str], env: Dict[str, str] = []):
        self._name = name
        self._arguments = to_execute
        self._env = env

    def get_name(self):
        return self._name

    def get_arguments(self) -> List[str]:
        return self._arguments

    def get_env(self) -> Dict[str, str]:
        return self._env
