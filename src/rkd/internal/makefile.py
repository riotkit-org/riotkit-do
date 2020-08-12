#
# Base RKD Makefile, contains basic commands such as :tasks, :clean or :version
#

from rkd.api.syntax import TaskDeclaration
from rkd.standardlib.shell import ShellCommandTask, ExecProcessCommand
from rkd.standardlib import InitTask, TasksListingTask, VersionTask, CreateStructureTask, LineInFileTask


IMPORTS = [
    TaskDeclaration(ShellCommandTask()),
    TaskDeclaration(ExecProcessCommand()),
    TaskDeclaration(InitTask()),
    TaskDeclaration(TasksListingTask()),
    TaskDeclaration(VersionTask()),
    TaskDeclaration(CreateStructureTask()),
    TaskDeclaration(LineInFileTask())
]

TASKS = [
    # example:
    # TaskAliasDeclaration(':env:test', [':py:publish', '--username=...', '--password=...'], env={'DB_PASSWORD': '123'})
]
