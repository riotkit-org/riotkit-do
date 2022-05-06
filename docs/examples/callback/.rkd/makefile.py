
import os
from rkd.core.api.syntax import TaskDeclaration
from rkd.api.contract import ExecutionContext
from rkd.core.standardlib import CallableTask


def union_method(context: ExecutionContext) -> bool:
    os.system('xdg-open https://iwa-ait.org')
    return True


IMPORTS = [
    TaskDeclaration(CallableTask(':create-union', union_method))
]

TASKS = []
