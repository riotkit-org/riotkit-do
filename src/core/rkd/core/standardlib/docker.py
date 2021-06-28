from argparse import ArgumentParser
from typing import List

from rkd.core.api.contract import TaskInterface, ExecutionContext
from rkd.core.api.lifecycle import ConfigurationLifecycleEventAware
from rkd.core.api.syntax import TaskDeclaration
from rkd.core.execution.lifecycle import ConfigurationLifecycleEvent


class RunInContainerTask(TaskInterface, ConfigurationLifecycleEventAware):
    """
    Runs a command inside a container
    """

    docker_image: str

    def get_configuration_attributes(self) -> List[str]:
        return [
            'docker_image'
        ]

    def configure(self, event: ConfigurationLifecycleEvent) -> None:
        self.docker_image = 'test'

        print('!!!', self.docker_image)
        print('???', self)

        print(self.get_name())

    def get_name(self) -> str:
        return ':exec'

    def get_group_name(self) -> str:
        return ':docker'

    def execute(self, context: ExecutionContext) -> bool:
        return True

    def configure_argparse(self, parser: ArgumentParser):
        pass


def imports() -> list:
    return [
        TaskDeclaration(RunInContainerTask(), internal=True)
    ]
