
"""
SYNTAX (part of API)
====================

Classes used in a declaration syntax in makefile.py

"""
import sys
import shlex
from dataclasses import dataclass
from types import FunctionType
from typing import List, Dict, Optional, Union
from copy import deepcopy
from uuid import uuid4
from .contract import TaskDeclarationInterface, ExtendableTaskInterface, PipelinePartInterface
from .contract import GroupDeclarationInterface
from .contract import TaskInterface
from .inputoutput import get_environment_copy, ReadableStreamType
from ..argparsing.model import ArgumentBlock
from ..exception import DeclarationException, BlockAlreadyConnectedException


this = sys.modules[__name__]

if 'DECLARED_TASKS_COUNT' not in dir(this):
    this.DECLARED_TASKS_COUNT = 0


def parse_path_into_subproject_prefix(path: str) -> str:
    """
    Logic for concatenating of subproject path from filesystem path as input

    :param path:
    :return:
    """

    return ':' + path.strip().strip('/').replace('/', ':').rstrip(': /')


def merge_workdir(task_workdir: Optional[str], subproject_workdir: Optional[str]) -> str:
    """
    Pure domain method that decides how the workdir merge logic should look like
    :param task_workdir:
    :param subproject_workdir:
    :return:
    """

    if not task_workdir:
        task_workdir = ''

    if not subproject_workdir:
        return task_workdir

    if task_workdir.startswith('/'):
        return task_workdir

    return subproject_workdir + '/' + task_workdir


