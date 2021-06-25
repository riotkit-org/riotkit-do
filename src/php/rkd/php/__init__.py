from rkd.core.api.syntax import TaskDeclaration
from .composer import ComposerIntegrationTask


def imports():
    return [
        TaskDeclaration(ComposerIntegrationTask())
    ]
