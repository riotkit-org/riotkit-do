# list of tasks there is kept for compatibility, as previously "core" tasks were placed in __init__
from .core import InitTask, \
    TasksListingTask, VersionTask, \
    ShellCommandTask, LineInFileTask, \
    CreateStructureTask, imports as core_imports
from .syntax import CallableTask
from .env import imports as env_imports
from .jinja import imports as jinja_imports
from .shell import imports as shell_imports


def imports() -> list:
    return [] + core_imports() + jinja_imports() + shell_imports()
