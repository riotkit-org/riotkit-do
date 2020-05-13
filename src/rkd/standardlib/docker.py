
import re
from argparse import ArgumentParser
from abc import ABC
from typing import Callable
from subprocess import CalledProcessError
from ..contract import TaskInterface, ExecutionContext
from ..syntax import TaskDeclaration


class DockerBaseTask(TaskInterface, ABC):
    def calculate_images(self, image: str, latest_per_version: bool, global_latest: bool, allowed_meta_list: str):
        """ Calculate tags propagation """

        allowed_meta = allowed_meta_list.replace(' ', '').split(',')
        tag = image.split(':')[-1]

        # output
        output_tags = [image]

        matches = re.match('([0-9.]+)(-([A-Za-z]+))?([0-9]+)?', tag, re.IGNORECASE)
        meta_type = matches.group(3)

        if not matches:
            self._io.warn('No release version found')
            return output_tags

        if meta_type and meta_type not in allowed_meta:
            self.io().warn('Version meta part is not allowed, not calculating propagation')
            return output_tags

        original_tag = matches.group(0)
        base_version = matches.group(1)
        meta = meta_type
        meta_number = matches.group(4)

        # :latest
        if global_latest:
            output_tags.append(image.replace(original_tag, 'latest'))

        # case 1: 1.0.0-RC1 -> 1.0.0-latest-RC
        if meta and meta_number:
            output_tags.append(image.replace(original_tag, base_version + '-latest%s' % meta))

            if latest_per_version:
                output_tags = self._generate_for_each_version(
                    image, original_tag, output_tags,
                    lambda version: original_tag.replace(base_version + meta + meta_number, version + '-latest%s' % meta)
                )
        elif meta and not meta_number:
            output_tags.append(image.replace(original_tag, base_version + '-latest%s' % meta))

            if latest_per_version:
                output_tags = self._generate_for_each_version(
                    image, original_tag, output_tags,
                    lambda version: original_tag.replace(base_version + meta, version + '-latest%s' % meta)
                )
        # release
        elif not meta:
            output_tags = self._generate_for_each_version(
                image, original_tag, output_tags,
                lambda version: original_tag.replace(base_version, version)
            )

        return output_tags

    @staticmethod
    def _generate_for_each_version(image: str, original_tag: str, output_tags: list, callback: Callable) -> list:
        parts = original_tag.split('.')

        for part_num in range(0, len(parts)):
            version = ".".join(parts[0:part_num])

            if not version:
                continue

            output_tags.append(
                image.replace(
                    original_tag,
                    callback(version)
                )
            )

        return output_tags

    def _print_images(self, images: list, action: str):
        for image in images:
            self._io.info(' -> Going to %s image "%s"' % (action, image))

    def get_group_name(self) -> str:
        return ':docker'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--image', '-i', help='Image name', required=True)
        parser.add_argument('--without-latest', '-wl', help='Do not tag latest per version', action='store_true')
        parser.add_argument('--without-global-latest', '-wgl', help='Do not tag :latest', action='store_true')
        parser.add_argument('--propagate', '-p', help='Propagate tags? eg. 1.0.0 -> 1.0 -> 1 -> latest', action='store_true')
        parser.add_argument('--allowed-meta', '-m', help='Allowed meta part eg. rc, alpha, beta',
                            default='rc,alpha,stable,dev,prod,test,beta,build,b')


class TagImageTask(DockerBaseTask):
    """Re-tag images to propagate version tags in docker-like format eg. 1.0.1 -> 1.0 -> 1 -> latest

    Examples:
        1.0.0 -> 1.0 -> 1 -> latest
        1.0.0-RC1 -> 1.0.0-latest-rc
    """

    def get_name(self) -> str:
        return ':tag'

    def execute(self, context: ExecutionContext) -> bool:
        original_image = context.args['image']

        if context.args['propagate']:
            images = self.calculate_images(
                image=original_image,
                latest_per_version=not context.args['without_latest'],
                global_latest=not context.args['without_global_latest'],
                allowed_meta_list=context.args['allowed_meta']
            )
        else:
            images = [original_image]

        self._print_images(images, 'tag')

        for image in images:
            try:
                self.exec('docker tag %s %s' % (original_image, image))
            except CalledProcessError as e:
                print(e)
                return False

        return True


class PushTask(DockerBaseTask):
    """Pushes all re-tagged images
    """

    def get_name(self) -> str:
        return ':push'

    def execute(self, context: ExecutionContext) -> bool:
        original_image = context.args['image']
        images = []

        if context.args['propagate']:
            images += self.calculate_images(
                image=original_image,
                latest_per_version=not context.args['without_latest'],
                global_latest=not context.args['without_global_latest'],
                allowed_meta_list=context.args['allowed_meta']
            )
        else:
            images = [original_image]

        self._print_images(images, 'push')

        for image in images:
            try:
                self.exec('docker push %s' % image)
            except CalledProcessError as e:
                print(e)
                return False

        return True


def imports():
    return [
        TaskDeclaration(TagImageTask()),
        TaskDeclaration(PushTask())
    ]
