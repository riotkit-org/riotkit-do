
from rkd.syntax import TaskAliasDeclaration as Task
from rkd.standardlib.python import imports as PythonImports

IMPORTS = [] + PythonImports()

TASKS = [
    Task(':release', [
        ':py:build', ':py:publish', '--username=__token__', '--password=${PYPI_TOKEN}'
    ]),

    Task(':test', [':py:unittest'])
]
