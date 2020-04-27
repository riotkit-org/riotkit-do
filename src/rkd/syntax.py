
from typing import List
from .task import TaskInterface


class Component:
    _task: TaskInterface
    _env: List[str]

    def __init__(self, task: TaskInterface, env: List[str] = []):
        self._task = task
        self._env = env

    def to_full_name(self):
        return self._task.get_full_name()


class Task:
    _name: str
    _arguments: List[str]

    def __init__(self, name: str, to_execute: List[str]):
        self._name = name
        self._arguments = to_execute

    def get_name(self):
        return self._name

