
import pkg_resources
import os
import re
from subprocess import CalledProcessError
from typing import Dict, Union
from typing import List
from argparse import ArgumentParser
from ..api.contract import TaskInterface, ArgumentEnv
from ..api.contract import ExecutionContext
from ..api.contract import TaskDeclarationInterface
from ..api.syntax import TaskDeclaration
from ..inputoutput import clear_formatting
from ..aliasgroups import parse_alias_groups_from_env, AliasGroup
from ..packaging import find_resource_directory
from .. import env
from .shell import ShellCommandTask


class TasksListingTask(TaskInterface):
    """Lists all enabled tasks

    Environment:
        - RKD_WHITELIST_GROUPS: Comma separated list of groups that should be only visible, others would be hidden
    """

    def get_name(self) -> str:
        return ':tasks'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--all', '-a', help='Show all tasks, including internal tasks', action='store_true')

    @classmethod
    def get_declared_envs(cls) -> Dict[str, Union[str, ArgumentEnv]]:
        return {
            'RKD_WHITELIST_GROUPS': '',
            'RKD_ALIAS_GROUPS': ''
        }

    def execute(self, context: ExecutionContext) -> bool:
        io = self._io
        groups = {}
        aliases = parse_alias_groups_from_env(context.get_env('RKD_ALIAS_GROUPS'))
        show_all_tasks = bool(context.get_arg('--all'))

        # fancy stuff
        whitelisted_groups = context.get_env('RKD_WHITELIST_GROUPS').replace(' ', '').split(',') \
            if context.get_env('RKD_WHITELIST_GROUPS') else []

        # collect into groups
        for name, declaration in self._ctx.find_all_tasks().items():
            group_name = declaration.get_group_name()

            # (optional) whitelists of displayed groups
            if whitelisted_groups:
                group_to_whitelist_check = (':' + group_name) if group_name else ''  # allow empty group ([global])

                if group_to_whitelist_check not in whitelisted_groups:
                    continue

            if group_name not in groups:
                groups[group_name] = {}

            # do not display tasks that are considered internal (eg. to be called only inside pipeline)
            if declaration.is_internal and not show_all_tasks:
                continue

            groups[group_name][self.translate_alias(declaration.to_full_name(), aliases)] = declaration

        # iterate over groups and list tasks under groups
        for group_name, tasks in groups.items():
            if not group_name:
                group_name = 'global'

            # skip empty group
            if not tasks:
                continue

            io.print_group(group_name)

            for task_name, declaration in tasks.items():
                declaration: TaskDeclarationInterface

                try:
                    description = declaration.get_description()
                    text_description = "# " + description if description else ""
                except AttributeError:
                    text_description = ""

                io.outln(
                    self.ljust_task_name(declaration, task_name)
                    + text_description
                )

            io.print_opt_line()

        io.print_opt_line()
        io.opt_outln('Use --help to see task environment variables and switches, eg. rkd :sh --help, rkd --help')

        return True

    @staticmethod
    def translate_alias(full_name: str, aliases: List[AliasGroup]) -> str:
        if not aliases:
            return full_name

        for alias in aliases:
            match = alias.get_aliased_task_name(full_name)

            if match:
                return match

        return full_name

    @staticmethod
    def ljust_task_name(declaration: TaskDeclarationInterface, task_name: str) -> str:
        with_fancy_formatting = declaration.format_task_name(task_name)
        without_fancy_formatting = clear_formatting(with_fancy_formatting)
        ljust_only = without_fancy_formatting.ljust(50, ' ')[len(without_fancy_formatting):]

        return with_fancy_formatting + ljust_only


