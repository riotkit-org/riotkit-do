
from .core import CleanTask, PublishTask, BuildTask, InstallTask, UnitTestTask
from rkd.core.api.syntax import TaskDeclaration


def imports():
    return [
        TaskDeclaration(CleanTask()),
        TaskDeclaration(PublishTask()),
        TaskDeclaration(BuildTask()),
        TaskDeclaration(InstallTask()),
        TaskDeclaration(UnitTestTask())
    ]
