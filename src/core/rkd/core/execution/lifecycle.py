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
from rkd.core.api.contract import TaskInterface
from rkd.core.api.lifecycle import CompilationLifecycleEventAware
from rkd.core.api.inputoutput import IO
from rkd.core.api.syntax import TaskDeclaration, GroupDeclaration


class CompilationLifecycleEvent(object):
    """
    When all of the contexts are compiled, then manipulate the list of tasks

    Context = single makefile (a build file)
    """

    __slots__ = ['_current_task', '_compiled', 'io']
    _current_task: TaskDeclaration
    _compiled: Dict[str, Union[TaskDeclaration, GroupDeclaration]]
    io: IO

    def __init__(self, current_task: TaskDeclaration, compiled: Dict[str, Union[TaskDeclaration, GroupDeclaration]], io: IO):
        self._current_task = current_task
        self._compiled = compiled
        self.io = io

    def expand_into_group(self, tasks: List[TaskDeclaration], pipeline: bool = True,
                          source_first: bool = False, source_last: bool = False) -> None:
        """
        Make a single task to expand itself into a group of tasks

        Input: List of tasks
        Result: All tasks added to the context + when original task is executed then all put tasks are executed

        :param:pipeline should the grouped task be added as a pipeline?
        :param:source_first Add source task at beginning of pipeline
        :param:source_last Add source task at end of pipeline
        """

        # be sure that old task is no longer there
        del self._compiled[self._current_task.to_full_name()]

        # rename original task, make internal
        renamed = self._current_task.with_new_name(
                task_name=':' + self._current_task.get_task_name() + ':exec-group',
                group_name=self._current_task.get_group_name()) \
            .as_internal_task()

        # renamed internal task
        self._compiled[renamed.to_full_name()] = renamed

        # add our group (a pipeline)
        if pipeline:
            if source_first:
                tasks = [renamed] + tasks

            if source_last:
                tasks.append(renamed)

            group = GroupDeclaration(
                name=self._current_task.to_full_name(),
                declarations=tasks,
                description=self._current_task.get_description()
            )
            self._compiled[group.to_full_name()] = group

        # add tasks that are part of the pipeline
        for task in tasks:
            self._compiled[task.to_full_name()] = task

    @staticmethod
    def run_event(io: IO, compiled: Dict[str, Union[TaskDeclaration, GroupDeclaration]]):
        io.internal('Running AfterCompileLifecycleEvent on all tasks')

        for name, declaration in copy(compiled).items():
            io.internal(f'compile({declaration})')

            if not isinstance(declaration, TaskDeclaration):
                io.internal('compile skipped, not a TaskDeclaration')
                continue

            if not isinstance(declaration.get_task_to_execute(), CompilationLifecycleEventAware):
                io.internal('compile skipped, task does not implement CompilationLifecycleEventAware')
                continue

            task: Union[CompilationLifecycleEventAware, TaskInterface] = declaration.get_task_to_execute()
            task.compile(CompilationLifecycleEvent(declaration, compiled, io))
