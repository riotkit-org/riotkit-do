from rkd.php import ComposerIntegrationTask

from rkd.core.api.syntax import TaskDeclaration

IMPORTS = [
    TaskDeclaration(ComposerIntegrationTask(), name=':php')
]
