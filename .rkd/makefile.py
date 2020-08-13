import os
from rkd.api.syntax import TaskAliasDeclaration as Task  # RKD API (for defining shortcuts/aliases for whole tasks lists)
from rkd.api.syntax import TaskDeclaration               # RKD API (for declaring usage of given task, importing it)
from rkd.api.contract import ExecutionContext            # RKD API (one of dependencies - context gives us access to commandline arguments and environment variables)
from rkd_python import imports as PythonImports          # group of imports (not all packages supports it, but most of them)
from rkd.standardlib.jinja import FileRendererTask       # single task
from rkd.standardlib import CallableTask                 # Basic Python callable task for a little bit advanced usage
# from .mypackage import MyTask                          # import your task from local package


def example_method(ctx: ExecutionContext, task: CallableTask) -> bool:
    os.system('xdg-open https://twitter.com/wrkclasshistory')
    return True


IMPORTS = [
    # We declare that we will use this task.
    # Declaration can take some additional arguments like args= or env=, to always append environment and/or commandline switches
    # regardless of if user used it
    TaskDeclaration(FileRendererTask()),
    # remember about the "," between tasks, it's an array/list ;)
    # TaskDeclaration(MyTask())

    TaskDeclaration(CallableTask(':read-real-history', example_method, description='Example task with simple Python code'))
]

IMPORTS += PythonImports()

TASKS = [
    # declared task-aliases. A Task Alias is a shortcut eg. ":release" that will expands to ":py:build :py:publish --username= (...)"
    # the best feature in task-aliases is that you can append and overwrite last commandline arguments, those will be added
    # at the end of the command
    Task(':release', description='Release to PyPI (snapshot when on master, release on tag)',
         to_execute=[
            ':py:build', ':py:publish', '--username=__token__', '--password=${PYPI_TOKEN}'
         ]),

    Task(':test', [':py:unittest'], description='Run unit tests'),
    Task(':docs', [':sh', '-c', ''' set -x
        cd docs
        rm -rf build
        sphinx-build -M html "source" "build"
    '''])
]
