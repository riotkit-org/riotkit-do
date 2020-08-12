import yaml
import os
import importlib
from types import FunctionType
from typing import List, Tuple, Union, Callable
from dotenv import dotenv_values
from copy import deepcopy
from collections import OrderedDict
from .exception import YamlParsingException
from .exception import EnvironmentVariablesFileNotFound
from .api.syntax import TaskDeclaration
from .api.syntax import TaskAliasDeclaration
from .api.contract import ExecutionContext
from .api.contract import TaskInterface
from .api.contract import ArgparseArgument
from .standardlib import CallableTask
from .api.inputoutput import IO
from .yaml_parser import YamlFileLoader
from .execution.declarative import DeclarativeExecutor


class YamlSyntaxInterpreter:
    """
    Translates YAML syntax into Python syntax of makefile (makefile.yaml -> makefile.py)
    """

    io: IO
    loader: YamlFileLoader

    def __init__(self, io: IO, loader: YamlFileLoader):
        self.io = io
        self.loader = loader

    def parse(self, content: str, rkd_path: str, file_path: str) \
            -> Tuple[List[TaskDeclaration], List[TaskAliasDeclaration]]:

        """ Parses whole YAML into entities same as in makefile.py - IMPORTS, TASKS """

        pre_parsed = yaml.load(content, yaml.Loader)

        if 'version' not in pre_parsed:
            raise YamlParsingException('"version" is not specified in YAML file')

        parsed = self.loader.load(content, pre_parsed['version'])

        imports = []
        global_envs = self.parse_env(parsed, file_path)

        if "imports" in parsed:
            imports = self.parse_imports(parsed['imports'])

        tasks = self.parse_tasks(
            parsed['tasks'] if 'tasks' in parsed else {},
            rkd_path,
            file_path,
            global_envs
        )

        return imports + tasks, []

    def parse_tasks(self, tasks: dict, rkd_path: str, makefile_path, global_envs: OrderedDict) -> List[TaskDeclaration]:
        """ Parse tasks section of YAML and creates rkd.standardlib.CallableTask type tasks

        Arguments:
            tasks: List of tasks
            rkd_path: Path to the .rkd directory
            makefile_path: Path to the makefile.yaml/yml that is being parsed
            global_envs: Environment defined in global scope of YAML document (WITHOUT os.environ)
        """

        parsed_tasks: List[Union[TaskDeclaration, None]] = []

        for name, yaml_declaration in tasks.items():
            parsed_tasks.append(self._parse_task(name, yaml_declaration, rkd_path, global_envs, makefile_path))

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

    def _parse_task(self, name: str, yaml_declaration: dict, rkd_path: str,
                    global_env: OrderedDict, makefile_path: str) -> TaskDeclaration:

        description = yaml_declaration['description'] if 'description' in yaml_declaration else ''
        arguments = yaml_declaration['arguments'] if 'arguments' in yaml_declaration else {}
        become = yaml_declaration['become'] if 'become' in yaml_declaration else ''

        # important: order of environment variables loading
        envs = deepcopy(global_env)
        envs.update(self.parse_env(yaml_declaration, makefile_path))
        envs.update(deepcopy(os.environ))

        try:
            steps = yaml_declaration['steps']

            # to make the syntax easier allow a single step
            if isinstance(steps, str):
                steps = [steps]

        except KeyError:
            raise YamlParsingException('"steps" are required to be defined in task "%s"' % name)

        task_name, group_name = TaskDeclaration.parse_name(name)

        return TaskDeclaration(
            CallableTask(
                name=task_name,
                description=description,
                group=group_name,
                argparse_options=self.parse_argparse_arguments(arguments),
                callback=self.create_execution_callback_from_steps(steps, name, rkd_path, envs),
                become=become
            )
        )

    @staticmethod
    def create_execution_callback_from_steps(steps: List[str], task_name: str, rkd_path: str, envs: dict) \
            -> Callable[[ExecutionContext, TaskInterface], bool]:

        """Creates implementation of TaskInterface.execute() - a callback that will execute all steps (callbacks)"""

        declarative = DeclarativeExecutor()

        #
        # Collect all steps and create micro-callbacks per step, that will be executed one-by-one in execute()
        #
        for step in steps:
            language = 'bash'
            as_lines = step.strip().split("\n")
            first_line = as_lines[0]
            code = step

            # code that begin with a hashbang will have hashbang cut off
            # #!bash
            # #!python
            if first_line[0:2] == '#!':
                language = first_line[2:]
                code = "\n".join(as_lines[1:])

            declarative.add_step(language, code, task_name, rkd_path, envs)

            if language not in ['python', 'bash']:
                raise YamlParsingException('Unsupported step language "%s"' % language)

        return declarative.execute_steps_one_by_one

    @staticmethod
    def parse_argparse_arguments(arguments: dict) -> List[ArgparseArgument]:
        """ Creates implementation of TaskInterface.configure_argparse() """

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

        parsed: List[TaskDeclaration] = []

        for import_str in classes:
            parts = import_str.split('.')
            class_name = parts[-1]
            import_path = '.'.join(parts[:-1])

            # importing just a full module name eg. "rkd_python"
            if len(parts) == 1:
                import_path = import_str
                class_name = 'imports'
            # Test if it's not a class name
            # In this case we treat is as a module and import an importing method imports()
            elif class_name.lower() == class_name:
                import_path += '.' + class_name
                class_name = 'imports'

            try:
                module = importlib.import_module(import_path)
            except ImportError as e:
                raise YamlParsingException('Import "%s" is invalid - cannot import class "%s" - error: %s' % (
                    import_str, class_name, str(e)
                ))

            if class_name not in dir(module):
                raise YamlParsingException('Import "%s" is invalid. Class "%s" not found in module "%s"' % (
                    import_str, class_name, import_path
                ))

            if isinstance(module.__getattribute__(class_name), FunctionType):
                parsed += module.__getattribute__(class_name)()
            else:
                parsed.append(TaskDeclaration(module.__getattribute__(class_name)()))

        return parsed
