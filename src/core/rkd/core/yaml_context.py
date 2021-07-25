from dataclasses import dataclass

import yaml
import os
from typing import List, Union
from dotenv import dotenv_values
from copy import deepcopy
from collections import OrderedDict
from .api.parsing import SyntaxParsing
from .dto import ParsedTaskDeclaration, StaticFileContextParsingResult
from .exception import StaticFileParsingException, ParsingException
from .exception import EnvironmentVariablesFileNotFound
from .api.syntax import TaskDeclaration
from .api.contract import ArgparseArgument
from .api.inputoutput import IO
from .api.inputoutput import get_environment_copy
from .yaml_parser import YamlFileLoader


STANDARD_YAML_SYNTAX_TASK = 'rkd.standardlib.syntax.MultiStepLanguageAgnosticTask'


class StaticFileSyntaxInterpreter(object):
    """
    Translates YAML syntax into Python syntax of makefile (makefile.yaml -> makefile.py)
    """

    io: IO
    loader: YamlFileLoader

    def __init__(self, io: IO, loader: YamlFileLoader):
        self.io = io
        self.loader = loader

    def parse(self, content: str, rkd_path: str, file_path: str) -> StaticFileContextParsingResult:
        """
        Loads a makefile.yaml file with validation on the fly, as results a parsed data is output
        that is ready to construct tasks from it
        """

        pre_parsed = yaml.load(content, yaml.Loader)
        subprojects = {}

        if 'version' not in pre_parsed:
            raise StaticFileParsingException(f'"version" is missing in "{file_path}" file')

        parsed = self.loader.load(content, str(pre_parsed.get('version')))

        imports = []

        if "imports" in parsed:
            imports = self.parse_imports(parsed['imports'])

        tasks = self.parse_tasks(
            parsed['tasks'] if 'tasks' in parsed else {},
            rkd_path,
            file_path
        )

        if "subprojects" in parsed:
            subprojects = self.parse_subprojects(parsed['subprojects'])

        return StaticFileContextParsingResult(
            imports=imports,
            parsed=tasks,
            subprojects=subprojects,
            global_environment=self.parse_env(parsed, file_path)
        )

    @staticmethod
    def parse_subprojects(subprojects: List[str]) -> List[str]:
        if not isinstance(subprojects, list):
            raise StaticFileParsingException.from_subproject_not_a_list()

        for value in subprojects:
            if not isinstance(value, str):
                raise StaticFileParsingException.from_not_a_string(str(value))

        return subprojects

    def parse_tasks(self, tasks: dict, rkd_path: str, makefile_path) \
            -> List[ParsedTaskDeclaration]:

        """
        Parse tasks section of YAML

        Arguments:
            tasks: List of tasks
            rkd_path: Path to the .rkd directory
            makefile_path: Path to the makefile.yaml/yml that is being parsed
        """

        parsed_tasks: List[ParsedTaskDeclaration] = []

        for name, yaml_declaration in tasks.items():
            parsed_tasks.append(self._parse_task(name, yaml_declaration, rkd_path, makefile_path))

        return parsed_tasks

    def parse_env(self, parent: dict, makefile_path: str) -> OrderedDict:
        """Parse environment variables from parent node

        Priority (first - higher): 1) environment 2) env_files

        Examples:
            environment:
                EVENT_NAME: "In memory of Maxwell Itoya, an Nigerian immigrant killed by police at flea market. He was innocent, and left wife with 3 kids."

            env_files:
                - .rkd/env/important-history-events.envs

        Returns:
            KV dictionary
        """
        envs = OrderedDict()

        if "env_files" in parent:
            for path in parent['env_files']:
                envs.update(self._load_env_from_file(path, makefile_path))

        if "environment" in parent:
            envs.update(parent['environment'])

        return envs

    @staticmethod
    def _load_env_from_file(path: str, makefile_path: str) -> dict:
        """Load .env file

        Loads .env file in Bash-like syntax from selected path (path to file, not directory).
        Looks also in .rkd/{{path}} and in {{makefile_path}}/{{path}}

        Arguments:
            path: Path to file that contains env variables
            makefile_path: Path to the Makefile.yaml that is being processed

        Returns:
            KV dictionary
        """

        search_paths = [
            path,
            '.rkd/' + path,
            os.path.dirname(makefile_path) + '/' + path
        ]

        for search_path in search_paths:
            if not os.path.isfile(search_path):
                continue

            return dotenv_values(dotenv_path=search_path)

        raise EnvironmentVariablesFileNotFound(path, search_paths)

    def _parse_task(self, name: str, yaml_declaration: dict,
                    rkd_path: str, makefile_path: str) -> ParsedTaskDeclaration:

        description = yaml_declaration['description'] if 'description' in yaml_declaration else ''
        arguments = yaml_declaration['arguments'] if 'arguments' in yaml_declaration else {}
        become = yaml_declaration['become'] if 'become' in yaml_declaration else ''
        workdir = yaml_declaration.get('workdir', '')
        internal = bool(yaml_declaration['internal']) if 'internal' in yaml_declaration else None
        inner_execute = yaml_declaration['execute'] if 'execute' in yaml_declaration else None
        task_input = yaml_declaration['input'] if 'input' in yaml_declaration else None
        extends = yaml_declaration['extends'] if 'extends' in yaml_declaration else STANDARD_YAML_SYNTAX_TASK
        steps = []

        # important: order of environment variables loading
        environment = self.parse_env(yaml_declaration, makefile_path)

        if rkd_path:
            environment['RKD_PATH'] = rkd_path

        try:
            steps = yaml_declaration['steps']

            # to make the syntax easier allow a single step
            if isinstance(steps, str):
                steps = [steps]

        except KeyError:
            if extends == STANDARD_YAML_SYNTAX_TASK:
                raise StaticFileParsingException('"steps" are required to be defined in task "%s"' % name)

        task_name, group_name = TaskDeclaration.parse_name(name)

        return ParsedTaskDeclaration(
            name=task_name,
            group=group_name,
            description=description,
            argparse_options=self.parse_argparse_arguments(arguments),
            task_type=extends,
            become=become,
            workdir=workdir,
            internal=internal,
            steps=steps,
            execute=inner_execute,
            task_input=task_input,
            environment=environment
        )

    @staticmethod
    def parse_argparse_arguments(arguments: dict) -> List[ArgparseArgument]:
        converted = []

        for name, params in arguments.items():
            converted.append(ArgparseArgument([name], params))

        return converted

    @staticmethod
    def parse_imports(classes: List[str]) -> List[TaskDeclaration]:
        """Parses imports strings into Python classes

        Args:
            classes: List of classes to import

        Returns:
            A list of basic task declarations with imported tasks inside
            [
                TaskDeclaration(ProtestWorkplaceTask()),
                TaskDeclaration(StrikeWorkplaceTask()),
                TaskDeclaration(OccupyWorkplaceTask()),
                TaskDeclaration(RunProductionByWorkersOnTheirOwnTask())
            ]

        Raises:
            YamlParsingException: When a class or module does not exist
        """

        try:
            return SyntaxParsing.parse_imports_by_list_of_classes(classes)

        except ParsingException as e:
            raise StaticFileParsingException(str(e))
