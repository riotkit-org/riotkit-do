
from rkd.syntax import TaskAliasDeclaration as Task

IMPORTS = []

TASKS = [
    Task(':hello-python', [':sh', '-c', ''' set -x
        echo "Hello python!"
    '''])
]
