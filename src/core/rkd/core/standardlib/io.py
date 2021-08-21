import os
from abc import ABC
from argparse import ArgumentParser
from tarfile import TarFile
from typing import Dict, Union, Callable, List
from zipfile import ZipFile
from gitignore_parser import parse_gitignore

from rkd.core.api.contract import ExtendableTaskInterface, ExecutionContext

ARCHIVE_TYPE_ZIP = 'zip'
ARCHIVE_TYPE_TARGZ = 'tar+gzip'


class IOBaseTask(ExtendableTaskInterface, ABC):
    _ignore: List[Callable]

    def __init__(self):
        self._ignore = [lambda x: False]

    def consider_ignore(self, path: str = '.gitignore'):
        """
        Load ignore rules from .gitignore or other file in gitignore format

        :api: configure
        :param path:
        :return:
        """

        if not os.path.isfile(path):
            raise FileNotFoundError(f'Cannot find .gitignore at path "{path}"')

        func = parse_gitignore(path)
        func.path = path

        self.io().debug(f'Loaded ignore from "{path}"')
        self._ignore.append(func)

    def consider_ignore_recursively(self, src_path: str, filename: str = '.gitignore'):
        """
        Recursively load rules from a gitignore-format file

        :param src_path:
        :param filename:
        :return:
        """

        for root, d_names, f_names in os.walk(src_path):
            if os.path.isfile(root + '/' + filename):
                self.consider_ignore(root + '/' + filename)

    def can_be_touched(self, path: str) -> bool:
        """
        Can file be touched? - Added to archive, copied, deleted etc.

        :param path:
        :return:
        """

        for callback in self._ignore:
            if callback(path):
                try:
                    # noinspection PyUnresolvedReferences
                    self.io().debug(f'can_be_touched({callback.path}) = blocked adding {path}')
                except AttributeError:
                    pass

                return False

        return True


