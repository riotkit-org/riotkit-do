#
# Base RKD Makefile, contains basic commands such as :tasks, :sh or :version
#

from rkd.core.api.syntax import TaskDeclaration
from rkd.core.standardlib.shell import ShellCommandTask, ExecProcessCommand
from rkd.core.standardlib import TasksListingTask, VersionTask, CreateStructureTask, LineInFileTask


IMPORTS = [
    TaskDeclaration(ShellCommandTask(), internal=True),
    TaskDeclaration(ExecProcessCommand(), internal=True),
    TaskDeclaration(TasksListingTask()),
    TaskDeclaration(VersionTask()),
    TaskDeclaration(CreateStructureTask()),
    TaskDeclaration(LineInFileTask(), internal=True)
]

TASKS = [
    # example:
    # TaskAliasDeclaration(':env:test', [':py:publish', '--username=...', '--password=...'], env={'DB_PASSWORD': '123'})
]
