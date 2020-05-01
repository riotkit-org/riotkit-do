#
# Base RKD Makefile, contains basic commands such as :tasks, :clean or :version
#

from rkd.syntax import TaskDeclaration, TaskAliasDeclaration
from rkd.standardlib.python import PublishTask, BuildTask
from rkd.standardlib.shell import ShellCommand, ExecProcessCommand
from rkd.standardlib import InitTask, TasksListingTask, CallableTask


IMPORTS = [
    TaskDeclaration(ShellCommand()),
    TaskDeclaration(ExecProcessCommand()),
    TaskDeclaration(InitTask()),
    TaskDeclaration(TasksListingTask()),

    TaskDeclaration(PublishTask()),
    TaskDeclaration(BuildTask())
]

TASKS = [
    # example:
    # TaskAliasDeclaration(':env:test', [':py:publish', '--username=...', '--password=...'], env={'DB_PASSWORD': '123'})
]
