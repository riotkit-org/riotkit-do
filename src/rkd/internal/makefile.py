#
# Base RKD Makefile, contains basic commands such as :help, :clean or :version
#

from rkd.syntax import Component, Task
from rkd.standardlib.pypublish import PyPublishTask
from rkd.standardlib.shell import ShellCommand

COMPONENTS = [
    Component(PyPublishTask()),
    Component(ShellCommand())
]

TASKS = [
    Task(':env:test', [':py:publish', '--username=...', '--password=...'])
]