class TaskDeclaration(TaskDeclarationInterface):
    """
    Task Declaration is a DECLARED USAGE of a Task (instance of TaskInterface)

    Examples of usage:

    .. code:: python

        TaskDeclaration(MyNiceTask(), env={'SOME': 'thing'}, workdir='/tmp', name=':custom:task:name')

    """

    _task: TaskInterface
    _env: Dict[str, str]       # environment at all
    _user_defined_env: list    # list of env variables overridden by user
    _args: List[str]
    _unique_id: str
    _workdir: Optional[str]        # current working directory (eg. combination of subproject + task)
    _task_workdir: Optional[str]   # original task working directory as defined in task
    _project_name: str
    _is_internal: Optional[bool]             # task is not listed on :tasks
    _enforced_task_full_name: Optional[str]

    # mutated fields
    # todo wywalić
    _parent: Optional['GroupDeclaration']
    _blocks: List[ArgumentBlock]

    def __init__(self, task: TaskInterface, env: Dict[str, str] = None, args: List[str] = None,
                 workdir: Optional[str] = None, internal: Optional[bool] = None, name: Optional[str] = None):

        if env is None:
            env = {}

        if args is None:
            args = []

        if not isinstance(task, TaskInterface):
            try:
                has_taskinterface_subclass = list(filter(lambda cls: issubclass(cls, TaskInterface), task.__bases__))

            except AttributeError:
                raise DeclarationException(
                    'Invalid class: TaskDeclaration needs to take TaskInterface as task argument. '
                    f'Got {type(task).__name__}'
                )

            if not has_taskinterface_subclass:
                raise DeclarationException(
                    'Invalid class: TaskDeclaration needs to take TaskInterface as task argument. '
                    f'Got {type(task).__name__}'
                )

        self._unique_id = uuid4().hex
        self._task = task
        self._env = merge_env(env)
        self._args = args
        self._workdir = workdir
        self._task_workdir = workdir
        self._user_defined_env = list(env.keys())
        self._project_name = ''
        self._is_internal = internal
        self._enforced_task_full_name = name
        self._blocks = []
        self._parent = None

    def to_full_name(self):
        full_name = self._enforced_task_full_name if self._enforced_task_full_name else self._task.get_full_name()

        if self._project_name:
            return self._project_name + full_name

        return full_name

    def with_new_name(self, task_name: str, group_name: str) -> 'TaskDeclaration':
        copy = self.clone()
        copy._enforced_task_full_name = task_name

        if group_name:
            copy._enforced_task_full_name += ':' + group_name

        return copy

    def as_internal_task(self) -> 'TaskDeclaration':
        copy = self.clone()
        copy._is_internal = True

        return copy

    def with_env(self, envs: Dict[str, str]):
        """ Immutable environment setter. Produces new object each time. """

        copy = self.clone()
        copy._env = envs

        return copy

    def with_args(self, args: List[str]):
        """ Immutable arguments setter. Produces new object each time """

        copy = self.clone()
        copy._args = args

        return copy

    def with_user_overridden_env(self, env_list: list):
        """ Immutable arguments setter. Produces new object each time """

        copy = self.clone()
        copy._user_defined_env = env_list

        return copy

    def with_connected_block(self, block: ArgumentBlock):
        """
        Immutable arguments setter. Produces new object each time
        Block should be a REFERENCE to an object, not a copy
        """

        if block in self._blocks:
            raise BlockAlreadyConnectedException()

        copy = self.clone()
        copy._blocks.append(block)

        # todo: CONFLICT! There should be DeclarationScheduledToRun as "copy"
        block.register_resolved_task(copy)  # register a both side relation

        return copy

    def as_part_of_subproject(self, workdir: str, subproject_name: str) -> 'TaskDeclaration':
        copy = self.clone()

        copy._workdir = merge_workdir(copy._task_workdir, workdir)
        copy._project_name = subproject_name

        return copy

    def clone(self) -> 'TaskDeclaration':
        """Clone securely the object. There fields shared across objects as references could be kept"""

        copy = deepcopy(self)
        copy._unique_id = uuid4().hex

        return copy

    def get_args(self) -> List[str]:
        return self._args

    def get_task_to_execute(self) -> Union[TaskInterface, ExtendableTaskInterface]:
        return self._task

    def to_list(self) -> list:
        return [self]

    def get_env(self):
        return self._env

    def get_list_of_user_overridden_envs(self) -> list:
        """ Lists environment variables which were overridden by user """

        return self._user_defined_env

    def get_user_overridden_env(self) -> Dict[str, str]:
        """
        Returns key->value of environment defined by user (not inherited from OS)
        :return:
        """

        return {k: v for k, v in self._env.items() if k in self.get_list_of_user_overridden_envs()}

    def get_group_name(self) -> str:
        split = self.to_full_name().split(':')
        return split[1] if len(split) >= 3 else ''

    def get_task_name(self) -> str:
        split = self.to_full_name().split(':')

        if len(split) >= 3:
            return split[2]

        try:
            return split[1]
        except KeyError:
            return self.to_full_name()

    def get_description(self) -> str:
        task = self.get_task_to_execute()

        if task.get_description():
            return task.get_description()

        return task.__doc__.strip().split("\n")[0] if task.__doc__ else ''

    def get_full_description(self) -> str:
        task = self.get_task_to_execute()

        if task.get_description():
            return task.get_description()

        return task.__doc__.strip() if task.__doc__ else ''

    def block(self) -> ArgumentBlock:
        return self._blocks[-1]

    @staticmethod
    def parse_name(name: str) -> tuple:
        split = name.split(':')
        task_name = ":" + split[-1]
        group = ":".join(split[:-1])

        return task_name, group

    def format_task_name(self, name: str) -> str:
        return self.get_task_to_execute().format_task_name(name)

    def get_unique_id(self) -> str:
        """
        Unique ID of a declaration is a TEMPORARY ID created during runtime to distinct even very similar declarations
        """
        return self._unique_id

    @property
    def workdir(self) -> str:
        if not self._workdir:
            return '.'

        return self._workdir

    @property
    def is_internal(self) -> bool:
        """
        Is task considered internal? Should it be unlisted on a list of tasks for end-user?
        """

        if self._is_internal is not None:
            return self._is_internal

        return self._task.is_internal

    def get_input(self) -> Optional[ReadableStreamType]:
        return None

    def __str__(self):
        return 'TaskDeclaration<%s>' % self.to_full_name()

    def with_runtime_declaration(self, parent: Optional['GroupDeclaration'], args: List[str]):
        """
        # todo: Czy na pewno? Może jako osobny byt? Wydaje mi się, że tak.
        #       ScheduledTaskToRun może?

        :param parent:
        :param args:
        :return:
        """

    @property
    def parent_pipeline(self) -> Optional['GroupDeclaration']:
        """
        Information that optionally the TaskDeclaration was defined inside GroupDeclaration (Pipeline)
        :return:
        """

        return self._parent