class VersionTask(TaskInterface):
    """
    Shows version of RKD and of all loaded tasks
    """

    def get_name(self) -> str:
        return ':version'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def execute(self, context: ExecutionContext) -> bool:
        self._io.outln('RKD version %s' % pkg_resources.get_distribution("rkd.core").version)
        self._io.print_opt_line()

        table_body = []

        for name, declaration in self._ctx.find_all_tasks().items():
            if not isinstance(declaration, TaskDeclarationInterface):
                continue

            task: TaskInterface = declaration.get_task_to_execute()
            class_name = str(task.__class__)
            module = task.__class__.__module__
            parts = module.split('.')

            for num in range(0, len(parts) + 1):
                try_module_name = ".".join(parts)

                try:
                    version = pkg_resources.get_distribution(try_module_name).version
                    table_body.append([name, version, module, class_name, task.extends_task()])

                    break
                except pkg_resources.DistributionNotFound:
                    parts = parts[:-1]
                except ValueError:
                    table_body.append([name, 'UNKNOWN (local module?)', module, class_name, task.extends_task()])

        self.io().outln(
            self.io().format_table(
                header=['Name', 'Version', 'Imported from', 'Representation', 'Extends'],
                body=table_body
            )
        )

        return True


class LineInFileTask(TaskInterface):
    """Adds or removes a line in file (works similar to the lineinfile from Ansible)
    """

    def get_name(self) -> str:
        return ':line-in-file'

    def get_group_name(self) -> str:
        return ':file'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('file', help='File name')
        parser.add_argument('--output', help='Output filename (optional, when not specified, ' +
                                             'then source would be overwritten)', default='', required=False)
        parser.add_argument('--regexp', '-r', help='Regexp to find existing occurrence of line', required=True)
        parser.add_argument('--insert', '-i', help='Line to insert or replace', required=True)
        parser.add_argument('--new-after-line', '-ir', help='Regexp to match a line ' +
                                                            'after which a new entry should be added (often called ' +
                                                            'a header or marker line below which we want to add a text)')
        parser.add_argument('--only-first-occurrence', help='Stop at first occurrence', action='store_true')
        parser.add_argument('--fail-on-no-occurrence', '-f', help='Return 1 exit code, when no any occurrence found',
                            action='store_true')

    def execute(self, context: ExecutionContext) -> bool:
        file = context.get_arg('file')
        output_file = context.get_arg('--output') if context.get_arg('--output') else file
        line = context.get_arg('--insert').split("\n")
        regexp = context.get_arg('--regexp')
        after_line_regexp = context.get_arg('--new-after-line')
        fail_on_no_occurrence = context.get_arg('--fail-on-no-occurrence')
        only_first_occurrence = bool(context.get_arg('--only-first-occurrence'))

        if not os.path.isfile(output_file):
            self.io().info('Creating empty file "%s"' % output_file)
            self.sh('touch "%s"' % output_file)

        with open(file, 'r') as f:
            content = f.readlines()

        new_contents = ""
        found = 0

        for file_line in content:
            match = re.match(regexp, file_line)

            if match:
                self.io().debug('Found occurrence of "%s"' % regexp)

                if found and only_first_occurrence:
                    new_contents += file_line
                    continue

                file_line = ("\n".join(line)) + "\n"

                found += 1
                group_num = 0

                for value in list(match.groups()):
                    var_to_replace = '$match[' + str(group_num) + ']'
                    self.io().debug('Replacing "%s" with "%s"' % (var_to_replace, value))
                    file_line = file_line.replace(var_to_replace, value)
                    group_num += 1

            new_contents += file_line

        if not found:
            if fail_on_no_occurrence:
                self.io().error_msg('No matching line for selected regexp found')
                return False

        new_contents = self._insert_new_lines_if_necessary(found, new_contents, line, after_line_regexp,
                                                           only_first_occurrence, regexp)

        with open(output_file, 'w') as f:
            f.write(new_contents)

        self.io().success_msg('Replaced %i lines with "%s" in "%s"' % (found, "\n".join(line), output_file))

        return True

    def _insert_new_lines_if_necessary(self, found_at_least_one_occurrence: bool, contents: str, lines_to_insert: list,
                                       after_line_regexp: str, only_first_occurrence: bool, regexp: str) -> str:
        """Inserts new lines (if necessary)

        For each MARKER (line after which we want to insert new lines)
        check if there are lines already, if not then insert them.
        """

        if not after_line_regexp:
            self.io().debug('No header (marker) regexp defined')

            if found_at_least_one_occurrence:
                return contents

            # if not found_at_least_one_occurrence
            return contents + ("\n".join(lines_to_insert)) + "\n"

        as_lines = contents.split("\n")

        new_lines = []
        current_line_num = -1
        inserted_already_only_first_occurrence_allowed = False

        for line in as_lines:
            current_line_num += 1
            new_lines.append(line)

            if inserted_already_only_first_occurrence_allowed:
                continue

            if re.match(after_line_regexp, line):
                self.io().debug('Matched header line: "%s"' % line)

                # try to skip insertion, if the line already exists (do not duplicate lines)
                # WARNING: Matches only two lines after marker, that's a limitation
                next_lines = "\n".join(as_lines[current_line_num + 1:current_line_num + 2])

                if next_lines and re.match(regexp, next_lines):
                    continue

                self.io().debug('Inserting')
                new_lines += lines_to_insert

                if only_first_occurrence:
                    self.io().debug('Only first occurrence - stopping there with insertions')
                    inserted_already_only_first_occurrence_allowed = True

        return "\n".join(new_lines)


