from rkd.php import ComposerIntegrationTask

from rkd.core.api.syntax import TaskDeclaration
from rkd.php.script import PhpScriptTask

IMPORTS = [
    TaskDeclaration(ComposerIntegrationTask(), name=':composer'),
    TaskDeclaration(PhpScriptTask(), name=':php')
]
