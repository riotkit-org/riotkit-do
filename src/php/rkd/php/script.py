import os
import subprocess
import tempfile
from argparse import ArgumentParser
from copy import copy
from typing import Dict, Union, Optional, List

from rkd.core.api.inputoutput import ReadableStreamType
from rkd.core.api.contract import ExecutionContext, ArgumentEnv, MultiStepLanguageExtensionInterface
from rkd.core.api.syntax import TaskDeclaration
from rkd.core.execution.lifecycle import ConfigurationLifecycleEvent
from rkd.core.standardlib.docker import RunInContainerBaseTask


class PhpScriptTask(RunInContainerBaseTask):
    """
    # <sphinx:extending-tasks>
    Execute a PHP code (using a docker container)
    Can be extended - this is a base task.

    Inherits settings from `RunInContainerBaseTask`.

    **Configuration:**

        - script: Path to script to load instead of stdin (could be a relative path)
        - version: PHP version. Leave None to use default 8.0-alpine version

    **Example of usage:**

        .. code:: yaml

            version: org.riotkit.rkd/yaml/v2
            imports:
                - rkd.php.script.PhpScriptTask
            tasks:
                :yaml:test:php:
                    extends: rkd.php.script.PhpScriptTask
                    configure@before_parent: |
                        self.version = '7.2-alpine'
                    inner_execute@after_parent: |
                        self.in_container('php --version')
                        print('IM AFTER PARENT. At first the PHP code from "input" will be executed.')
                        return True
                    input: |
                        var_dump(getcwd());
                        var_dump(phpversion());

    **Example of usage with MultiStepLanguageAgnosticTask:**

        .. code:: yaml

            version: org.riotkit.rkd/yaml/v1
            tasks:
                :exec:
                    environment:
                        PHP: '7.4'
                        IMAGE: 'php'
                    steps: |
                        #!rkd.php.script.PhpLanguage
                        phpinfo();

    # </sphinx:extending-tasks>
    """

    script: Optional[str]
    version: Optional[str]
    name: Optional[str]
    input: Optional[callable]

    def __init__(self):
        super().__init__()
        self.user = 'www-data'
        self.entrypoint = 'sleep'
        self.command = '9999999'
        self.script = None
        self.version = None
        self.name = None
        self.input = None

    def get_name(self) -> str:
        return ':php' if not self.name else self.name

    def get_group_name(self) -> str:
        return ''

    @classmethod
    def get_declared_envs(cls) -> Dict[str, Union[str, ArgumentEnv]]:
        return {
            'PHP': ArgumentEnv('PHP', '--php', '8.0-alpine'),
            'IMAGE': ArgumentEnv('IMAGE', '--image', 'php')
        }

    def configure(self, event: ConfigurationLifecycleEvent) -> None:
        super().configure(event)

        self.docker_image = '{image}:{version}'.format(
            image=event.ctx.get_arg_or_env('--image'),
            version=self.version if self.version else event.ctx.get_arg_or_env('--php')
        )

        # todo: Check - is workdir already set there? (subprojects, custom workdir etc.)
        self.mount(local=os.getcwd(), remote=os.getcwd())

    def inner_execute(self, context: ExecutionContext) -> bool:
        """
        Execute a code when the container is up and running
        :param context:
        :return:
        """

        try:
            # takes a RKD task input as input file, stdin is interactive
            if not self.script and self.get_input(context):
                input_php_code = self.get_input(context).read()

                if "<?php" not in input_php_code:
                    input_php_code = "<?php\n" + input_php_code

                with tempfile.NamedTemporaryFile() as tmp_file:
                    tmp_file.write(input_php_code.encode('utf-8'))
                    tmp_file.flush()

                    self.copy_to_container(local=tmp_file.name, remote='/tmp/script.php')      # copy file
                    self.in_container('chown www-data:www-data /tmp/script.php', user='root')  # fix permissions

                self.in_container('php /tmp/script.php', workdir=os.getcwd(), user=self.user)
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

    def get_input(self, ctx: ExecutionContext):
        if self.input:
            return self.input

        return ctx.get_input()


class PhpLanguage(PhpScriptTask, MultiStepLanguageExtensionInterface):
    """
    Language extension for MultiStepLanguageAgnosticTask

    .. code:: yaml

        version: org.riotkit.rkd/yaml/v1
        tasks:
            :exec:
                environment:
                    PHP: '7.4'
                    IMAGE: 'php'
                steps: |
                    #!rkd.php.script.PhpLanguage
                    phpinfo();

    """

    def with_predefined_details(self, code: str, name: str, step_num: int) -> 'PhpScriptTask':
        clone = copy(self)
        clone.name = name
        clone.input = ReadableStreamType(code)

        return clone


def imports() -> List[TaskDeclaration]:
    return [
        TaskDeclaration(PhpScriptTask(), internal=True)
    ]
