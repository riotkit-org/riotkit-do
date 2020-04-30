
from rkd.syntax import TaskDeclaration, TaskAliasDeclaration
from rkd.standardlib.python import imports as PythonImports

IMPORTS = [] + PythonImports()

TASKS = [
    TaskAliasDeclaration(':release', [
        ':py:build', ':py:publish', '--username=__token__', '--password=${PYPI_TOKEN}'
    ])
]
