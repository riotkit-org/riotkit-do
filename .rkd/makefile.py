
from rkd.syntax import TaskDeclaration, TaskAliasDeclaration
from rkd.standardlib.python import imports as PythonImports

IMPORTS = [] + PythonImports()

TASKS = [
    TaskAliasDeclaration(':env:test', [':py:publish', '--username=...', '--password=...'])
]
