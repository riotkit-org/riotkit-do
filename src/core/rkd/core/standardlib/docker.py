import docker
from typing import List, Dict
from docker.models.containers import Container
from docker.types import Mount
from rkd.core.api.contract import ExecutionContext, AbstractExtendableTask
from rkd.core.api.lifecycle import ConfigurationLifecycleEventAware


class RunInContainerBaseTask(AbstractExtendableTask, ConfigurationLifecycleEventAware):
    """
    RunInContainerBaseTask
    ----------------------

    Allows to work inside of a temporary docker container.
    """

    docker_image: str
    user: str
    shell: str
    container: Container
    to_copy: Dict[str, str]
    mountpoints: List[Mount]

    def __init__(self):
        self.user = 'root'
        self.shell = '/bin/sh'
        self.docker_image = 'alpine:3.13'
        self.to_copy = {}
        self.mountpoints = []

    def get_configuration_attributes(self) -> List[str]:
        return [
            'docker_image', 'mount', 'add_file_to_copy', 'user', 'shell'
        ]

    def get_name(self) -> str:
        return ':exec'

    def get_group_name(self) -> str:
        return ':docker'

    def execute(self, context: ExecutionContext) -> bool:
        self._run_container()

        try:
            result = self.inner_execute(context)

        finally:
            self._clean_up_image()

        return result

    def mount(self, local: str, remote: str, mount_type: str = 'bind', read_only: bool = False) -> None:
        self.mountpoints.append(Mount(target=remote, source=local, type=mount_type, read_only=read_only))

    def add_file_to_copy(self, local: str, remote: str) -> None:
        self.to_copy[remote] = local

    def in_container(self, cmd: str) -> None:
        self.io().info_msg(f'   >> {cmd}')
        self.sh('docker exec {id} {shell} -c "{cmd}"'.format(
            id=self.container.id,
            shell=self.shell,
            cmd=cmd.replace('"', '\"')
        ))

    def copy_to_container(self, local: str, remote: str) -> None:
        """
        Copies a file from host to container
        Can be used on execute stage

        :api:
        :param local:
        :param remote:
        :return:
        """

        self.sh('docker cp {local} {container_id}:{remote}'.format(
            local=local, remote=remote, container_id=self.container.id
        ))

    def _run_container(self):
        client = docker.from_env()
        self.container = client.containers.create(
            image=self.docker_image,
            command='99999999',
            entrypoint='sleep',
            user=self.user,
            mounts=self.mountpoints
        )

        for remote, local in self.to_copy.items():
            self.copy_to_container(local=local, remote=remote)

        self.container.start()

    def _clean_up_image(self) -> None:
        self.container.remove(force=True)
