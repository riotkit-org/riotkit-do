import os
import re
from copy import copy
from typing import Pattern, Union
from argparse import ArgumentParser
from subprocess import CalledProcessError
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import StrictUndefined
from jinja2.exceptions import UndefinedError

from ..api.contract import TaskInterface, ExtendableTaskInterface, MultiStepLanguageExtensionInterface
from ..api.contract import ExecutionContext
from ..api.syntax import TaskDeclaration


class FileRendererTask(ExtendableTaskInterface):
    """
    Renders a .j2 file using environment as input variables

    **API**

    To be used inside "execute":

        - render(): Allows to render a JINJA template (from a string)
        - render_to_file(): Renders a template to a file

    **Example of API usage in YAML (if want to inherit the task):**

    .. code:: yaml

        execute: |
            with open('some-file.j2', 'r') as f:
                task.render_to_file(f.read(), ctx, 'output.html')

    **Usage**

        .. code:: bash

            ./rkdw :j2:render --source=src.j2 --output=dst.html
    """

    def get_name(self) -> str:
        return ':render'

    def get_group_name(self) -> str:
        return ':j2'

    def _validate_source(self, source: str) -> bool:
        """
        Validate if source exists, is readable etc.

        :param source:
        :return:
        """

        if not os.path.isfile(source):
            self.io().error_msg('Source file does not exist at path "%s"' % source)
            return False

        return True

    def _read_content(self, source: str, context: ExecutionContext) -> str:
        with open(source, 'r') as f:
            return f.read()

    def _prepare_target_dir_for_path(self, output: str):
        if output != '-' and "/" in output and not os.path.isdir(os.path.dirname(output)):
            self.sh(f'mkdir -p {os.path.dirname(output)}')

    def execute(self, context: ExecutionContext) -> bool:
        source = context.get_arg('--source')
        output = context.get_arg('--output')

        if not self._validate_source(source):
            return False

        self._prepare_target_dir_for_path(output)
        raw_content = self._read_content(source, context)
        rendered = self.render(raw_content, context)

        if rendered is False:
            return False

        if output == "-":
            self.io().outln(rendered)
        else:
            with open(output, 'wb') as t:
                t.write(rendered.encode('utf-8'))

        return True

    def render_to_file(self, raw_content: str, context: ExecutionContext, dst: str) -> bool:
        """
        Renders a template into a file

        :param raw_content:
        :param context:
        :param dst:
        :return:
        """

        self._prepare_target_dir_for_path(dst)

        with open(dst, 'w') as f:
            rendered = self.render(raw_content, context)

            if rendered is False:
                return False

            f.write(rendered)

        return True

    def render(self, raw_content: str, context: ExecutionContext) -> Union[str, bool]:
        """
        Renders a template
        On error a False is returned

        :return:
        """

        tpl = Environment(loader=FileSystemLoader(['./', './.rkd/templates']), undefined=StrictUndefined) \
            .from_string(raw_content)

        try:
            return tpl.render(**context.env)

        except UndefinedError as e:
            self.io().error_msg('Undefined variable - ' + str(e))
            return False

    def configure_argparse(self, parser: ArgumentParser):
        parser.description = 'Renders a JINJA2 file. Environment variables are accessible in templates.'
        parser.add_argument('--source', '-s', help='Template file', required=True)
        parser.add_argument('--output', '-o', help='Output to file, set "-" for stdout', default='-')


