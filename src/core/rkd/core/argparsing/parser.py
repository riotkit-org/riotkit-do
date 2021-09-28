#!/usr/bin/env python3

import os
from dataclasses import dataclass
from typing import List, Optional
from typing import Tuple
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
from shlex import split as split_argv

from .. import env
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


@dataclass
class CommandlineParsingContext(object):
    current_group_elements: list
    current_task_name: Optional[str]
    cursor: int
    task_num: int
    max_cursor: int
    in_block: bool

    # used only when: in_block = True
    in_block_current_body: list
    in_block_task_arguments: list

    parsed_into_blocks: list

    def is_next_cursor_an_end(self) -> bool:
        return self.cursor + 1 == self.max_cursor


class CommandlineParsingHelper(object):
    """
    Extends argparse functionality by grouping arguments into Blocks -> Tasks arguments
    """

    io: IO

    def __init__(self, io: IO):
        self.io = io

    def create_grouped_arguments(self, commandline: List[str], in_block: bool = False) -> List[ArgumentBlock]:
        commandline, blocks = parse_blocks(commandline)

        self.io.internal_lifecycle(f'Argument parsing, in_block={in_block}')
        self.io.internal(f'commandline, blocks = {commandline}, {blocks}')

        ctx = CommandlineParsingContext(
            current_group_elements=[],
            current_task_name=None,
            cursor=-1,
            task_num=0,
            max_cursor=len(commandline),

            # used only when: in_block = True
            in_block_current_body=[],
            in_block_task_arguments=[],

            parsed_into_blocks=[],
            in_block=in_block
        )

        for part in commandline:
            ctx.cursor += 1

            # normalize - strip out spaces to be able to detect "-", "--" and ":" at the beginning of string
            part = part.strip()

            is_flag = part[0:1] == "-"
            is_task = part[0:1] in (':', '@')
            is_block = part.startswith(TOKEN_BLOCK_REFERENCE_OPENING) and part.endswith(TOKEN_BLOCK_REFERENCE_CLOSING)

            previous_is_flag = commandline[ctx.cursor-1][0:1] == "-" if ctx.cursor >= 1 else False

            # option name or flag
            # e.g. --help or --name="something"
            if is_flag:
                self.io.internal(f'parse({part}), is_flag=True, cursor={ctx.cursor}')
                ctx.current_group_elements.append(part)

            elif is_block:
                self._close_current_task(ctx)
                self.io.internal(f'parse({part}), is_block=True, cursor={ctx.cursor}')

                if part not in blocks:
                    raise Exception(f'Parser error. Cannot find block "{part}". Block found in commandline, '
                                    'but not parsed by parse_blocks() before')

                block: ArgumentBlock = blocks[part]
                self.io.internal(f'Constructing block from body {block.body}')

                block = block.with_tasks_from_first_block(
                    self.create_grouped_arguments(block.body, in_block=True)
                )

                self.io.internal(f'Appending a block to the arguments in place of {part}')
                self.io.internal(f'commandline={commandline}')
                ctx.parsed_into_blocks.append(block)

            # option value
            # e.g. "something" - in context of --name "something"
            elif not is_flag and previous_is_flag and not is_task:
                self.io.internal(f'parse({part}), is_value=True, cursor={ctx.cursor}')
                ctx.current_group_elements.append(part)

            # new task
            elif is_task:
                self.io.internal(f'[Begin] parse({part}) is_task={is_task}, '
                                 f'task_num={ctx.task_num}, cursor={ctx.cursor}')

                # at first close previous Task
                if ctx.task_num > 0:
                    self._close_current_task(ctx)

                # then open a new Task parsing
                ctx.task_num += 1
                ctx.current_task_name = part
                ctx.current_group_elements = []

                self.io.internal(
                    f'[Finalize] parse({part}), is_task=True, cursor={ctx.cursor}, in_block={in_block} '
                    f', Opened new task: current_task_name={ctx.current_task_name}'
                )

            # is not an option (--some or -s) but a positional argument actually
            else:
                self.io.internal('parse({part}): else')
                ctx.current_group_elements.append(part)

            # we are at the end of block
            if ctx.is_next_cursor_an_end():
                self.io.internal('parse({part}): is_next_cursor_an_end=True')
                self._close_current_task(ctx)

        self.io.internal_lifecycle(f'End of in_block={in_block} argument parsing')

        if in_block:
            ctx.parsed_into_blocks = [
                ArgumentBlock(ctx.in_block_current_body).clone_with_tasks(ctx.in_block_task_arguments)
            ]

        return self._parse_shared_arguments(self.parse_modifiers_in_blocks(ctx.parsed_into_blocks))

    def _close_current_task(self, ctx: CommandlineParsingContext) -> None:
        """
        Join all task arguments, options, switches etc. and create TaskArguments() object

        :param ctx:
        :return:
        """

        self.io.internal(f'Trying to close Task parsing for {ctx.current_task_name}')

        if ctx.current_task_name is None:
            self.io.internal('current_task_name is None, not closing Task parsing')
            return

        self.io.internal(f'task_num={ctx.task_num}, in_block={ctx.in_block}')
        task_arguments = [TaskArguments(ctx.current_task_name, ctx.current_group_elements)]

        self.io.internal(f'Creating task with arguments {task_arguments}, cursor={ctx.cursor}')

        if ctx.in_block:
            ctx.in_block_current_body += [ctx.current_task_name] + ctx.current_group_elements
            ctx.in_block_task_arguments += task_arguments
        else:
            # by default every task belongs to a block, even if the block for it was not defined
            ctx.parsed_into_blocks.append(
                ArgumentBlock.create_default_block([ctx.current_task_name] + ctx.current_group_elements, task_arguments)
            )

        ctx.current_task_name = None

    def parse_modifiers_in_blocks(self, blocks: List[ArgumentBlock]) -> List[ArgumentBlock]:
        """
        Parse list of tasks in blocks attributes eg.
        @error :notify -m 'Failed' and resolve as Notify task with -m argument
        """

        for block in blocks:
            attributes = block.raw_attributes()

            if attributes['error']:
                self.io.internal(f'Parsing @error in {block}')
                block.set_parsed_error_handler(
                    self.create_grouped_arguments(split_argv(attributes['error']))[0].tasks())

            if attributes['rescue']:
                self.io.internal(f'Parsing @rescue in {block}')
                block.set_parsed_rescue(self.create_grouped_arguments(split_argv(attributes['rescue']))[0].tasks())

        return blocks

    def _parse_shared_arguments(self, blocks: List[ArgumentBlock]) -> List[ArgumentBlock]:
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
            new_block = block.clone_with_tasks(block_tasks)

            self.io.internal(f'Got finally a block {new_block.tasks()} from block body {new_block.body}, '
                             f'id={new_block.id()}')

            new_blocks.append(new_block)

        return new_blocks

    @classmethod
    def parse(cls, declaration: TaskDeclarationInterface, args: list) -> Tuple[dict, dict]:
        """Parses ArgumentParser arguments defined by tasks

        Behavior:
          - Adds RKD-specific arguments
          - Includes task's specific arguments
          - Formats description, including documentation of environment variables

        Returns:
          Tuple of two dicts. First dict: arguments key=>value, Second dict: arguments definitions for advanced usage
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

        argparse.description += "\nType: " + \
                                type(task.get_task_to_execute()).__module__ + \
                                "." + \
                                type(task.get_task_to_execute()).__name__ + \
                                "\n"

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
    def preparse_global_arguments_before_tasks(args: List[str]):
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

        argparse = ArgumentParser(add_help=True, prog='rkd', formatter_class=RawTextHelpFormatter)
        argparse.description = '''
Global environment variables:
 - RKD_DEPTH (default: 0) (should not be touched - internal)
 - RKD_PATH (default: )
 - RKD_ALIAS_GROUPS (default: )
 - RKD_UI (default: true)
 - RKD_SYS_LOG_LEVEL (default: info)
 - RKD_IMPORTS (default: )
        '''

        argparse.add_argument('--imports', '-ri',
                              help='Imports a task or list of tasks separated by ":". '
                                   'Example: "rkt_utils.docker:rkt_ciutils.boatci:rkd_python". '
                                   'Instead of switch there could be also environment variable "RKD_IMPORTS" used',
                              default='')
        argparse.add_argument('--log-level', '-rl',
                              help='Global log level (can be overridden on task level)',
                              default='info')
        argparse.add_argument('--silent', '-s',
                              help='Show only tasks stdout/stderr (during all tasks)',
                              action='store_true')
        argparse.add_argument('--print-event-history',
                              help='Print execution history at the end',
                              action='store_true')
        argparse.add_argument('--no-ui', '-n',
                              action='store_true',
                              help='Do not display RKD interface (similar to --silent, '
                                   'but applies only to beginning and end messages)')

        parsed = vars(argparse.parse_args(args=limited_args))

        imports = list(filter(
            None,
            (parsed['imports'] if parsed['imports'] else os.getenv('RKD_IMPORTS', '')).split(':')
        ))

        return {
            'imports': imports,
            'log_level': env.system_log_level() if env.system_log_level() else parsed['log_level'],
            'silent': parsed['silent'],
            'no_ui': env.no_ui() if env.no_ui() else parsed['no_ui'],
            'print_event_history': parsed['print_event_history']
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
