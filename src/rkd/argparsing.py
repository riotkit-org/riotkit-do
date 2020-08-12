#!/usr/bin/env python3

from typing import List
from typing import Tuple
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
from .api.contract import TaskDeclarationInterface
from .api.contract import ArgumentEnv


class TraceableArgumentParser(ArgumentParser):
    """Traces options inserted into ArgumentParser for later interpretation

    Example case: ArgumentParser does not allow to check what is the default defined value for argument
                  but we need this information somewhere, so we track add_argument() parameters
                  (it is safe as the API is stable)
    """

    traced_arguments: dict

    def __init__(self, *args, **kwargs):
        self.traced_arguments = {}
        super().__init__(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        self._trace_argument(args, kwargs)
        super().add_argument(*args, **kwargs)

    def _trace_argument(self, args: tuple, kwargs: dict):
        for arg in args:
            self.traced_arguments[arg] = {
                'default': kwargs['default'] if 'default' in kwargs else None
            }

    def get_traced_argument(self, name: str):
        return self.traced_arguments[name]


class TaskArguments(object):
    _name: str
    _args: list

    def __init__(self, task_name: str, args: list):
        self._name = task_name
        self._args = args

    def __repr__(self):
        return 'Task<%s (%s)>' % (self._name, str(self._args))

    def name(self):
        return self._name

    def args(self):
        return self._args


class CommandlineParsingHelper(object):
    """
    Extends argparse functionality by grouping arguments into tasks -> tasks arguments
    """

    @classmethod
    def create_grouped_arguments(cls, commandline: List[str]) -> List[TaskArguments]:
        current_group_elements = []
        current_task_name = 'rkd:initialize'
        tasks = []
        cursor = -1
        max_cursor = len(commandline)

        for part in commandline:
            cursor += 1

            # normalize - strip out spaces to be able to detect "-", "--" and ":" at the beginning of string
            part = part.strip()

            is_flag = part[0:1] == "-"
            is_task = part[0:1] in (':', '@')
            previous_is_flag = commandline[cursor-1][0:1] == "-" if cursor >= 1 else False

            # option name or flag
            if is_flag:
                current_group_elements.append(part)

            # option value
            elif not is_flag and previous_is_flag and not is_task:
                current_group_elements.append(part)

            # new task
            elif is_task:
                if current_task_name != 'rkd:initialize':
                    tasks.append([current_task_name, current_group_elements])

                current_task_name = part
                current_group_elements = []

            # is not an option (--some or -s) but an argument actually
            else:
                current_group_elements.append(part)

            if cursor + 1 == max_cursor:
                tasks.append([current_task_name, current_group_elements])

        return cls._map_to_task_arguments(
            cls._parse_shared_arguments(tasks)
        )

    @classmethod
    def _map_to_task_arguments(cls, tasks: list) -> List[TaskArguments]:
        return list(map(
            lambda task: TaskArguments(task[0], task[1]),
            tasks
        ))

    @classmethod
    def _parse_shared_arguments(cls, tasks: list) -> list:
        """Apply arguments from task "@" that is before a group of tasks
           "@" without any arguments is clearing previous "@" with arguments
        """

        global_group_elements = []
        edited_tasks = []

        for task in tasks:
            task_name, group_elements = task

            if task_name == '@':
                global_group_elements = group_elements
                continue

            edited_tasks.append([
                task_name,
                group_elements + global_group_elements
            ])

        return edited_tasks

    @classmethod
    def parse(cls, task: TaskDeclarationInterface, args: list) -> Tuple[dict, dict]:
        """Parses ArgumentParser arguments defined by tasks

        Behavior:
          - Adds RKD-specific arguments
          - Includes task's specific arguments
          - Formats description, including documentation of environment variables

        Returns:
          Tuple of two dicts. First dict: arguments key=>value, Second dict: arguments definitions for advanced usae
        """

        argparse = TraceableArgumentParser(task.to_full_name(), formatter_class=RawTextHelpFormatter)

        argparse.add_argument('--log-to-file', '-rf', help='Capture stdout and stderr to file')
        argparse.add_argument('--log-level', '-rl', help='Log level: debug,info,warning,error,fatal')
        argparse.add_argument('--keep-going', '-rk', help='Allow going to next task, even if this one fails',
                              action='store_true')
        argparse.add_argument('--silent', '-rs', help='Do not print logs, just task output', action='store_true')
        argparse.add_argument('--become', '-rb', help='Execute task as given user (requires sudo)', default='')

        task.get_task_to_execute().configure_argparse(argparse)
        cls.add_env_variables_to_argparse(argparse, task)

        return vars(argparse.parse_args(args)), argparse.traced_arguments

    @classmethod
    def add_env_variables_to_argparse(cls, argparse: ArgumentParser, task: TaskDeclarationInterface):
        if argparse.description is None:
            argparse.description = ""

        argparse.description += task.get_full_description() + "\n"

        # print all environment variables possible to use
        argparse.description += "\nEnvironment variables for task \"%s\":\n" % task.to_full_name()

        for env in task.get_task_to_execute().internal_normalized_get_declared_envs().values():
            env: ArgumentEnv

            argparse.description += " - %s (default: %s)\n" % (
                str(env.name), str(env.default)
            )

        if not task.get_task_to_execute().get_declared_envs():
            argparse.description += ' -- No environment variables declared -- '
