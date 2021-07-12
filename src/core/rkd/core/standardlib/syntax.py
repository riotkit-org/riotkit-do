
from typing import Dict
from typing import List
from argparse import ArgumentParser
from typing import Callable
from typing import Optional
from copy import deepcopy
from ..api.contract import TaskInterface
from ..api.contract import ExecutionContext
from ..api.contract import ArgparseArgument


class CallableTask(TaskInterface):
    """
    Executes a custom callback - allows to quickly define a short, primitive task
    """

    _callable: Callable[[ExecutionContext, TaskInterface], bool]
    _args_callable: Callable[[ArgumentParser], None]
    _argparse_options: Optional[List[ArgparseArgument]]
    _name: str
    _group: str
    _description: str
    _envs: dict
    _become: str

    def __init__(self, name: str, callback: Callable[[ExecutionContext, TaskInterface], bool],
                 args_callback: Callable[[ArgumentParser], None] = None,
                 description: str = '',
                 group: str = '',
                 become: str = '',
                 argparse_options: List[ArgparseArgument] = None):
        self._name = name
        self._callable = callback
        self._args_callable = args_callback
        self._description = description
        self._group = group
        self._envs = {}
        self._become = become
        self._argparse_options = argparse_options

    def get_name(self) -> str:
        return self._name

    def get_become_as(self) -> str:
        return self._become

    def get_description(self) -> str:
        return self._description

    def get_group_name(self) -> str:
        return self._group

    def configure_argparse(self, parser: ArgumentParser):
        if self._argparse_options:
            for opts in self._argparse_options:
                parser.add_argument(*opts.args, **opts.kwargs)

        if self._args_callable:
            self._args_callable(parser)

    def execute(self, context: ExecutionContext) -> bool:
        return self._callable(context, self)

    def push_env_variables(self, envs: dict):
        self._envs = deepcopy(envs)

    def get_declared_envs(self) -> Dict[str, str]:
        return self._envs

