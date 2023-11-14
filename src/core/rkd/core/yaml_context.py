"""
Static File Syntax Interpreter
==============================

Parses static document (eg. YAML) into StaticFileContextParsingResult()
On later stage there are tasks created from StaticFileContextParsingResult()
"""

import yaml
import os
from typing import List, Dict, Union
from dotenv import dotenv_values
from collections import OrderedDict, namedtuple
from .api.decorators import SUPPORTED_DECORATORS
from .api.parsing import SyntaxParsing
from .dto import ParsedTaskDeclaration, StaticFileContextParsingResult
from .exception import StaticFileParsingException, ParsingException
from .exception import EnvironmentVariablesFileNotFound
from .api.syntax import TaskDeclaration, Pipeline, PipelineTask, PipelineBlock
from .api.contract import ArgparseArgument, PipelinePartInterface
from .api.inputoutput import IO
from .yaml_parser import YamlFileLoader


STANDARD_YAML_SYNTAX_TASK = 'rkd.core.standardlib.syntax.MultiStepLanguageAgnosticTask'


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

        if "pipelines" in parsed:
            imports += self.parse_pipelines(parsed['pipelines'])

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

        for name, task_attributes in tasks.items():
            parsed_tasks.append(self._parse_task(name, task_attributes, rkd_path, makefile_path))

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

    def parse_pipelines(self, pipelines: Dict[str, dict]) -> List[Pipeline]:
        """
        Parse pipelines in the document

        :param pipelines:
        :return:
        """

        parsed = []

        for name, options in pipelines.items():
            parsed.append(self._parse_pipeline(name, options))

        return parsed

    def _parse_pipeline(self, name: str, pipeline: dict) -> Pipeline:
        return Pipeline(
            name=name,
            description=pipeline.get('description'),
            to_execute=self._parse_pipeline_task_list(pipeline.get('tasks'))
        )

    def _parse_entry_on_task_list(self, task: dict):
        if "task" in task:
            if isinstance(task['task'], str):
                return PipelineTask(task['task'])

            return PipelineTask(*task['task'])

        elif "block" in task:
            task = task['block']
            tasks: List[PipelineTask] = self._parse_pipeline_task_list(task.get('tasks'))

            return PipelineBlock(
                tasks=tasks,   # recursion
                retry=int(task.get('retry')) if 'retry' in task else None,
                retry_block=int(task.get('retry-block')) if 'retry-block' in task else None,
                error=str(task.get('error')) if 'error' in task else None,
                rescue=str(task.get('rescue')) if 'rescue' in task else None
            )
        else:
            # todo: better exception
            raise Exception(f'A Task on the "tasks" list needs to have "task" or "block" defined. Body: {task}')

    def _parse_pipeline_task_list(self, tasks: list) -> Union[List[PipelinePartInterface], List[PipelineTask]]:
        return list(map(lambda task: self._parse_entry_on_task_list(task), tasks))

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

    def _parse_task(self, name: str, document_attributes: dict,
                    rkd_path: str, makefile_path: str) -> ParsedTaskDeclaration:
        """
        Maps YAML keys into ParsedTaskDeclaration() object
        Parsing decorators, putting default values, casting data types

        :param name:
        :param document_attributes:
        :param rkd_path:
        :param makefile_path:
        :return:
        """

        mappedVar = namedtuple('mappedVar', ['name', 'default', 'casting', 'is_method'])
        mapping = {
            # ParsedTaskDeclaration attributes
            'description': mappedVar(name='description', default='', casting=None, is_method=False),
            'argparse_options': mappedVar(name='arguments', default={},
                                          casting=self.parse_argparse_arguments, is_method=False),
            'become': mappedVar(name='become', default='', casting=None, is_method=False),
            'workdir': mappedVar(name='workdir', default='', casting=None, is_method=False),
            'internal': mappedVar(name='internal', default=False, casting=bool, is_method=False),
            'execute': mappedVar(name='execute', default=None, casting=None, is_method=True),
            'configure': mappedVar(name='configure', default=None, casting=None, is_method=True),
            'steps': mappedVar(name='steps', default=[], casting=None, is_method=True),
            'inner_execute': mappedVar(name='inner_execute', default=None, casting=None, is_method=True),
            'task_input': mappedVar(name='input', default=None, casting=None, is_method=False),
            'task_type': mappedVar(name='extends', default=STANDARD_YAML_SYNTAX_TASK, casting=None, is_method=False)
        }

        mapping_by_yaml_key = {v.name: k for k, v in mapping.items()}
        allowed_keys_not_in_mapping = ['environment', 'env_files']  # those are handled manually
        allowed_yaml_keys = mapping_by_yaml_key.keys()

        parsed_task_declaration_kwargs = {}
        parsed_decorators = {}
        overridden = []

        # resolve all configuration that is defined
        for attribute, value in document_attributes.items():
            split = attribute.split('@')
            yaml_key_without_decorator = split[0]

            try:
                decorator = split[1]
            except IndexError:
                decorator = None

            yaml_key = yaml_key_without_decorator + ('@' + decorator if decorator else '')
            overridden.append(yaml_key_without_decorator)

            #
            # Special attributes - are not mapped, but handled manually
            #
            if yaml_key_without_decorator in allowed_keys_not_in_mapping:
                if decorator:
                    raise StaticFileParsingException.from_attribute_not_supporting_decorators(
                        yaml_key_without_decorator, decorator
                    )
                continue

            # the YAML key that describes task is not supported (e.g. a name with typo "extteends")
            if yaml_key_without_decorator not in allowed_yaml_keys:
                raise StaticFileParsingException.from_not_allowed_attribute(
                    yaml_key_without_decorator, name
                )

            # @before_parent, @after_parent, etc.
            if decorator:
                if not mapping[yaml_key_without_decorator].is_method:
                    raise StaticFileParsingException.from_attribute_not_supporting_decorators(
                        yaml_key_without_decorator, decorator
                    )

                if decorator not in SUPPORTED_DECORATORS:
                    raise StaticFileParsingException.from_unsupported_decorator_type(
                        attribute, name, makefile_path
                    )

                if yaml_key_without_decorator in parsed_decorators:
                    raise StaticFileParsingException.from_doubled_decorator(yaml_key_without_decorator, decorator)

                parsed_decorators[yaml_key_without_decorator] = decorator

            def_key, default_value, casting, is_method = mapping[mapping_by_yaml_key[yaml_key_without_decorator]]
            value = document_attributes.get(yaml_key)

            if casting:
                value = casting(value)

            # output will be used as kwargs to ParsedTaskDeclaration()
            parsed_task_declaration_kwargs[mapping_by_yaml_key[yaml_key_without_decorator]] = value

        # apply default values to keys NOT DEFINED by user
        for kwarg, mapped_var in mapping.items():
            yaml_key, default_value, casting, is_method = mapped_var

            # value already defined
            if yaml_key in overridden:
                continue

            if casting:
                default_value = casting(default_value)

            parsed_task_declaration_kwargs[kwarg] = default_value

        # important: order of environment variables loading
        environment = self.parse_env(document_attributes, makefile_path)

        if rkd_path:
            environment['RKD_PATH'] = rkd_path

        # extra logic: Multistep tasks have a mandatory "steps" key to be defined
        if not parsed_task_declaration_kwargs.get('steps'):
            if parsed_task_declaration_kwargs['task_type'] == STANDARD_YAML_SYNTAX_TASK:
                raise StaticFileParsingException('"steps" are required to be defined in task "%s"' % name)

        # to make the syntax easier allow a single step
        if isinstance(parsed_task_declaration_kwargs.get('steps'), str):
            parsed_task_declaration_kwargs['steps'] = [parsed_task_declaration_kwargs.get('steps')]

        task_name, group_name = TaskDeclaration.parse_name(name)

        return ParsedTaskDeclaration(
            name=task_name,
            group=group_name,
            environment=environment,
            method_decorators=parsed_decorators,
            **parsed_task_declaration_kwargs
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
