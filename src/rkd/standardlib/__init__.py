
import pkg_resources
import os
import re
from subprocess import CalledProcessError
from typing import Dict
from typing import List
from argparse import ArgumentParser
from typing import Callable
from typing import Optional
from copy import deepcopy
from ..api.contract import TaskInterface
from ..api.contract import ExecutionContext
from ..api.contract import TaskDeclarationInterface
from ..api.contract import ArgparseArgument
from ..inputoutput import SystemIO
from ..inputoutput import clear_formatting
from ..aliasgroups import parse_alias_groups_from_env, AliasGroup


class InitTask(TaskInterface):
    """
    :init task is executing ALWAYS. That's a technical, core task.

    The purpose of this task is to handle global settings
    """

    def get_name(self) -> str:
        return ':init'

    def get_group_name(self) -> str:
        return ''

    def get_declared_envs(self) -> Dict[str, str]:
        return {
            'RKD_DEPTH': '0',
            'RKD_PATH': '',
            'RKD_ALIAS_GROUPS': '',
            'RKD_UI': 'true'
        }

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--no-ui', '-n', action='store_true',
                            help='Do not display RKD interface (similar to --silent, ' +
                                 'but does not inherit --silent into next tasks)')

    def execute(self, context: ExecutionContext) -> bool:
        """
        :init task is setting user-defined global defaults on runtime
        It allows user to call eg. rkd --log-level debug :task1 :task2
        to set global settings such as log level

        :param context:
        :return:
        """

        # increment RKD_DEPTH
        os.environ['RKD_DEPTH'] = str(int(os.getenv('RKD_DEPTH', '0')) + 1)

        self._ctx.io  # type: SystemIO
        self._ctx.io.silent = context.args['silent']

        # log level is optional to be set
        if context.args['log_level']:
            self._ctx.io.set_log_level(context.args['log_level'])

        if context.get_env('RKD_UI'):
            self._ctx.io.set_display_ui(context.get_env('RKD_UI').lower() == 'true')

        if int(os.getenv('RKD_DEPTH')) >= 2 or context.args['no_ui']:
            self._ctx.io.set_display_ui(False)

        return True

    def is_silent_in_observer(self) -> bool:
        return True


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
        pass

    def get_declared_envs(self) -> Dict[str, str]:
        return {
            'RKD_WHITELIST_GROUPS': '',
            'RKD_ALIAS_GROUPS': ''
        }

    def execute(self, context: ExecutionContext) -> bool:
        io = self._io
        groups = {}
        aliases = parse_alias_groups_from_env(context.get_env('RKD_ALIAS_GROUPS'))

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

            groups[group_name][self.translate_alias(declaration.to_full_name(), aliases)] = declaration

        # iterate over groups and list tasks under groups
        for group_name, tasks in groups.items():
            if not group_name:
                group_name = 'global'

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


class CallableTask(TaskInterface):
    """ Executes a custom callback - allows to quickly define a short task """

    _callable: Callable[[ExecutionContext, TaskInterface], bool]
    _args_callable: Callable[[ArgumentParser], None]
    _argparse_options: Optional[List[ArgparseArgument]]
    _name: str
    _group: str
    _description: str
    _envs: dict
    _become: str

    def __init__(self, name: str, callback: Callable[[ExecutionContext, TaskInterface], bool],
                 args_callback: Callable[[ArgumentParser], None] = None,
                 description: str = '',
                 group: str = '',
                 become: str = '',
                 argparse_options: List[ArgparseArgument] = None):
        self._name = name
        self._callable = callback
        self._args_callable = args_callback
        self._description = description
        self._group = group
        self._envs = {}
        self._become = become
        self._argparse_options = argparse_options

    def get_name(self) -> str:
        return self._name

    def get_become_as(self) -> str:
        return self._become

    def get_description(self) -> str:
        return self._description

    def get_group_name(self) -> str:
        return self._group

    def configure_argparse(self, parser: ArgumentParser):
        if self._argparse_options:
            for opts in self._argparse_options:
                parser.add_argument(*opts.args, **opts.kwargs)

        if self._args_callable:
            self._args_callable(parser)

    def execute(self, context: ExecutionContext) -> bool:
        return self._callable(context, self)

    def push_env_variables(self, envs: dict):
        self._envs = deepcopy(envs)

    def get_declared_envs(self) -> Dict[str, str]:
        return self._envs


