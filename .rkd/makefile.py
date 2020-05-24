
from rkd.syntax import TaskAliasDeclaration as Task
from rkd_python import imports as PythonImports

IMPORTS = [] + PythonImports()

TASKS = [
    Task(':release', description='Release RKD to PyPI (snapshot when on master, release on tag)',
         to_execute=[
            ':py:build', ':py:publish', '--username=__token__', '--password=${PYPI_TOKEN}'
         ]),

    Task(':test', [':py:unittest'], description='Run unit tests'),
    Task(':docs', [':sh', '-c', ''' set -x
        cd docs
        sphinx-build -M html "source" "build"
    '''])
]
