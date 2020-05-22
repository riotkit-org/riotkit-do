
import os
import sys
from typing import Dict, List, Union
from importlib.machinery import SourceFileLoader
from traceback import print_exc
from .syntax import TaskDeclaration
from .syntax import TaskAliasDeclaration
from .syntax import GroupDeclaration
from .contract import ContextInterface
from .argparsing import CommandlineParsingHelper
from .inputoutput import SystemIO
from .exception import TaskNotFoundException
from .exception import ContextFileNotFoundException
from .exception import PythonContextFileNotFoundException
from .exception import NotImportedClassException
from .yaml_context import YamlParser


CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class ApplicationContext(ContextInterface):
    """
    Application context - collects all tasks together

    Each Context() is collecting tasks from selected directory.
    merge() static method is merging two Context() objects
    eg. merge(Context(), Context()) selecting second as a priority

    ContextFactory() is controlling the order.
    """

    _imported_tasks: Dict[str, TaskDeclaration]
    _task_aliases: Dict[str, TaskAliasDeclaration]
    _compiled: Dict[str, Union[TaskDeclaration, GroupDeclaration]]
    io: SystemIO

    def __init__(self, tasks: List[TaskDeclaration], aliases: List[TaskAliasDeclaration]):
        self._imported_tasks = {}
        self._task_aliases = {}

        for task in tasks:
            self._add_component(task)

        for alias in aliases:
            self._add_task(alias)

    @classmethod
    def merge(cls, first, second):
        """ Add one context to other context. Produces immutable new context. """

        new_ctx = cls([], [])

        for context in [first, second]:
            context: ApplicationContext

            for name, component in context._imported_tasks.items():
                new_ctx._add_component(component)

            for name, task in context._task_aliases.items():
                new_ctx._add_task(task)

        return new_ctx

    def compile(self) -> None:
        """ Resolve all objects in the context. Should be called only, when all contexts were merged """

        self._compiled = self._imported_tasks

        for name, details in self._task_aliases.items():
            self._compiled[name] = self._resolve_alias(name, details)

    def find_task_by_name(self, name: str) -> Union[TaskDeclaration, GroupDeclaration]:
        try:
            return self._compiled[name]
        except KeyError:
            raise TaskNotFoundException(('Task "%s" is not defined. Check if it is defined, or' +
                                         ' imported, or if the spelling is correct.') % name)

    def find_all_tasks(self) -> Dict[str, Union[TaskDeclaration, GroupDeclaration]]:
        return self._compiled

    def _add_component(self, component: TaskDeclaration) -> None:
        self._imported_tasks[component.to_full_name()] = component

    def _add_task(self, task: TaskAliasDeclaration) -> None:
        self._task_aliases[task.get_name()] = task

    def _resolve_alias(self, name: str, alias: TaskAliasDeclaration) -> GroupDeclaration:
        """
        Parse commandline args to fetch list of tasks to join into a group

        Produced result will be available to fetch via find_task_by_name()
        """

        args = CommandlineParsingHelper.create_grouped_arguments(alias.get_arguments())
        resolved_tasks = []

        for argument_group in args:
            resolved_task = self.find_task_by_name(argument_group.name())

            # preserve original task env, and append alias env in priority
            merged_env = resolved_task.get_env()
            merged_env.update(alias.get_env())

            new_task = resolved_task \
                .with_env(merged_env) \
                .with_args(argument_group.args()) \
                .with_user_overridden_env(
                    alias.get_user_overridden_envs() + resolved_task.get_user_overridden_envs()
                )

            resolved_tasks.append(new_task)

        return GroupDeclaration(name, resolved_tasks, alias.get_description())


class ContextFactory:
    """
    Takes responsibility of loading all tasks defined in USER PROJECT, USER HOME and GLOBALLY
    """

    def __init__(self, io: SystemIO):
        self._io = io

    def _load_context_from_directory(self, path: str) -> ApplicationContext:
        if not os.path.isdir(path):
            raise Exception('Path "%s" not found' % path)

        ctx = ApplicationContext([], [])
        contexts = []

        if os.path.isfile(path + '/makefile.py'):
            contexts.append(self._load_from_py(path))

        if os.path.isfile(path + '/makefile.yaml'):
            contexts.append(self._load_from_yaml(path, 'makefile.yaml'))

        if os.path.isfile(path + '/makefile.yml'):
            contexts.append(self._load_from_yaml(path, 'makefile.yml'))

        if not contexts:
            raise ContextFileNotFoundException(path)

        for subctx in contexts:
            ctx = ApplicationContext.merge(ctx, subctx)

        return ctx

    def _load_from_yaml(self, path: str, filename: str) -> ApplicationContext:
        makefile_path = path + '/' + filename

        with open(makefile_path, 'rb') as handle:
            imports, tasks = YamlParser(self._io).parse(handle.read().decode('utf-8'), path, makefile_path)
            return ApplicationContext(tasks=imports, aliases=tasks)

    @staticmethod
    def _load_from_py(path: str):
        makefile_path = path + '/makefile.py'

        if not os.path.isfile(makefile_path):
            raise PythonContextFileNotFoundException(makefile_path)

        try:
            sys.path.append(path)
            makefile = SourceFileLoader("Makefile", makefile_path).load_module()

        except ImportError as e:
            print_exc()
            raise NotImportedClassException(e)

        return ApplicationContext(
            tasks=makefile.IMPORTS if "IMPORTS" in dir(makefile) else [],
            aliases=makefile.TASKS if "TASKS" in dir(makefile) else []
        )

    def create_unified_context(self, chdir: str = '') -> ApplicationContext:
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
            os.getcwd() + '/.rkd'
        ]

        if chdir:
            paths += chdir + '/.rkd'

        if os.getenv('RKD_PATH'):
            paths += os.getenv('RKD_PATH', '').split(':')

        # export for usage inside in makefiles
        os.environ['RKD_PATH'] = ":".join(paths)

        ctx = ApplicationContext([], [])

        for path in paths:
            # not all paths could exist, we consider this, we look where it is possible
            if not os.path.isdir(path):
                continue

            try:
                ctx = ApplicationContext.merge(ctx, self._load_context_from_directory(path))
            except ContextFileNotFoundException:
                pass

        ctx.compile()
        ctx.io = self._io

        return ctx
