from rkd.core.api.contract import ExecutionContext
from rkd.core.execution.lifecycle import ConfigurationLifecycleEvent, CompilationLifecycleEvent
from rkd.core.standardlib import ShellCommandTask
from rkd.core.standardlib.io import ArchivePackagingBaseTask
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


@extends(ArchivePackagingBaseTask)
def PackIntoZipTask():
    """
    Packs application into a ZIP file

    :return:
    """

    def configure(task: ArchivePackagingBaseTask, event: ConfigurationLifecycleEvent):
        task.archive_path = '/tmp/test-archive.zip'
        task.consider_gitignore('/home/krzysiek/Projekty/riotkit/riotkit/rkd/.gitignore')
        task.add('/home/krzysiek/Projekty/riotkit/riotkit/rkd/src/php/tests/samples/', './')

    return [configure]


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


# =================
# compile() example
# =================
# Compilation takes place very early - even before task is picked into current execution context
# so it is a good place to configure task settings that affects eg. arguments parsing (as it is done on early stage)
#
@extends(ShellCommandTask)
def ListWorkspaceFiles():
    def compile(task: ShellCommandTask, event: CompilationLifecycleEvent):
        task.is_cmd_required = False

    def stdin():
        return '''ls -la'''

    def execute(task: ShellCommandTask, ctx: ExecutionContext):
        out = task.sh('ps aux', capture=True)
        task.io().info(f'Test length: {len(out)}')

    return [stdin, compile, execute]


IMPORTS = [
    TaskDeclaration(ComposerIntegrationTask(), name=':composer'),
    TaskDeclaration(PhpScriptTask(), name=':php'),
    # ExtendedTaskDeclaration(name=':phpinfo', task=PhpInfoTask),
    ExtendedTaskDeclaration(name=':workspace:ls', task=ListWorkspaceFiles),
    ExtendedTaskDeclaration(name=':dist:zip', task=PackIntoZipTask),
    # ExtendedTaskDeclaration(name=':docs:copy', task=CopyDocsTask),
    # ExtendedTaskDeclaration(name=':dist:build', task=PackDistributionTask)
]

PIPELINES = [
    # :docs:copy :dist:build
]
