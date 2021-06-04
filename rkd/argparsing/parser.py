#!/usr/bin/env python3

import os
from typing import List
from typing import Tuple
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
from shlex import split as split_argv
from ..api.inputoutput import IO
from ..api.contract import TaskDeclarationInterface
from ..api.contract import ArgumentEnv
from .blocks import parse_blocks, TOKEN_BLOCK_REFERENCE_OPENING, TOKEN_BLOCK_REFERENCE_CLOSING, ArgumentBlock
from .model import TaskArguments


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


class CommandlineParsingHelper(object):
    """
    Extends argparse functionality by grouping arguments into Blocks -> Tasks arguments
    """

    io: IO

    def __init__(self, io: IO):
        self.io = io

    def create_grouped_arguments(self, commandline: List[str]) -> List[ArgumentBlock]:
        commandline, blocks = parse_blocks(commandline)

        current_group_elements = []
        current_task_name = 'rkd:initialize'
        cursor = -1
        max_cursor = len(commandline)

        parsed_into_blocks = []

        for part in commandline:
            cursor += 1

            # normalize - strip out spaces to be able to detect "-", "--" and ":" at the beginning of string
            part = part.strip()

            is_flag = part[0:1] == "-"
            is_task = part[0:1] in (':', '@')
            is_block = part.startswith(TOKEN_BLOCK_REFERENCE_OPENING) and part.endswith(TOKEN_BLOCK_REFERENCE_CLOSING)
            previous_is_flag = commandline[cursor-1][0:1] == "-" if cursor >= 1 else False

            # option name or flag
            if is_flag:
                current_group_elements.append(part)

            elif is_block:
                if part not in blocks:
                    raise Exception('Parser error. Cannot find block "{}"'.format(part))

                block: ArgumentBlock = blocks[part]
                block = block.with_tasks_from_first_block(
                    self.create_grouped_arguments(block.body)
                )

                parsed_into_blocks.append(block)

            # option value
            elif not is_flag and previous_is_flag and not is_task:
                current_group_elements.append(part)

            # new task
            elif is_task:
                if current_task_name != 'rkd:initialize':
                    task_arguments = [TaskArguments(current_task_name, current_group_elements)]

                    self.io.internal('Creating task with arguments {}'.format(task_arguments))

                    # by default every task belongs to a block, even if the block for it was not defined
                    parsed_into_blocks.append(ArgumentBlock([current_task_name] + current_group_elements)
                                              .clone_with_tasks(task_arguments))

                current_task_name = part
                current_group_elements = []

            # is not an option (--some or -s) but a positional argument actually
            else:
                current_group_elements.append(part)

            if cursor + 1 == max_cursor:
                task_arguments = [TaskArguments(current_task_name, current_group_elements)]

                self.io.internal('End of commandline arguments, closing current task collection with {}'
                                 .format(task_arguments))

                parsed_into_blocks.append(ArgumentBlock([current_task_name] + current_group_elements)
                                          .clone_with_tasks(task_arguments))

        return self._parse_shared_arguments(self.parse_modifiers_in_blocks(parsed_into_blocks))

    def parse_modifiers_in_blocks(self, blocks: List[ArgumentBlock]) -> List[ArgumentBlock]:
        """Parse list of tasks in blocks attributes eg.
        @error :notify -m 'Failed' and resolve as Notify task with -m argument"""

        for block in blocks:
            attributes = block.raw_attributes()

            if attributes['error']:
                block.set_parsed_error_handler(
                    self.create_grouped_arguments(split_argv(attributes['error']))[0].tasks())

            if attributes['rescue']:
                block.set_parsed_rescue(self.create_grouped_arguments(split_argv(attributes['rescue']))[0].tasks())

        return blocks

    @classmethod
    def _parse_shared_arguments(cls, blocks: List[ArgumentBlock]) -> List[ArgumentBlock]:
        """Apply arguments from task "@" that is before a group of tasks
           "@" without any arguments is clearing previous "@" with arguments
        """

        global_group_elements = []
        new_blocks = []

        for block in blocks:
            block_tasks = []
            block_body = []

            for task in block.tasks():
                task: TaskArguments

                if task.name() == '@':
                    global_group_elements = task.args()
                    # jump to next task - "@" task should not be finally on the list
                    continue

                block_body.append([task.name()] + task.args() + global_group_elements)
                block_tasks.append(task.with_args(task.args() + global_group_elements))

            # cut off empty blocks (ex. ['@', '--type', 'human-rights'] -> [] -> to be removed after propagation)
            if not block_body:
                continue

            # replace all blocks with new blocks that contains the additional arguments
            new_blocks.append(block.clone_with_tasks(block_tasks))

        return new_blocks

    @classmethod
    def parse(cls, declaration: TaskDeclarationInterface, args: list) -> Tuple[dict, dict]:
        """Parses ArgumentParser arguments defined by tasks

        Behavior:
          - Adds RKD-specific arguments
          - Includes task's specific arguments
          - Formats description, including documentation of environment variables

        Returns:
          Tuple of two dicts. First dict: arguments key=>value, Second dict: arguments definitions for advanced usae
        """

        argparse = TraceableArgumentParser(declaration.to_full_name(), formatter_class=RawTextHelpFormatter)

        argparse.add_argument('--log-to-file', '-rf', help='Capture stdout and stderr to file')
        argparse.add_argument('--log-level', '-rl', help='Log level: debug,info,warning,error,fatal')
        argparse.add_argument('--keep-going', '-rk', help='Allow going to next task, even if this one fails',
                              action='store_true')
        argparse.add_argument('--silent', '-rs', help='Do not print logs, just task output', action='store_true')
        argparse.add_argument('--become', '-rb', help='Execute task as given user (requires sudo)', default='')
        argparse.add_argument('--task-workdir', '-rw', help='Set a working directory for this task', default='')

        declaration.get_task_to_execute().configure_argparse(argparse)
        cls.add_env_variables_to_argparse_description(argparse, declaration)

        return vars(argparse.parse_args(args)), argparse.traced_arguments

    @classmethod
    def add_env_variables_to_argparse_description(cls, argparse: ArgumentParser, task: TaskDeclarationInterface):
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

    @staticmethod
    def preparse_args(args: List[str]):
        """
        Parses commandline arguments which are not accessible on tasks level, but are accessible behind tasks
        Those arguments should decide about RKD core behavior on very early stage

        :param args:
        :return:
        """

        limited_args = []

        for arg in args:
            # parse everything before any task or block starts
            if arg.startswith(':') or arg.startswith('@') or arg.startswith('{@'):
                break

            limited_args.append(arg)

        argparse = ArgumentParser(add_help=False)
        argparse.add_argument('--imports', '-ri')

        parsed = vars(argparse.parse_known_args(args=limited_args)[0])

        return {
            'imports': list(filter(None,
                                   os.getenv('RKD_IMPORTS', parsed['imports'] if parsed['imports'] else '').split(':')
                                   ))
        }

    @staticmethod
    def has_any_task(argv: List[str]) -> bool:
        """
        Checks if arguments contains at least one task

        :param argv:
        :return:
        """

        for arg in argv:
            if arg.startswith(':'):
                return True

        return False

    @staticmethod
    def was_help_used(argv: List[str]) -> bool:
        for arg in argv:
            if arg in ['-h', '--help']:
                return True

        return False
