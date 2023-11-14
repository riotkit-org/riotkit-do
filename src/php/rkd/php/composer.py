import json
import os
from argparse import ArgumentParser
from typing import List
from rkd.core.api.contract import TaskInterface, ExecutionContext, ExtendableTaskInterface
from rkd.core.api.inputoutput import IO
from rkd.core.api.syntax import TaskDeclaration
from rkd.core.execution.lifecycle import CompilationLifecycleEvent


class ComposerScriptTask(TaskInterface):
    group_name: str
    task_name: str
    composer_task_name: str

    def __init__(self, group_name: str, task_name: str, composer_task_name: str):
        self.group_name = group_name
        self.task_name = task_name
        self.composer_task_name = composer_task_name

    def get_name(self) -> str:
        return self.task_name

    def get_group_name(self) -> str:
        return self.group_name

    def get_description(self) -> str:
        return 'Composer task'

    def execute(self, context: ExecutionContext) -> bool:
        if context.get_arg('--clear'):
            self.sh('rm -rf vendor')

        if not os.path.isdir('vendor') or context.get_arg('--install'):
            install_args = ' --no-progress '

            if context.get_arg('--no-dev'):
                install_args += ' --no-dev '

            if context.get_arg('--no-scripts'):
                install_args += ' --no-scripts '

            self.sh(f'composer install {install_args}')

        self.sh('composer run {task_name} -- {args}'.format(
            task_name=self.composer_task_name,
            args=''
            # args=context.get_unknown_args()
        ))

        return True

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--no-dev', help='Disables installation of require-dev packages', action='store_true')
        parser.add_argument('--no-scripts', help='Skips the execution of all scripts defined in composer.json file',
                            action='store_true')
        parser.add_argument('--install', help='Enforce `composer install`', action='store_true')
        parser.add_argument('--clear', help='Force remove `vendor` directory first', action='store_true')


class ComposerIntegrationTask(ExtendableTaskInterface):
    """Runs tasks from composer.json"""

    def get_name(self) -> str:
        return ':composer'

    def get_group_name(self) -> str:
        return ':php'

    def configure_argparse(self, parser: ArgumentParser):
        pass

    @staticmethod
    def find_composer_tasks(io: IO) -> List[str]:
        if not os.path.isfile('composer.json'):
            io.debug('composer.json not found')
            return []

        try:
            io.debug('Trying to load composer.json')

            with open('composer.json', 'r') as f:
                data = json.loads(f.read())

            return data['scripts'].keys()

        except Exception as exc:
            # todo specific exception class
            raise Exception('Cannot load composer.json') from exc

    def compile(self, event: CompilationLifecycleEvent) -> None:
        """
        Collects all scripts from "composer.json" and adds into the RKD's context as tasks
        :param event:
        :return:
        """

        tasks: List[TaskDeclaration] = []

        for task_name in self.find_composer_tasks(event.io):
            tasks.append(
                TaskDeclaration(ComposerScriptTask(
                    group_name='',
                    task_name=event.get_current_declaration().to_full_name() + ':' + task_name,
                    composer_task_name=task_name
                ))
            )

        event.expand_into_group(tasks, pipeline=False)

    def execute(self, context: ExecutionContext) -> bool:
        for task_name in self.find_composer_tasks(self.io()):
            self.io().outln(task_name)

        return True

