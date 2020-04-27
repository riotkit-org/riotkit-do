
import os
from typing import Dict, List
from .syntax import Component, Task
from importlib.machinery import SourceFileLoader

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class Context:
    _components: Dict[str, Component]
    _tasks: Dict[str, Task]

    def __init__(self, components: List[Component], tasks: List[Task]):
        self._components = {}
        self._tasks = {}

        for component in components:
            self.add_component(component)

        for task in tasks:
            self.add_task(task)

    @classmethod
    def merge(cls, first, second):
        new_ctx = cls([], [])

        for context in [first, second]:
            context: Context

            for name, component in context._components.items():
                new_ctx.add_component(component)

            for name, task in context._tasks.items():
                new_ctx.add_task(task)

        return new_ctx

    def add_component(self, component: Component) -> None:
        self._components[component.to_full_name()] = component

    def add_task(self, task: Task) -> None:
        self._tasks[task.get_name()] = task


class TaskDiscovery:
    """
    Takes responsibility of loading all tasks defined in USER PROJECT, USER HOME and GLOBALLY
    """

    @staticmethod
    def _load_context_from_directory(path: str) -> Context:
        if not os.path.isdir(path):
            raise Exception('Path "%s" font found' % path)

        makefile_path = path + '/makefile.py'

        if not os.path.isfile(makefile_path):
            raise Exception('makefile.py not found at path "%s"' % makefile_path)

        makefile = SourceFileLoader("Makefile", makefile_path).load_module()

        return Context(
            components=makefile.COMPONENTS if "COMPONENTS" in dir(makefile) else [],
            tasks=makefile.TASKS if "TASKS" in dir(makefile) else []
        )

    def create_unified_context(self, chdir: str = '') -> Context:
        """
        Creates a merged context in order:
        - Internal/Core (this package)
        - System-wide (/usr/lib/rkd)
        - User-home ~/.rkd
        - Application (current directory ./.rkd)
        :return:
        """

        paths = [
            CURRENT_SCRIPT_PATH + '/internal',
            '/usr/lib/rkd',
            os.path.expanduser('~/.rkd'),
            chdir + './.rkd'
        ]

        ctx = Context([], [])

        for path in paths:
            if os.path.isdir(path) and os.path.isfile(path + '/makefile.py'):
                ctx = Context.merge(ctx, self._load_context_from_directory(path))

        return ctx