class CreateStructureTask(TaskInterface):
    """ Creates a RKD file structure in current directory

This task is designed to be extended, see methods marked as "interface methods".
    """

    def get_name(self) -> str:
        return ':create-structure'

    def get_group_name(self) -> str:
        return ':rkd'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--commit', '-c',
                            help='Prepare RKD structure as a git commit (needs workspace to be clean)',
                            action='store_true')
        parser.add_argument('--no-venv', help='Do not create virtual env automatically', action='store_true')
        parser.add_argument('--pipenv', help='Generate files for Pipenv', action='store_true')
        parser.add_argument('--latest', help='Always use latest RKD (not recommended)', action='store_true')
        parser.add_argument('--rkd-dev', help='Development mode. Use RKD components from specified local directory')

    def execute(self, ctx: ExecutionContext) -> bool:
        commit_to_git = ctx.get_arg('--commit')
        without_venv = ctx.get_arg('--no-venv')
        use_pipenv = bool(ctx.get_arg('--pipenv'))
        latest = bool(ctx.get_arg('--latest'))
        dev = ctx.get_arg('--rkd-dev')

        if commit_to_git and not self.check_git_is_clean():
            self.io().error_msg('Current working directory is dirty, you have WIP changes, ' +
                                'please commit them or stash first')
            return False

        template_structure_path = find_resource_directory('initial-structure')

        self.on_startup(ctx)

        # 1) Create structure from template
        if not os.path.isdir('.rkd'):
            self._io.info_msg('Creating a folder structure at %s' % os.getcwd())
            self.sh('cp -pr %s/.rkd ./' % template_structure_path, verbose=True)
            self.on_files_copy(ctx)
        else:
            self.io().info_msg('Not creating .rkd directory, already present')

        # 2) Populate git ignore
        self.sh('touch .gitignore')

        for file_path in self.get_patterns_to_add_to_gitignore(ctx):
            self.rkd([':file:line-in-file',
                      '.gitignore',
                      '--regexp="%s"' % file_path.replace('*', "\\*"),
                      '--insert=%s' % file_path
                      ])

        # 3) Add RKD to requirements
        self.io().info('Adding RKD to requirements.txt')
        self._write_requirements(ctx, use_latest=latest)

        # 4) Create virtual env
        if not without_venv:
            self.io().info('Setting up virtual environment')
            self.on_creating_venv(ctx)
            self._setup_venv(use_pipenv, template_structure_path, use_latest=latest, dev_dir=dev)

        if commit_to_git:
            self.on_git_add(ctx)
            self.git_add('.gitignore')
            self.git_add('rkdw')
            self.git_add('requirements.txt')
            self.git_add('.rkd')

            self.commit_to_git()

        self.print_success_msg(use_pipenv, ctx)

        return True

    def _write_requirements(self, ctx: ExecutionContext, use_latest: bool):
        self.sh('touch requirements.txt')
        self.rkd([
            ':file:line-in-file',
            'requirements.txt',
            '--regexp="{package}(.*)"'.format(package=self.get_package_name()),
            '--insert="{package}{selector}"'.format(
                package=self.get_package_name(),
                selector=self.get_rkd_version_selector(use_latest=use_latest)
            )
        ])
        self.on_requirements_txt_write(ctx)

    @staticmethod
    def get_package_name() -> str:
        return 'rkd.core'

    def _setup_venv(self, use_pipenv: bool, template_structure_path: str, use_latest: bool, dev_dir: str):
        if use_pipenv:
            install_str = '{package_name}{selector}'.format(
                package_name=self.get_package_name(),
                selector=self.get_rkd_version_selector(use_latest=use_latest)
            )

            if dev_dir:
                install_str = self._get_development_pipenv_install_str(dev_dir)

            self.sh(f'pipenv install {install_str}')
            return

        self.sh('cp %s/rkdw.py ./rkdw' % template_structure_path)
        self.sh('chmod +x ./rkdw')
        self.sh('./rkdw', env={'ENVIRONMENT_TYPE': 'pipenv' if use_pipenv else 'venv'})

    @staticmethod
    def _get_development_pipenv_install_str(dev_dir: str):
        return f'-e {dev_dir}/process -e {dev_dir}/core'

    def get_rkd_version_selector(self, use_latest: bool):
        if use_latest:
            return ''

        rkd_version = pkg_resources.get_distribution(self.get_package_name()).version
        return '==%s' % rkd_version

    def on_requirements_txt_write(self, ctx: ExecutionContext) -> None:
        """After requirements.txt file is written

        Interface method: to be overridden
        """

        pass

    def get_patterns_to_add_to_gitignore(self, ctx: ExecutionContext) -> list:
        """List of patterns to write to .gitignore

        Interface method: to be overridden
        """

        return ['.rkd/logs', '*.pyc', '*__pycache__*', '/.venv',
                '.venv-setup.log', '/*.egg-info/*', '.eggs', 'dist', 'build']

    def on_startup(self, ctx: ExecutionContext) -> None:
        """When the command is triggered, and the git is not dirty

        Interface method: to be overridden
        """

        pass

    def on_files_copy(self, ctx: ExecutionContext) -> None:
        """When files are copied

        Interface method: to be overridden
        """

        pass

    def on_creating_venv(self, ctx: ExecutionContext) -> None:
        """When creating virtual environment

        Interface method: to be overridden
        """

        pass

    def on_git_add(self, ctx: ExecutionContext) -> None:
        """Action on, when adding files via `git add`

        Interface method: to be overridden
        """

        pass

    def print_success_msg(self, use_pipenv: bool, ctx: ExecutionContext) -> None:
        """Emits a success message

        Interface method: to be overridden
        """

        if use_pipenv:
            self.io().success_msg("Structure created, use \"pipenv shell\" to enter project environment\n" +
                                  "Add libraries, task providers, tools to the environment using \"pipenv install\"\n" +
                                  "Use RKD with 'rkd' command inside pipenv environment")
            return

        self.io().success_msg("Structure created, use RKD through ./rkdw wrapper. To activate environment manually"
                              "type 'source .venv/bin/activate', inside virtual environment you don't need wrapper, "
                              "just type 'rkd'")

    def commit_to_git(self):
        if not os.path.isdir('.git'):
            return

        try:
            self.sh('LANG=C git commit -m "Create RKD structure"')
        except CalledProcessError as e:
            if 'nothing to commit, working tree clean' in e.output:
                return

            raise e

    def git_add(self, path: str):
        if not os.path.isdir('.git'):
            return

        self.sh('git add "%s"' % path)

    def check_git_is_clean(self):
        return self.sh('git diff --stat || true', capture=True).strip() == ''


class DummyTask(TaskInterface):
    """
    Dummy task, use for testing
    """

    def get_name(self) -> str:
        return ':dummy'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--test', action='store_true', required=False, help='Just a test boolean parameter')

    def execute(self, context: ExecutionContext) -> bool:
        self.io().info_msg(f'Hello from dummy task, test={context.get_arg("--test")}')

        return True


def imports() -> List[TaskDeclaration]:
    return [
        TaskDeclaration(TasksListingTask()),
        TaskDeclaration(VersionTask()),
        TaskDeclaration(ShellCommandTask(), internal=True),
        TaskDeclaration(LineInFileTask(), internal=True),
        TaskDeclaration(CreateStructureTask())
    ]