class ArchivePackagingBaseTask(IOBaseTask):
    """
    Packages files into a compressed archive.
    -----------------------------------------

    Supports:
      - dry-run mode (do not write anything to disk, just print messages)
      - copies directories recursively
      - .gitignore files support (manually added using API method)
      - can work both as preconfigured and fully on runtime


    Example (preconfigured):

        .. code:: python

            @extends(ArchivePackagingBaseTask)
            def PackIntoZipTask():
                def configure(task: ArchivePackagingBaseTask, event: ConfigurationLifecycleEvent):
                    task.archive_path = '/tmp/test-archive.zip'
                    task.consider_gitignore('.gitignore')
                    task.add('tests/samples/', './')

                return [configure]


    Example (on runtime):

        .. code:: python

            @extends(ArchivePackagingBaseTask)
            def PackIntoZipTask():
                def configure(task: ArchivePackagingBaseTask, event: ConfigurationLifecycleEvent):
                    task.archive_path = '/tmp/test-archive.zip'

                def execute(task: ArchivePackagingBaseTask):
                    task.consider_gitignore('.gitignore')
                    task.add('tests/samples/', './')
                    task.perform()

                return [configure, execute]

    """

    sources: Dict[str, str]

    dry_run: bool                     # Skip IO operations, just print messages
    allow_archive_overwriting: bool   # Allow overwriting if destination file already exists
    archive: Union[ZipFile, TarFile]  # Direct access to archive object - TarFile or ZipFile

    archive_path: str  # Path where to save the archive
    archive_type: str  # One of supported types (see io.ARCHIVE_TYPE_ZIP and io.ARCHIVE_TYPE_TARGZ), defaults to zip

    def __init__(self):
        super().__init__()
        self.archive_type = ARCHIVE_TYPE_ZIP
        self.sources = {}
        self.dry_run = False

    def get_configuration_attributes(self) -> List[str]:
        return [
            'archive_path', 'archive_type', 'sources', 'dry_run',
            'allow_archive_overwriting', 'add', 'consider_ignore', 'consider_ignore_recursively'
        ]

    def get_name(self) -> str:
        return ':archive'

    def get_group_name(self) -> str:
        return ':dist'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--dry-run', help='Don\'t do anything, just print messages', action='store_true')
        parser.add_argument('--allow-overwrite', help='Overwrite destination file if exists', action='store_true')

    def add(self, src_path: str, target_path: str = None):
        """
        Enqueue file/directory to be added to the archive file


        :api: configure
        :param src_path:
        :param target_path: Optional - name under which the file will be added to the archive
        :return:
        """

        include_src_last_dir = not src_path.endswith('/')
        src_path = os.path.abspath(src_path)

        if os.path.isfile(src_path):
            include_src_last_dir = False
            src_dir = os.path.dirname(src_path)
            self._add(src_dir, os.path.basename(src_path), target_path, src_path, include_src_last_dir)

        for root, d_names, f_names in os.walk(src_path):
            for f in f_names:
                self._add(root, f, target_path, src_path, include_src_last_dir)

    def _add(self, root, f, target_path, src_path, include_src_last_dir):
        current_file_path = os.path.abspath(os.path.join(root, f))

        try:
            if not self.can_be_touched(current_file_path):
                self.io().info(f'Ignoring "{current_file_path}"')
                return

        except ValueError:
            # ValueError: 'X' is not in the sub-path of 'Y'
            pass

        if not target_path:
            current_file_target_path = current_file_path
        else:
            current_file_target_path = target_path

            if "." not in os.path.basename(target_path):
                current_file_target_path += '/' + current_file_path[len(src_path) + 1:]

            # fix up paths like `.//vendor/composer/installed.json`
            current_file_target_path = current_file_target_path.replace('.//', '')

            # include last directory from source path if it did not end with "/"
            if include_src_last_dir:
                current_file_target_path = os.path.basename(src_path) + '/' + current_file_target_path

        self.sources[current_file_target_path] = current_file_path
        self.io().debug(f'Adding {current_file_path} as {current_file_target_path}')

    def execute(self, context: ExecutionContext) -> bool:
        self.dry_run = bool(context.get_arg('--dry-run'))
        self.allow_archive_overwriting = bool(context.get_arg('--allow-overwrite'))

        if self.dry_run:
            self.io().warn('Dry run active, will not perform any disk operation')

        self.perform(context)

        return True

    def perform(self, context: ExecutionContext):
        # prepare
        self._make_sure_destination_directory_exists(os.path.dirname(self.archive_path))
        self.archive = self._create_archive(self.archive_path)

        for dest_path, path in self.sources.items():
            self._add_to_archive(self.archive, path, dest_path)

        self.inner_execute(context)
        self._commit_changes(self.archive)

    def _add_to_archive(self, archive: Union[ZipFile, TarFile], path: str, dest_path: str):
        self.io().info(f'Compressing "{path}" -> "{dest_path}"')

        if not self.dry_run:
            if isinstance(archive, ZipFile):
                archive.write(path, arcname=dest_path)
            elif isinstance(archive, TarFile):
                archive.add(path, arcname=dest_path)

    def _create_archive(self, path: str) -> Union[ZipFile, TarFile]:
        self.io().info(f'Creating archive "{path}"')

        if not self.allow_archive_overwriting and os.path.isfile(self.archive_path):
            raise FileExistsError(f'File "{self.archive_path}" already exists, '
                                  f'use --allow-overwrite to enforce recreation')

        temp_path = self._create_temporary_path(self.archive_path)

        if not self.dry_run:
            if self.archive_type == ARCHIVE_TYPE_ZIP:
                return ZipFile(temp_path, 'w')
            elif self.archive_type == ARCHIVE_TYPE_TARGZ:
                return TarFile.open(temp_path, 'w:gz')
            else:
                raise Exception('Unknown archive type')

    def _make_sure_destination_directory_exists(self, path: str) -> None:
        if not self.dry_run:
            self.sh(f'mkdir -p "{path}"')

    def _commit_changes(self, archive: Union[ZipFile, TarFile]):
        if not self.dry_run:
            archive.close()

            self.sh(f'mv "{self._create_temporary_path(self.archive_path)}" "{self.archive_path}"')

    @staticmethod
    def _create_temporary_path(path: str) -> str:
        return path + '.tmp'
