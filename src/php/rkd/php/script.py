import os
from argparse import ArgumentParser
from rkd.core.api.contract import ExecutionContext
from rkd.core.api.syntax import TaskDeclaration
from rkd.core.execution.lifecycle import ConfigurationLifecycleEvent
from rkd.core.standardlib.docker import RunInContainerBaseTask


class PhpScriptTask(RunInContainerBaseTask):
    """
    Execute a PHP code (using a docker container)
    """

    def get_name(self) -> str:
        return ':php'

    def get_group_name(self) -> str:
        return ''

    def configure(self, event: ConfigurationLifecycleEvent) -> None:
        self.docker_image = 'php:{version}'.format(version=event.ctx.get_arg('--php'))
        self.mount(local=os.getcwd(), remote=os.getcwd())

    def inner_execute(self, context: ExecutionContext) -> bool:
        self.in_container('ls -la /var')

        return True

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--php', help='PHP version ("php" docker image tag)', default='8.0-alpine')


def imports() -> list:
    return [
        TaskDeclaration(PhpScriptTask(), internal=True),
        TaskDeclaration(PhpScriptTask(), internal=True, name=':php2')
    ]
