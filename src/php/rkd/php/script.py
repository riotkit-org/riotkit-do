import os
import subprocess
import tempfile
from argparse import ArgumentParser
from typing import Dict, Union, Optional

from rkd.core.api.contract import ExecutionContext, ArgumentEnv
from rkd.core.api.syntax import TaskDeclaration
from rkd.core.execution.lifecycle import ConfigurationLifecycleEvent
from rkd.core.standardlib.docker import RunInContainerBaseTask


class PhpScriptTask(RunInContainerBaseTask):
    """
    Execute a PHP code (using a docker container)
    Can be extended - this is a base task.

    Inherits settings from `RunInContainerBaseTask`.

    Configuration:
        script: Path to script to load instead of stdin (could be a relative path)

    """

    script: Optional[str]

    def __init__(self):
        super().__init__()
        self.user = 'www-data'
        self.entrypoint = 'sleep'
        self.command = '9999999'
        self.script = None

    def get_name(self) -> str:
        return ':php'

    def get_group_name(self) -> str:
        return ''

    def get_declared_envs(self) -> Dict[str, Union[str, ArgumentEnv]]:
        return {
            'PHP': ArgumentEnv('PHP', '--php', '8.0-alpine'),
            'IMAGE': ArgumentEnv('IMAGE', '--image', 'php')
        }

    def configure(self, event: ConfigurationLifecycleEvent) -> None:
        super().configure(event)

        self.docker_image = '{image}:{version}'.format(
            image=event.ctx.get_arg_or_env('--image'),
            version=event.ctx.get_arg_or_env('--php')
        )
        self.mount(local=os.getcwd(), remote=os.getcwd())

    def inner_execute(self, context: ExecutionContext) -> bool:
        """
        Execute a code when the container is up and running
        :param context:
        :return:
        """

        try:
            # takes a RKD task input as input file, stdin is interactive
            if not self.script and context.get_input():
                with tempfile.NamedTemporaryFile() as tmp_file:
                    tmp_file.write(context.get_input().read().encode('utf-8'))
                    tmp_file.flush()

                    self.copy_to_container(local=tmp_file.name, remote='/tmp/script.php')
                    self.in_container('chown www-data:www-data /tmp/script.php', user='root')

                self.in_container('php /tmp/script.php')
                return True

            # takes stdin as input
            self.in_container(f'php {self.script}')

        except subprocess.CalledProcessError:
            self.io().error('PHP process exited with non-zero exit code')
            return False

        return True

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--php', help='PHP version ("php" docker image tag)', default='8.0-alpine')
        parser.add_argument('--image', help='Docker image name', default='php')


def imports() -> list:
    return [
        TaskDeclaration(PhpScriptTask(), internal=True)
    ]
