import os
import re
from typing import Pattern
from argparse import ArgumentParser
from subprocess import CalledProcessError
from jinja2 import Template
from jinja2 import StrictUndefined
from jinja2.exceptions import UndefinedError
from ..contract import TaskInterface
from ..contract import ExecutionContext
from ..syntax import TaskDeclaration


class FileRendererTask(TaskInterface):
    """Renders a .j2 file using environment as input variables"""

    def get_name(self) -> str:
        return ':render'

    def get_group_name(self) -> str:
        return ':j2'

    def execute(self, context: ExecutionContext) -> bool:
        source = context.get_arg('--source')
        output = context.get_arg('--output')

        if not os.path.isfile(source):
            self.io().error_msg('Source file does not exist at path "%s"' % source)
            return False

        if output != '-' and not os.path.isdir(os.path.dirname(output)):
            self.sh('mkdir -p %s' % os.path.dirname(output))

        with open(source, 'rb') as f:
            tpl = Template(f.read().decode('utf-8'), undefined=StrictUndefined)

            try:
                rendered = tpl.render(**context.env)
            except UndefinedError as e:
                self.io().error_msg('Undefined variable - ' + str(e))
                return False

            if output == "-":
                self.io().outln(rendered)
            else:
                with open(output, 'wb') as t:
                    t.write(rendered.encode('utf-8'))

            return True

    def configure_argparse(self, parser: ArgumentParser):
        parser.description = 'Renders a JINJA2 file. Environment variables are accessible in templates.'
        parser.add_argument('--source', '-s', help='Template file', required=True)
        parser.add_argument('--output', '-o', help='Output to file, set "-" for stdout', default='-')


class RenderDirectoryTask(TaskInterface):
    """Renders *.j2 files recursively in a directory to other directory"""

    def get_name(self) -> str:
        return ':directory-to-directory'

    def get_group_name(self) -> str:
        return ':j2'

    def execute(self, context: ExecutionContext) -> bool:
        source_root = context.get_arg('--source')
        target_root = context.get_arg('--target')
        delete_source_files = context.get_arg('--delete-source-files')
        pattern = re.compile(context.get_arg('--pattern'))

        self.io().info_msg('Pattern is `%s`' % context.get_arg('--pattern'))

        for root, subdirs, files in os.walk(source_root):
            for file in files:
                source_full_path = root + '/' + file
                target_full_path = target_root + '/' + source_full_path[len(source_root):]

                if not self._is_file_matching_filter(pattern, source_full_path):
                    self.io().info_msg('Skipping file "%s" (filtered out)' % source_full_path)
                    continue

                self.io().info_msg('Rendering file "%s" into "%s"' % (source_full_path, target_full_path))

                if not self._render(source_full_path, target_full_path):
                    # stderr will be passed through
                    return False

                if delete_source_files:
                    self._delete_file(source_full_path)

        return True

    def _render(self, source_path: str, target_path: str) -> bool:
        try:
            self.rkd([':j2:render', '--source="%s"' % source_path, '--output="%s"' % target_path], verbose=True)
            return True

        except CalledProcessError:
            return False

    @staticmethod
    def _delete_file(full_path: str):
        os.unlink(full_path)

    @staticmethod
    def _is_file_matching_filter(pattern: Pattern, full_path: str):
        return pattern.match(full_path) is not None

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--source', '-s', help='Source path where templates are stored', required=True)
        parser.add_argument('--target', '-t', help='Target path where templates should be rendered', required=True)
        parser.add_argument('--delete-source-files', '-d', help='Delete source files after rendering?', default=False,
                            action='store_true')
        parser.add_argument('--pattern', '-p', help='Optional regexp pattern to match full paths',
                            default='(.*).j2')


def imports():
    return [
        TaskDeclaration(FileRendererTask()),
        TaskDeclaration(RenderDirectoryTask())
    ]
