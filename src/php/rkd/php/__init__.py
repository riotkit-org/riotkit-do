from rkd.core.api.syntax import TaskDeclaration
from .composer import ComposerIntegrationTask
from .script import PhpScriptTask, imports as script_imports


def imports():
    return [
        TaskDeclaration(ComposerIntegrationTask())
    ] + script_imports()