class DeclarationScheduledToRun(object):
    """
    Declaration scheduled to be executed
    """

    declaration: TaskDeclaration
    runtime_arguments: List[str]
    parent: Optional['GroupDeclaration']
    created_task_num: int
    _env: dict
    _user_overridden_env: list

    _unique_id: str
    _blocks: List[ArgumentBlock]

    def __init__(self, declaration: TaskDeclaration,
                 runtime_arguments: List[str],
                 parent: Optional['GroupDeclaration'] = None,
                 env: Dict[str, any] = None,
                 user_overridden_env: List[str] = None):

        this.DECLARED_TASKS_COUNT += 1

        self.declaration = declaration
        self.runtime_arguments = runtime_arguments
        self.parent = parent
        self._env = env if env else {}
        self._user_overridden_env = user_overridden_env if user_overridden_env else []

        self.created_task_num = this.DECLARED_TASKS_COUNT
        self._unique_id = uuid4().hex
        self._blocks = []

    @property
    def args(self) -> List[str]:
        return self.declaration.get_args() + self.runtime_arguments

    @property
    def env(self) -> Dict[str, any]:
        env = {}
        env.update(self.declaration.get_env())
        env.update(self._env)

        return env

    @property
    def user_overridden_env(self):
        return self.declaration.get_list_of_user_overridden_envs() + self._user_overridden_env

    @property
    def task_num(self) -> int:
        return self.created_task_num

    def connect_block(self, block: ArgumentBlock):
        """
        Append a relation between Block <-> Declaration scheduled for execution
        :param block:
        :return:
        """

        block.register_resolved_task(self)
        self._blocks.append(block)

    def unique_id(self) -> str:
        return self._unique_id

    def __str__(self) -> str:
        return f'Task<{self.declaration.to_full_name()}, #{self.task_num}>'

    def debug(self) -> str:
        return f'Task<{self.declaration.to_full_name()}, #{self.task_num}, ' \
               f'declaration_id={self.declaration.get_unique_id()}>'

    @property
    def repr_as_invoked_task(self) -> str:
        """
        Shows how the Task was called e.g. :sh -c "echo 'The Conquest of Bread, Chapter 2: Well-Being for All'"

        :return:
        """

        return self.declaration.to_full_name() + ' ' + ' '.join(self.args)

    def get_blocks_ordered_by_children_to_parent(self) -> List[ArgumentBlock]:
        """
        Order: First are children, then are parents

        {@first} {@second} {/@} {/@}

        Why: Because the CLOSING ORDER is important, it's like a COMMIT, finalization, closed blocks are collected
             as soon as they are closed

        Will return:
        1. second
        2. first

        :return:
        """

        return list(self._blocks)

    @property
    def blocks(self) -> List[ArgumentBlock]:
        return self._blocks

    def count_non_empty_blocks(self) -> int:
        return len(
            list(filter(
                lambda block: not block.is_default_empty_block,
                self.blocks
            )),
        )


