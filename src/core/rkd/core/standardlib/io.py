import os
from argparse import ArgumentParser
from tarfile import TarFile
from typing import Dict, Union, Callable, List
from zipfile import ZipFile
from gitignore_parser import parse_gitignore

from rkd.core.api.contract import ExtendableTaskInterface, ExecutionContext

ARCHIVE_TYPE_ZIP = 'zip'
ARCHIVE_TYPE_TARGZ = 'tar+gzip'


class ArchivePackagingBaseTask(ExtendableTaskInterface):
    """
    Packages files into a compressed archive.
    -----------------------------------------

    Supports:
      - dry-run mode (do not write anything to disk, just print messages)
      - copies directories recursively
      - .gitignore files support (manually added using API method)
    """

    sources: Dict[str, str]
    _gitignore: List[Callable]

    dry_run: bool                     # Skip IO operations, just print messages
    allow_archive_overwriting: bool   # Allow overwriting if destination file already exists
    archive: Union[ZipFile, TarFile]  # Direct access to archive object - TarFile or ZipFile

    archive_path: str  # Path where to save the archive
    archive_type: str  # One of supported types (see io.ARCHIVE_TYPE_ZIP and io.ARCHIVE_TYPE_TARGZ), defaults to zip

    def __init__(self):
        self.archive_type = ARCHIVE_TYPE_ZIP
        self.sources = {}
        self._gitignore = [lambda x: True]
        self.dry_run = False

    def get_configuration_attributes(self) -> List[str]:
        return [
            'archive_path', 'archive_type', 'sources', 'dry_run',
            'allow_archive_overwriting', 'add', 'consider_gitignore'
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

        for root, d_names, f_names in os.walk(src_path):
            for f in f_names:
                current_file_path = os.path.abspath(os.path.join(root, f))

                try:
                    if not self._can_be_added(current_file_path):
                        self.io().info(f'Ignoring "{current_file_path}"')
                        continue

                except ValueError:
                    # ValueError: 'X' is not in the subpath of 'Y'
                    pass

                if not target_path:
                    current_file_target_path = current_file_path
                else:
                    current_file_target_path = target_path + '/' + current_file_path[len(src_path) + 1:]

                    # fix up paths like `.//vendor/composer/installed.json`
                    current_file_target_path = current_file_target_path.replace('.//', '')

                    # include last directory from source path if it did not end with "/"
                    if include_src_last_dir:
                        current_file_target_path = os.path.basename(src_path) + '/' + current_file_target_path

                self.sources[current_file_target_path] = current_file_path

    def consider_gitignore(self, path: str = '.gitignore'):
        """
        Load ignore rules from .gitignore

        :api: configure
        :param path:
        :return:
        """

        if not os.path.isfile(path):
            raise FileNotFoundError(f'Cannot find .gitignore at path "{path}"')

        self._gitignore.append(parse_gitignore(path))

    def execute(self, context: ExecutionContext) -> bool:
        self.dry_run = bool(context.get_arg('--dry-run'))
        self.allow_archive_overwriting = bool(context.get_arg('--allow-overwrite'))

        if self.dry_run:
            self.io().warn('Dry run active, will not perform any disk operation')

        # prepare
        self._make_sure_destination_directory_exists(os.path.dirname(self.archive_path))
        self.archive = self._create_archive(self.archive_path)

        for dest_path, path in self.sources.items():
            self._add_to_archive(self.archive, path, dest_path)

        self.inner_execute(context)
        self._commit_changes(self.archive)

        return True

    def _can_be_added(self, path: str) -> bool:
        for callback in self._gitignore:
            if not callback(path):
                return False

        return True

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
                return TarFile(temp_path, 'w:gz')

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