class VersionTask(TaskInterface):
    """ Shows version of RKD and of all loaded tasks """

    def get_name(self) -> str:
        return ':version'

    def get_group_name(self) -> str:
        return ''

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def execute(self, context: ExecutionContext) -> bool:
        self._io.outln('RKD version %s' % pkg_resources.get_distribution("rkd").version)
        self._io.print_opt_line()

        table_body = []

        for name, declaration in self._ctx.find_all_tasks().items():
            if not isinstance(declaration, TaskDeclarationInterface):
                continue

            task = declaration.get_task_to_execute()
            class_name = str(task.__class__)
            module = task.__class__.__module__
            parts = module.split('.')

            for num in range(0, len(parts) + 1):
                try_module_name = ".".join(parts)

                try:
                    version = pkg_resources.get_distribution(try_module_name).version
                    table_body.append([name, version, module, class_name])

                    break
                except pkg_resources.DistributionNotFound:
                    parts = parts[:-1]
                except ValueError:
                    table_body.append([name, 'UNKNOWN (local module?)', module, class_name])

        self.io().outln(self.table(
            header=['Name', 'Version', 'Imported from', 'Representation'],
            body=table_body
        ))

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

    def execute(self, ctx: ExecutionContext) -> bool:
        commit_to_git = ctx.get_arg('--commit')
        without_venv = ctx.get_arg('--no-venv')
        use_pipenv = bool(ctx.get_arg('--pipenv'))

        if commit_to_git and not self.check_git_is_clean():
            self.io().error_msg('Current working directory is dirty, you have working changes, ' +
                                'please commit them or stash first')
            return False

        template_structure_path = os.path.dirname(os.path.realpath(__file__)) + '/../misc/initial-structure'

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
                      '--regexp="%s"' % file_path.replace('*', '\*'),
                      '--insert=%s' % file_path
                      ])

        # 3) Add RKD to requirements
        self.io().info('Adding RKD to requirements.txt')
        self._write_requirements(ctx)

        # 4) Create virtual env
        if not without_venv:
            self.io().info('Setting up virtual environment')
            self.on_creating_venv(ctx)
            self._setup_venv(use_pipenv, template_structure_path)

        if commit_to_git:
            self.on_git_add(ctx)
            self.git_add('.gitignore')
            self.git_add('setup-venv.sh')
            self.git_add('requirements.txt')
            self.git_add('.rkd')

            self.commit_to_git()

        self.print_success_msg(use_pipenv, ctx)

        return True

    def _write_requirements(self, ctx: ExecutionContext):
        self.sh('touch requirements.txt')
        self.rkd([':file:line-in-file',
                  'requirements.txt',
                  '--regexp="rkd(.*)"',
                  '--insert="rkd%s"' % self.get_rkd_version_selector()
                  ])
        self.on_requirements_txt_write(ctx)

    def _setup_venv(self, use_pipenv: bool, template_structure_path: str):
        if use_pipenv:
            self.sh('pipenv install rkd%s' % self.get_rkd_version_selector())
            return

        self.sh('cp %s/setup-venv.sh ./' % template_structure_path)
        self.sh('chmod +x setup-venv.sh')
        self.sh('./setup-venv.sh')

    @staticmethod
    def get_rkd_version_selector():
        rkd_version = pkg_resources.get_distribution("rkd").version
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

        return ['.rkd/logs', '*.pyc', '*__pycache__*', '/.venv', '.venv-setup.log']

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
                                  "Add libraries, task providers, tools to the environment using \"pipenv install\"")
            return

        self.io().success_msg("Structure created, use eval $(./setup-venv.sh) to enter Python\'s " +
                              "virtual environment with installed desired RKD version from requirements.txt\n" +
                              "Add libraries, task providers, tools to the requirements.txt " +
                              "for reproducible environments")

    def commit_to_git(self):
        if not os.path.isdir('.git'):
            return

        try:
            self.sh('git commit -m "Create RKD structure"')
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
