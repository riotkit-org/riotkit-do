#
# Base RKD Makefile, contains basic commands such as :help, :clean or :version
#

from rkd.syntax import Task, TaskAlias
from rkd.standardlib.pypublish import PyPublishTask
from rkd.standardlib.shell import ShellCommand

IMPORTS = [
    Task(PyPublishTask()),
    Task(ShellCommand())
]

TASKS = [
    TaskAlias(':env:test', [':py:publish', '--username=...', '--password=...'], env={'DB_PASSWORD': '123'})
]
