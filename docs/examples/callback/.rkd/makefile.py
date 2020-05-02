
import os
from rkd.syntax import TaskDeclaration
from rkd.standardlib import CallableTask
from rkd.contract import ExecutionContext


def union_method(context: ExecutionContext) -> bool:
    os.system('xdg-open https://iwa-ait.org')
    return True


IMPORTS = [
    TaskDeclaration(CallableTask(':create-union', union_method))
]

TASKS = []
