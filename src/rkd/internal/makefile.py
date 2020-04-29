#
# Base RKD Makefile, contains basic commands such as :help, :clean or :version
#

from rkd.syntax import TaskDeclaration, TaskAliasDeclaration
from rkd.standardlib.pypublish import PyPublishTask
from rkd.standardlib.shell import ShellCommand
from rkd.standardlib import InitTask, TasksListingTask

IMPORTS = [
    TaskDeclaration(PyPublishTask()),
    TaskDeclaration(ShellCommand()),
    TaskDeclaration(InitTask()),
    TaskDeclaration(TasksListingTask())
]

TASKS = [
    # example:
    # TaskAliasDeclaration(':env:test', [':py:publish', '--username=...', '--password=...'], env={'DB_PASSWORD': '123'})
]
