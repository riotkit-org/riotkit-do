from abc import ABC

import docker
from typing import List, Dict, Optional
from docker.models.containers import Container
from docker.types import Mount
from docker.errors import ImageNotFound
from rkd.core.api.contract import ExecutionContext, AbstractExtendableTask
from rkd.core.api.lifecycle import ConfigurationLifecycleEventAware


class RunInContainerBaseTask(AbstractExtendableTask, ConfigurationLifecycleEventAware, ABC):
    """
    RunInContainerBaseTask
    ----------------------

    Allows to work inside of a temporary docker container.

    Configuration:
        mount(): Mount directories/files as volumes
        add_file_to_copy(): Copy given files to container before container starts
        user: Container username, defaults to "root"
        shell: Shell binary path, defaults to "/bin/sh"
        docker_image: Full docker image name with registry (optional), group, image name and tag
        entrypoint: Entrypoint
        command: Command to execute on entrypoint

    Runtime:
        copy_to_container(): Copy files/directory to container immediately
        in_container(): Execute inside container
    """

    docker_image: str
    user: str
    shell: str
    container: Container
    to_copy: Dict[str, str]
    mounts: List[Mount]
    entrypoint: Optional[str]
    command: Optional[str]

    def __init__(self):
        self.user = 'root'
        self.shell = '/bin/sh'
        self.docker_image = 'alpine:3.13'
        self.to_copy = {}
        self.mounts = []
        self.entrypoint = None
        self.command = None

    def get_configuration_attributes(self) -> List[str]:
        return [
            'docker_image', 'mount',
            'add_file_to_copy', 'user', 'shell'
        ]

    def get_name(self) -> str:
        return ':exec'

    def get_group_name(self) -> str:
        return ':docker'

    def execute(self, context: ExecutionContext) -> bool:
        self._run_container(context)

        try:
            result = self.inner_execute(context)

        finally:
            self._clean_up_image()

        return result

    def mount(self, local: str, remote: str, mount_type: str = 'bind', read_only: bool = False) -> None:
        self.mounts.append(Mount(target=remote, source=local, type=mount_type, read_only=read_only))

    def add_file_to_copy(self, local: str, remote: str) -> None:
        self.to_copy[remote] = local

    def in_container(self, cmd: str, workdir: Optional[str] = None, user: Optional[str] = None) -> None:
        additional_args = ''

        if workdir:
            additional_args += f' -w {workdir} '

        if user is None:
            user = self.user

        if user:
            additional_args += f' --user {user} '

        self.io().info_msg(f'   >> {cmd}')
        self.sh('docker exec {additional_args} -it {id} {shell} -c "{cmd}"'.format(
            id=self.container.id,
            shell=self.shell,
            cmd=cmd.replace('"', '\"'),
            capture=False,
            additional_args=additional_args
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

    def _run_container(self, context: ExecutionContext):
        client = docker.from_env()
        env = {}

        for env_name, definition in self.get_declared_envs().items():
            env[env_name] = context.get_env(env_name)

        container_kwargs = {
            'image': self.docker_image,
            'command': self.command,
            'entrypoint': self.entrypoint,
            'user': self.user,
            'mounts': self.mounts,
            'environment': env
        }

        self.io().debug(f'Running docker image with args: {container_kwargs}')

        try:
            self.container = client.containers.create(**container_kwargs)

        # pull image on-demand
        except ImageNotFound:
            client.images.pull(self.docker_image)
            self.container = client.containers.create(**container_kwargs)

        for remote, local in self.to_copy.items():
            self.copy_to_container(local=local, remote=remote)

        self.container.start()

    def _clean_up_image(self) -> None:
        self.container.remove(force=True)
