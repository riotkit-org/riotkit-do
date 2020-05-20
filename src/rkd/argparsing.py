#!/usr/bin/env python3

from typing import List
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
from .contract import TaskDeclarationInterface
from .exception import TaskNotFoundException


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

    @staticmethod
    def create_grouped_arguments(commandline: List[str]) -> List[TaskArguments]:
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
            is_task = part[0:1] == ":"
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
                    tasks.append(TaskArguments(current_task_name, current_group_elements))

                current_task_name = part
                current_group_elements = []
            else:
                raise TaskNotFoundException('Unknown task "%s"' % part)

            if cursor + 1 == max_cursor:
                tasks.append(TaskArguments(current_task_name, current_group_elements))

        return tasks

    @classmethod
    def parse(cls, task: TaskDeclarationInterface, args: list):
        argparse = ArgumentParser(task.to_full_name(), formatter_class=RawTextHelpFormatter)

        argparse.add_argument('--log-to-file', '-rf', help='Capture stdout and stderr to file')
        argparse.add_argument('--log-level', '-rl', help='Log level: debug,info,warning,error,fatal')
        argparse.add_argument('--keep-going', '-rk', help='Allow going to next task, even if this one fails',
                              action='store_true')
        argparse.add_argument('--silent', '-rs', help='Do not print logs, just task output', action='store_true')

        task.get_task_to_execute().configure_argparse(argparse)
        cls.add_env_variables_to_argparse(argparse, task)

        return vars(argparse.parse_args(args))

    @classmethod
    def add_env_variables_to_argparse(cls, argparse: ArgumentParser, task: TaskDeclarationInterface):
        if argparse.description is None:
            argparse.description = ""

        # print all environment variables possible to use
        argparse.description += "\nEnvironment variables for task \"%s\":\n" % task.to_full_name()

        for env_name, default_value in task.get_task_to_execute().get_declared_envs().items():
            argparse.description += " - %s (default: %s)\n" % (str(env_name), str(default_value))

        if not task.get_task_to_execute().get_declared_envs():
            argparse.description += ' -- No environment variables declared -- '