class DeclarationBelongingToPipeline(DeclarationScheduledToRun):
    """
    Task declared inside a Pipeline
    """

    def append(self, runtime_arguments: List[str], env: Dict[str, str], user_overridden_env: List[str]):
        """
        Mutate parameters in cases, where the Task is wrapped multiple times in eg. pipelines, nested blocks

        :param runtime_arguments:
        :param env:
        :param user_overridden_env:
        :return:
        """

        self.runtime_arguments += runtime_arguments
        self._env.update(env)
        self._user_overridden_env += user_overridden_env


class ExtendedTaskDeclaration(object):
    """
    Declaration for a task that extends other task using a function-like syntax
    This is a factory class for the TaskDeclaration
    """

    func: Union[FunctionType, any]
    declaration_args: Dict[str, any]
    name: str

    def __init__(self, task: Union[FunctionType, any], env: Dict[str, str] = None, args: List[str] = None,
                 workdir: Optional[str] = None, internal: Optional[bool] = None, name: Optional[str] = None):

        """
        NOTICE: Should keep the same interface as TaskDeclaration

        :param task:
        :param env:
        :param args:
        :param workdir:
        :param internal:
        :param name:
        """

        self.func = task
        self.name = name
        self.declaration_args = {
            'env': env,
            'args': args,
            'workdir': workdir,
            'internal': internal,
            'name': name
        }

    def create_declaration(self, task: TaskInterface, stdin: Optional[FunctionType] = None):
        """
        To not create dependencies from TaskFactory in the API the job to create a task from function
        is delegated to later layer

        :param task:
        :param stdin:
        :return:
        """

        args = self.declaration_args
        args['task'] = task

        declaration = TaskDeclaration(
            **args
        )

        if stdin:
            declaration.get_input = stdin

        return declaration


class GroupDeclaration(GroupDeclarationInterface):
    """
    Internal DTO: Processed definition of TaskAliasDeclaration into TaskDeclaration
    """

    _name: str
    _declarations: List[DeclarationBelongingToPipeline]
    _description: str

    def __init__(self, name: str, declarations: List[DeclarationBelongingToPipeline], description: str):
        self._name = name
        self._declarations = declarations
        self._description = description

    def get_declarations(self) -> List[DeclarationBelongingToPipeline]:
        return self._declarations

    def get_name(self) -> str:
        return self._name

    def get_group_name(self) -> str:
        split = self._name.split(':')
        return split[1] if len(split) >= 3 else ''

    def get_task_name(self) -> str:
        split = self._name.split(':')

        if len(split) >= 3:
            return split[2]

        try:
            return split[1]
        except KeyError:
            return self._name

    def to_full_name(self):
        return self.get_name()

    def get_description(self) -> str:
        return self._description

    def format_task_name(self, name: str) -> str:
        return name

    @property
    def is_internal(self) -> bool:
        return False


class Pipeline(object):
    """
    Task Caller

    Has a name like a Task, but itself does not do anything than calling other tasks in selected order
    """

    _name: str
    _arguments: List[str]
    _env: Dict[str, str]
    _user_defined_env: list  # list of env variables overridden by user
    _description: str
    _workdir: str
    _project_name: str

    def __init__(self, name: str, to_execute: List[Union[str, PipelinePartInterface]],
                 env: Dict[str, str] = None, description: str = ''):

        if env is None:
            env = {}

        self._name = name
        self._arguments = self._resolve_pipeline_parts(to_execute)
        self._env = merge_env(env)
        self._user_defined_env = list(env.keys())
        self._description = description
        self._workdir = ''
        self._project_name = ''

    def get_name(self):
        if self._project_name:
            return self._project_name + self._name

        return self._name

    def get_arguments(self) -> List[str]:
        return self._arguments

    def get_env(self) -> Dict[str, str]:
        return self._env

    def get_user_overridden_envs(self) -> list:
        """ Lists environment variables which were overridden by user """

        return self._user_defined_env

    def get_description(self) -> str:
        return self._description

    def _clone(self) -> 'Pipeline':
        """Clone securely the object. There fields shared across objects as references could be kept"""

        return deepcopy(self)

    def as_part_of_subproject(self, workdir: str, subproject_name: str) -> 'Pipeline':
        copy = self._clone()

        copy._workdir = merge_workdir(copy._workdir, workdir)
        copy._project_name = subproject_name

        return copy

    @property
    def workdir(self) -> str:
        return self._workdir

    @property
    def project_name(self) -> str:
        return self._project_name

    def is_part_of_subproject(self) -> bool:
        return isinstance(self._project_name, str) and len(self._project_name) > 1

    @staticmethod
    def _resolve_pipeline_parts(parts: List[Union[str, PipelinePartInterface]]) -> List[str]:
        resolved = []

        for part in parts:
            if isinstance(part, PipelinePartInterface):
                resolved += part.to_pipeline_part()
            else:
                resolved.append(part)

        return resolved

    def __str__(self) -> str:
        return f'Pipeline<{self.get_name()}>'


