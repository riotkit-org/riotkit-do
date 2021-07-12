from rkd.core.execution.lifecycle import ConfigurationLifecycleEvent
from rkd.php import ComposerIntegrationTask, PhpScriptTask
from rkd.core.api.syntax import TaskDeclaration, ExtendedTaskDeclaration
from rkd.core.api.decorators import no_parent_call, extends, call_parent_first


@extends(PhpScriptTask)
def PhpInfoTask():
    """
    Returns information about used PHP version

    ---
    environment:
        SOME: "thing"
    """

    def stdin():
        return '''
<?php
phpinfo();
        '''

    # @no_parent_call
    # @call_parent_first
    def configure(task: PhpScriptTask, event: ConfigurationLifecycleEvent):
        task.version = '8.0-alpine'

    return [stdin, configure]


# def CopyDocsTask(extends: FileOperationsBaseTask):
#     """
#     Copies documentation
#     """
#
#     def execute(task: FileOperationsBaseTask):
#         task.copy_from('composer.json').into('/tmp')
#
#     return [execute]
#
#
# def PackDistributionTask(extends: PHPDistributionBaseTask):
#     """
#     Packs built files
#     """
#
#     def configure(task: FileOperationsBaseTask):
#         task.enable_gitignore()
#         task.enable_self_installer()
#         task.add_path('./')
#
#     return [configure]


IMPORTS = [
    TaskDeclaration(ComposerIntegrationTask(), name=':composer'),
    TaskDeclaration(PhpScriptTask(), name=':php'),
    ExtendedTaskDeclaration(name=':phpinfo', task=PhpInfoTask),
    # ExtendedTaskDeclaration(name=':docs:copy', task=CopyDocsTask),
    # ExtendedTaskDeclaration(name=':dist:build', task=PackDistributionTask)
]

PIPELINES = [
    # :docs:copy :dist:build
]
