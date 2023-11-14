"""
Lifecycle
=========

Defines a lifecycle of tasks in RKD scheduler.

-> compile: When all of the contexts are compiled, then manipulate the list of tasks
-> configure: After task was scheduled to execute (we know this task will be executed)
-> shutdown: After all tasks have been executed

Each lifecycle event emits a separate event for each task. Events are immutable, cannot be manipulated by task -
only allowed methods can be executed.
"""

from copy import copy
from typing import Dict, Union, List
from ..api.contract import ExecutionContext, ExtendableTaskInterface
from ..api.inputoutput import IO
from ..iterator import TaskIterator
from ..api.syntax import TaskDeclaration, GroupDeclaration, DeclarationScheduledToRun
from ..argparsing.parser import CommandlineParsingHelper
from ..exception import LifecycleConfigurationException, HandledExitException
from ..execution.analysis import analyze_allowed_usages


class CompilationLifecycleEvent(object):
    """
    When all of the contexts are compiled, then give possibility to manipulate the list of tasks
    EXECUTES FOR ALL TASKS that are implementing CompilationLifecycleEventAware interface

    Context = single makefile (a build file)
    """

    __slots__ = ['_current_task', '_compiled', 'io']
    _current_task: TaskDeclaration
    _compiled: Dict[str, Union[TaskDeclaration, GroupDeclaration]]
    io: IO

    def __init__(self, current_task: TaskDeclaration, compiled: Dict[str, Union[TaskDeclaration, GroupDeclaration]],
                 io: IO):

        self._current_task = current_task
        self._compiled = compiled
        self.io = io

    def get_current_declaration(self) -> TaskDeclaration:
        return self._current_task

    def expand_into_group(self, tasks: List[TaskDeclaration], pipeline: bool = True,
                          source_first: bool = False, source_last: bool = False,
                          rename_to: str = ':exec-group', hide_children: bool = False) -> None:
        """
        Make a single task to expand itself into a group of tasks

        Input: List of tasks
        Result: All tasks added to the context + when original task is executed then all put tasks are executed

        :param:pipeline should the grouped task be added as a pipeline?
        :param:source_first Add source task at beginning of pipeline
        :param:source_last Add source task at end of pipeline
        :param:rename_to Rename original task to
        """

        # todo: Fix pipeline support after introducing DeclarationScheduledToRun and DeclarationBelongingToPipeline

        self.io.internal(f'Expanding task {self._current_task} into a group')

        # be sure that old task is no longer there
        del self._compiled[self._current_task.to_full_name()]

        # rename original task, make internal
        renamed = self._current_task.with_new_name(
                task_name=':' + self._current_task.get_task_name() + rename_to,
                group_name=self._current_task.get_group_name()) \
            .as_internal_task()

        # renamed internal task
        self._compiled[renamed.to_full_name()] = renamed

        # add our group (a pipeline)
        if pipeline:
            if source_first:
                self.io.internal('Original task will be executed first in a group')
                tasks = [renamed] + tasks

            if source_last:
                self.io.internal('Original task will be executed last in a group')
                tasks.append(renamed)

            group = GroupDeclaration(
                name=self._current_task.to_full_name(),
                declarations=tasks,
                description=self._current_task.get_description()
            )

            self.io.internal(f'Adding group task {group} as {group.to_full_name()}')
            self._compiled[group.to_full_name()] = group

        # add tasks that are part of the pipeline
        for task in tasks:
            if hide_children:
                task = task.as_internal_task()

            self.io.internal(f'Appending {task} to group')
            self._compiled[task.to_full_name()] = task

    @staticmethod
    def run_event(io: IO, compiled: Dict[str, Union[TaskDeclaration, GroupDeclaration]]):
        io.internal('Running AfterCompileLifecycleEvent on all tasks')

        for name, declaration in copy(compiled).items():
            io.internal(f'compile({declaration})')

            if not isinstance(declaration, TaskDeclaration):
                io.internal('compilation skipped, not a TaskDeclaration')
                continue

            if not isinstance(declaration.get_task_to_execute(), ExtendableTaskInterface):
                io.internal('compilation skipped, task does not implement ExtendableTaskInterface')
                continue

            task: ExtendableTaskInterface = declaration.get_task_to_execute()
            task.compile(CompilationLifecycleEvent(declaration, compiled, io))


class ConfigurationLifecycleEvent(object):
    ctx: ExecutionContext

    def __init__(self, ctx: ExecutionContext):
        self.ctx = ctx


class ConfigurationResolver(TaskIterator):
    """
    Goes through task-by-task and calls configure() ONLY WHEN method implements ConfigurationLifecycleEventAware
    interface.

    NOTICE: The configure() method has limited scope of what can be called inside it. The purpose is to prevent
            misuse of that method to avoid having heavy tasks like in Gradle project
    """

    io: IO

    def __init__(self, io: IO):
        self.io = io

    def iterate_blocks(self) -> bool:
        return True

    # see TaskIterator interface
    def process_task(self, scheduled: DeclarationScheduledToRun, task_num: int):
        self.run_event(scheduled)

    def run_event(self, scheduled: DeclarationScheduledToRun):

        if not isinstance(scheduled.declaration, TaskDeclaration):
            self.io.internal('configuration skipped, not a TaskDeclaration')
            return

        if not isinstance(scheduled.declaration.get_task_to_execute(), ExtendableTaskInterface):
            self.io.internal('configuration skipped, task does not implement ExtendableTaskInterface')
            return

        self.io.internal(f'configuring {scheduled.debug()}')

        task: ExtendableTaskInterface = scheduled.declaration.get_task_to_execute()

        try:
            # perform a static analysis first
            usage_report = analyze_allowed_usages(task.configure, task.get_configuration_attributes())

            if usage_report.has_any_not_allowed_usage():
                raise LifecycleConfigurationException.from_invalid_method_used(
                    task_full_name=scheduled.declaration.to_full_name(),
                    method_names=str(usage_report)
                )

            # call configuration
            task.internal_inject_dependencies(self.io)
            task.configure(ConfigurationLifecycleEvent(
                ctx=self._create_ctx(scheduled.declaration, scheduled.parent, scheduled.args))
            )

        except Exception as err:
            self.io.error_msg('{exc_type}: {msg}'.format(exc_type=str(err.__class__.__name__), msg=str(err)))
            self.io.error_msg(f'Task "{scheduled}" cannot be configured')

            raise HandledExitException() from err

    @classmethod
    def _create_ctx(cls, declaration: TaskDeclaration, parent: Union[GroupDeclaration, None] = None, args: list = None):
        parsed_args, defined_args = CommandlineParsingHelper.parse(declaration, args if args else [])

        return ExecutionContext(
            declaration=declaration,
            parent=parent,
            args=parsed_args,
            env=declaration.get_env(),
            defined_args=defined_args
        )