class Jinja2Language(FileRendererTask, MultiStepLanguageExtensionInterface):
    """
    Jinja2 language extension for MultiStepLanguageAgnosticTask

    **Usage using MultiStepLanguageAgnosticTask**

    .. code:: yaml

        version: org.riotkit.rkd/yaml/v2
        imports:
            - rkd.core.standardlib.jinja.Jinja2Language
        tasks:
            :render:
                steps: |
                    #!rkd.core.standardlib.jinja.Jinja2Language
                    Test - RKD_PATH environment variable is {{ RKD_PATH }}.
                    System PATH is {{ PATH }}, using shell {{ SHELL }}


    **Usage standalone**

    .. code:: yaml

        version: org.riotkit.rkd/yaml/v2
        imports:
            - rkd.core.standardlib.jinja.Jinja2Language
        tasks:
            :render:
                extends: rkd.core.standardlib.jinja.Jinja2Language
                input: |
                    Test - RKD_PATH environment variable is {{ RKD_PATH }}.
                    System PATH is {{ PATH }}, using shell {{ SHELL }}

    .. code:: bash

        ./rkdw :render
        ./rkdw :render --output=/tmp/rendered
    """

    name: str
    code: str

    def __init__(self):
        self.name = ':j2:lang'
        self.code = ''

    def get_name(self):
        return self.name

    def _validate_source(self, source: str) -> bool:
        return True

    def configure_argparse(self, parser: ArgumentParser):
        parser.description = 'Renders a JINJA2 file. Environment variables are accessible in templates.'
        parser.add_argument('--source', '-s', help='Template file', required=False, default='')
        parser.add_argument('--output', '-o', help='Output to file, set "-" for stdout', default='-')

    def _read_content(self, source: str, context: ExecutionContext) -> str:
        """
        Read from stdin instead of from file

        :param source:
        :param context:
        :return:
        """

        if self.code:
            return self.code

        return context.get_input().read()

    def with_predefined_details(self, code: str, name: str, step_num: int) -> 'Jinja2Language':
        clone = copy(self)
        clone.name = name
        clone.code = code

        return clone


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
        exclude_pattern = re.compile(context.get_arg('--exclude-pattern')) if context.get_arg('--exclude-pattern') else None
        copy_not_matched = context.get_arg('--copy-not-matching-files')
        template_filenames = context.get_arg('--template-filenames')

        self.io().info_msg('Pattern is `%s`' % context.get_arg('--pattern'))

        for root, subdirs, files in os.walk(source_root):
            for file in files:
                source_full_path = root + '/' + file
                target_full_path = target_root + '/' + source_full_path[len(source_root):]

                if target_full_path.endswith('.j2'):
                    target_full_path = target_full_path[:-3]

                if template_filenames:
                    target_full_path = self.replace_vars_in_filename(context.env, target_full_path)

                if exclude_pattern and self._is_file_matching_filter(exclude_pattern, source_full_path):
                    self.io().info_msg('Skipping file "%s" - (filtered out by --exclude-pattern)' % source_full_path)
                    continue

                if not self._is_file_matching_filter(pattern, source_full_path):
                    if copy_not_matched:
                        self.io().info_msg('Copying "%s" regular file' % source_full_path)
                        self._copy_file(source_full_path, target_full_path)

                        continue

                    self.io().info_msg('Skipping file "%s" (filtered out by --pattern)' % source_full_path)
                    continue

                self.io().info_msg('Rendering file "%s" into "%s"' % (source_full_path, target_full_path))

                if not self._render(source_full_path, target_full_path):
                    # stderr will be passed through
                    return False

                if delete_source_files:
                    self._delete_file(source_full_path)

        return True

    @staticmethod
    def replace_vars_in_filename(env_vars: dict, filename: str) -> str:
        for name, value in env_vars.items():
            filename = filename.replace('--%s--' % name, value)

        return filename

    def _copy_file(self, source_full_path: str, target_full_path: str):
        self.sh('mkdir -p "%s"' % os.path.dirname(target_full_path))
        self.sh('cp -p "%s" "%s"' % (source_full_path, target_full_path))

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
        parser.add_argument('--exclude-pattern', '-xp', help='Optional regexp for a pattern exclude, to exclude files')
        parser.add_argument('--copy-not-matching-files', '-c', help='Copy all files that are not matching the pattern' +
                                                                    ' instead of skipping them', action='store_true')
        parser.add_argument('--template-filenames', '-tf',
                            help='Replace variables in filename eg. --VAR--, ' +
                                 'where VAR is a name of environment variable', action='store_true')


def imports():
    return [
        TaskDeclaration(FileRendererTask()),
        TaskDeclaration(RenderDirectoryTask())
    ]
