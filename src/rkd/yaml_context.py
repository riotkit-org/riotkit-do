import yaml
import ast
import os
import importlib
from types import FunctionType
from argparse import ArgumentParser
from typing import List, Tuple, Union, Callable
from traceback import format_exc
from dotenv import dotenv_values
from copy import deepcopy
from collections import OrderedDict
from .exception import YamlParsingException
from .exception import EnvironmentVariablesFileNotFound
from .syntax import TaskDeclaration
from .syntax import TaskAliasDeclaration
from .contract import ExecutionContext
from .contract import TaskInterface
from .standardlib import CallableTask
from .inputoutput import IO


class YamlParser:
    """
    Translates YAML syntax into Python syntax of makefile (makefile.yaml -> makefile.py)
    """

    io: IO

    def __init__(self, io: IO):
        self.io = io

    def parse(self, content: str, rkd_path: str, file_path: str) -> Tuple[List[TaskDeclaration], List[TaskAliasDeclaration]]:
        """ Parses whole YAML into entities same as in makefile.py - IMPORTS, TASKS """

        parsed = yaml.load(content, yaml.FullLoader)
        imports = []
        global_envs = self.parse_env(parsed, file_path)

        if "imports" in parsed:
            imports = self.parse_imports(parsed['imports'])

        if "tasks" not in parsed or not isinstance(parsed, dict):
            raise YamlParsingException('"tasks" section not found in YAML file')

        tasks = self.parse_tasks(parsed['tasks'], rkd_path, file_path, global_envs)

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
                args_callback=self.create_arguments_callback(arguments),
                callback=self.create_execution_callback_from_steps(steps, name, rkd_path, envs)
            )
        )

    def create_execution_callback_from_steps(self, steps: List[str], task_name: str, rkd_path: str, envs: dict) \
            -> Callable[[ExecutionContext, TaskInterface], bool]:

        """Creates implementation of TaskInterface.execute() - a callback that will execute all steps (callbacks)"""

        steps_as_callbacks = []
        step_num = 0

        for step in steps:
            step_num += 1
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

            if language == 'python':
                steps_as_callbacks.append(self.create_python_callable(code, step_num, task_name, rkd_path, envs))
            elif language == 'bash':
                steps_as_callbacks.append(self.create_bash_callable(code, step_num, task_name, rkd_path, envs))
            else:
                raise YamlParsingException('Unsupported step language "%s"' % language)

        #
        # Here is code that will be executed as a TASK execute() -> list of step.execute()
        #
        def execute(ctx: ExecutionContext, this: TaskInterface) -> bool:
            """ Proxy that executes all steps one-by-one in TaskInterface.execute() """

            for step_execute in steps_as_callbacks:
                # if one of step failed, then interrupt and mark task as failure
                if not step_execute(ctx, this):
                    return False

            return True

        return execute

    @staticmethod
    def create_python_callable(code: str, step_num: int, task_name: str, rkd_path: str, envs: dict) \
            -> Callable[[ExecutionContext, CallableTask], bool]:

        def execute(ctx: ExecutionContext, this: CallableTask) -> bool:
            env_backup = deepcopy(os.environ)

            # "ctx" and "this" will be available as a local context
            try:
                # prepare environment
                os.environ.update(envs)
                os.environ['RKD_PATH'] = rkd_path
                this.push_env_variables(os.environ)
                filename = task_name + '@step ' + str(step_num)

                # compile code
                tree = ast.parse(code)
                eval_expr = ast.Expression(tree.body[-1].value)
                exec_expr = ast.Module(tree.body[:-1], type_ignores=[])

                # run compiled code
                exec(compile(exec_expr, filename, 'exec'))

                to_return = eval(compile(eval_expr, filename, 'eval'))

            except Exception as e:
                this.io().error_msg('Error while executing step %i in task "%s". Exception: %s' % (
                    step_num, task_name, str(e)
                ))
                this.io().error_msg(format_exc())

                to_return = False

            finally:
                os.environ = env_backup

            return to_return

        return execute

    @staticmethod
    def create_bash_callable(code: str, step_num: int, task_name: str, rkd_path: str, envs: dict) \
            -> Callable[[ExecutionContext, TaskInterface], bool]:

        def execute(ctx: ExecutionContext, this: TaskInterface) -> bool:
            try:
                # assign arguments from ArgumentParser (argparse) to env variables
                args = OrderedDict()
                for name, value in ctx.args.items():
                    args['ARG_' + name.upper()] = value

                # glue all environment variables
                process_env = OrderedDict()
                process_env.update(envs)
                process_env.update(args)
                process_env.update({'RKD_PATH': rkd_path, 'RKD_DEPTH': int(os.getenv('RKD_DEPTH', 0)) + 1})

                this.sh(code, strict=True, env=process_env)
                return True

            except Exception as e:
                this.io().error_msg('Error while executing step %i in task "%s". Exception: %s' % (
                    step_num, task_name, str(e)
                ))
                return False

        return execute

    @staticmethod
    def create_arguments_callback(arguments: dict) -> Callable[[ArgumentParser], None]:
        """ Creates implementation of TaskInterface.configure_argparse() """

        def arguments_callback(parser: ArgumentParser):
            for name, params in arguments.items():
                parser.add_argument(name, **params)

        return arguments_callback

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