class TaskAliasDeclaration(Pipeline):
    """
    Deprecated: Name will be removed in RKD 6.0
    """


class PipelineTask(PipelinePartInterface):
    """
    Represents a single task in a Pipeline

    .. code:: python

        from rkd.core.api.syntax import Pipeline

        PIPELINES = [
            Pipeline(
                name=':build',
                to_execute=[
                    Task(':server:build --with-bluetooth'),
                    Task(':client:build', '--with-bluetooth')
                ]
            )
        ]
    """

    task_args: List[str]

    def __init__(self, task: str, *task_args):
        if not task_args:
            self.task_args = shlex.split(task)
        else:
            self.task_args = [task] + list(task_args)

    def to_pipeline_part(self) -> List[str]:
        return self.task_args


@dataclass
class PipelineBlock(PipelinePartInterface):
    """
    Represents block of tasks

    Example of generated block:
        {@retry 3} :some-task {/@}


    .. code:: python

        from rkd.core.api.syntax import Pipeline, PipelineTask as Task, PipelineBlock as Block, TaskDeclaration

        Pipeline(
            name=':error-handling-example',
            description=':notify should be invoked after "doing exit" task, and execution of a BLOCK should be interrupted',
            to_execute=[
                Task(':server:build'),
                Block(error=':notify -c "echo \'Build failed\'"', retry=3, tasks=[
                    Task(':docs:build', '--test'),
                    Task(':sh', '-c', 'echo "doing exit"; exit 1'),
                    Task(':client:build')
                ]),
                Task(':server:clear')
            ]
        )

    """

    tasks: List[PipelineTask]
    retry: Optional[int] = None
    retry_block: Optional[int] = None
    error: Optional[str] = None
    rescue: Optional[str] = None

    def __init__(self, tasks: List[PipelineTask], retry: Optional[int] = None, retry_block: Optional[int] = None,
                 error: Optional[str] = None, rescue: Optional[str] = None):
        self.tasks = tasks
        self.retry = retry
        self.retry_block = retry_block
        self.error = error
        self.rescue = rescue

        if not retry and not retry_block and not error and not rescue:
            # @todo: Better exception
            raise Exception('Block needs to have defined at least one modifier e.g. @rescue')

    def to_pipeline_part(self) -> List[str]:
        partial = []
        block_body = ['{']

        if self.error:
            block_body.append(f'@error {self.error} ')

        if self.rescue:
            block_body.append(f'@rescue {self.rescue} ')

        if self.retry:
            block_body.append(f'@retry {self.retry} ')

        if self.retry_block:
            block_body.append(f'@retry-block {self.retry_block} ')

        block_body.append('} ')
        partial.append(''.join(block_body))

        for task in self.tasks:
            partial += task.to_pipeline_part()

        partial.append('{/@}')

        return partial


def merge_env(env: Dict[str, str]):
    """
    Merge custom environment variables set per-task with system environment
    """

    merged_dict = deepcopy(env)
    merged_dict.update(get_environment_copy())

    return merged_dict
