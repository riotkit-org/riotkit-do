
"""Application container - manages a list of available tasks to execute (all imported)
"""

import os
import sys
import time
from copy import deepcopy
from datetime import datetime
from typing import Dict, List, Union, Tuple, Optional
from importlib.machinery import SourceFileLoader
from traceback import print_exc
from uuid import uuid4
from . import env
from .api.syntax import TaskDeclaration, parse_path_into_subproject_prefix
from .api.syntax import TaskAliasDeclaration
from .api.syntax import GroupDeclaration
from .api.contract import ContextInterface
from .api.parsing import SyntaxParsing
from .argparsing.parser import CommandlineParsingHelper
from .api.inputoutput import SystemIO
from .exception import TaskNotFoundException
from .exception import ContextFileNotFoundException
from .exception import PythonContextFileNotFoundException
from .exception import NotImportedClassException
from .exception import ContextException
from .execution.lifecycle import CompilationLifecycleEvent
from .packaging import get_user_site_packages
from .yaml_context import YamlSyntaxInterpreter
from .yaml_parser import YamlFileLoader


RKD_CORE_PATH = os.path.dirname(os.path.realpath(__file__))


def generate_id() -> str:
    return str(time.time_ns()) + '-' + str(uuid4())


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
    _created_at: datetime
    _directory: str
    _subprojects: List[str]
    workdir: Optional[str]
    project_prefix: Optional[str]
    directories: []
    io: SystemIO
    id: str

    def __init__(self, tasks: List[TaskDeclaration],
                 aliases: List[TaskAliasDeclaration],
                 directory: str,
                 subprojects: List[str],
                 workdir: str,
                 project_prefix: str):

        self._imported_tasks = {}
        self._task_aliases = {}
        self._created_at = datetime.now()
        self._directory = directory
        self.directories = [directory] if directory else []
        self.workdir = workdir
        self.project_prefix = project_prefix
        self._subprojects = subprojects
        self.id = generate_id()

        for name in subprojects:
            if name != name.strip('./ '):
                raise Exception(f'Subproject "{name}" name is invalid')

        for task in tasks:
            self._add_task(task)

        for alias in aliases:
            self._add_pipeline(alias)

    @classmethod
    def merge(cls, primary: 'ApplicationContext', subctx: 'ApplicationContext') -> 'ApplicationContext':
        """ Add one context to other context. Produces immutable new context. """

        context: ApplicationContext
        primary = deepcopy(primary)

        for name, component in subctx._imported_tasks.items():
            primary._add_task(component, parent_ctx=subctx)

        for name, task in subctx._task_aliases.items():
            primary._add_pipeline(task)

        primary.directories += subctx.directories

        return primary

    def compile(self) -> None:
        """ Resolve all objects in the context. Should be called only, when all contexts were merged """

        self._compiled = self._imported_tasks

        for task in self._compiled:
            self.io.internal(f'Defined task {task} by context compilation')

        for name, details in self._task_aliases.items():
            self.io.internal(f'Defined task alias {name}')
            self._compiled[name] = self._resolve_pipeline(name, details)

        CompilationLifecycleEvent.run_event(self.io, self._compiled)

    def find_task_by_name(self, name: str) -> Union[TaskDeclaration, GroupDeclaration]:
        try:
            return self._compiled[name]
        except KeyError:
            raise TaskNotFoundException(('Task "%s" is not defined. Check if it is defined, or' +
                                         ' imported, or if the spelling is correct.') % name)

    def find_all_tasks(self) -> Dict[str, Union[TaskDeclaration, GroupDeclaration]]:
        return self._compiled

    def get_creation_date(self) -> datetime:
        return self._created_at

    @property
    def subprojects(self) -> List[str]:
        return self._subprojects

    def _add_task(self, task: TaskDeclaration, parent_ctx: Optional['ApplicationContext'] = None) -> None:
        """
        :param task:
        :param parent_ctx: Task could be imported from an inherited subproject context
        :return:
        """

        if not parent_ctx:
            parent_ctx = self

        if parent_ctx.workdir and parent_ctx.project_prefix:
            task = task.as_part_of_subproject(parent_ctx.workdir, subproject_name=parent_ctx.project_prefix)

        self._imported_tasks[task.to_full_name()] = task

    def _add_pipeline(self, pipeline: TaskAliasDeclaration, parent_ctx: Optional['ApplicationContext'] = None) -> None:
        if not parent_ctx:
            parent_ctx = self

        if parent_ctx.workdir and parent_ctx.project_prefix:
            pipeline = pipeline.as_part_of_subproject(parent_ctx.workdir, subproject_name=parent_ctx.project_prefix)

        self._task_aliases[pipeline.get_name()] = pipeline

    def _resolve_pipeline(self, name: str, pipeline: TaskAliasDeclaration) -> GroupDeclaration:
        """
        Parse commandline args to fetch list of tasks to join into a group

        Produced result will be available to fetch via find_task_by_name()
        This brings a support for "Pipelines" (also called Task Aliases)

        Scenario:
            Given as input a list of chained tasks eg. ":task1 :task2 --arg1=value :task3"
            Expected to resolve as TaskDeclaration objects with injected arguments
        """

        cmdline_parser = CommandlineParsingHelper(self.io)
        args = cmdline_parser.create_grouped_arguments(pipeline.get_arguments())
        resolved_tasks = []

        for block in args:
            for argument_group in block.tasks():
                # single TaskDeclaration
                resolved_declarations = [self.find_task_by_name(argument_group.name())]

                # or GroupDeclaration (multiple)
                if isinstance(resolved_declarations[0], GroupDeclaration):
                    resolved_declarations = self._resolve_recursively(resolved_declarations[0])

                for resolved_declaration in resolved_declarations:
                    resolved_declaration: TaskDeclaration

                    # preserve original task env, and append alias env in priority
                    merged_env = resolved_declaration.get_env()
                    merged_env.update(pipeline.get_env())

                    new_task = resolved_declaration \
                        .with_env(merged_env) \
                        .with_args(argument_group.args() + resolved_declaration.get_args()) \
                        .with_user_overridden_env(
                            pipeline.get_user_overridden_envs() + resolved_declaration.get_user_overridden_envs()
                        ) \
                        .with_connected_block(block)

                    if pipeline.is_part_of_subproject():
                        new_task = new_task.as_part_of_subproject(
                            workdir=pipeline.workdir,
                            subproject_name=pipeline.project_name
                        )

                    resolved_tasks.append(new_task)

        return GroupDeclaration(name, resolved_tasks, pipeline.get_description())

    def _resolve_recursively(self, group: GroupDeclaration) -> List[TaskDeclaration]:
        """
        Returns:
            List[Tuple[bool, TaskDeclaration]] - the "bool" means if task was resolved from a group
        """

        tasks = []

        for declaration in group.get_declarations():
            if isinstance(declaration, GroupDeclaration):
                tasks += self._resolve_recursively(declaration)
                continue

            tasks.append(declaration)

        return tasks

    def __str__(self):
        return 'ApplicationContext<id={id}, workdir={workdir},prefix={prefix}>'.format(
            id=self.id,
            workdir=self.workdir,
            prefix=self.project_prefix
        )


class ContextFactory(object):
    """
    Takes responsibility of loading all tasks defined in USER PROJECT, USER HOME and GLOBALLY
    """

    def __init__(self, io: SystemIO):
        self._io = io

    def _load_context_from_directory(self, path: str, workdir: Optional[str] = None,
                                     subproject: str = None) -> List[ApplicationContext]:

        if not os.path.isdir(path):
            raise Exception('Path "%s" not found' % path)

        contexts = []

        if os.path.isfile(path + '/makefile.py'):
            contexts += self._expand_contexts(self._load_from_py(path,
                                                                 workdir=workdir,
                                                                 prefix=subproject))

        if os.path.isfile(path + '/makefile.yaml'):
            contexts += self._expand_contexts(self._load_from_yaml(path, 'makefile.yaml',
                                                                   workdir=workdir,
                                                                   prefix=subproject))

        if os.path.isfile(path + '/makefile.yml'):
            contexts += self._expand_contexts(self._load_from_yaml(path, 'makefile.yml',
                                                                   workdir=workdir,
                                                                   prefix=subproject))
        if not contexts:
            raise ContextFileNotFoundException(path)

        return contexts

    def _expand_contexts(self, ctx: ApplicationContext) -> List[ApplicationContext]:
        """
        Expands a single ApplicationContext into multiple contexts, when an input context
        contains **subprojects**

        :param ctx:
        :return:
        """

        contexts = [ctx]

        self._io.internal(f'Expanding contexts for {ctx}')

        if ctx.subprojects:
            for subdir_path in ctx.subprojects:
                workdir_path = subdir_path

                if ctx.workdir:
                    workdir_path = ctx.workdir + '/' + workdir_path

                rkd_path = workdir_path + '/.rkd'

                self._io.internal('Trying subproject at {path}'.format(path=rkd_path))

                if not os.path.isdir(rkd_path):
                    raise Exception(
                        f'Subproject directory {rkd_path} does not exist or does not contain ".rkd" directory'
                    )

                project_prefix = parse_path_into_subproject_prefix(subdir_path)

                if ctx.project_prefix:
                    project_prefix = ctx.project_prefix + project_prefix

                contexts += self._load_context_from_directory(
                    path=rkd_path,
                    workdir=workdir_path,
                    subproject=project_prefix
                )

        return contexts

    def _load_from_yaml(self, path: str, filename: str, workdir: str, prefix: str) -> ApplicationContext:
        makefile_path = path + '/' + filename

        with open(makefile_path, 'rb') as handle:
            imported, tasks, subprojects = YamlSyntaxInterpreter(self._io, YamlFileLoader([])).parse(
                handle.read().decode('utf-8'), path, makefile_path
            )

            # Issue 33: Support mixed declarations in imports()
            imports, aliases = distinct_imports(makefile_path, imported)

            self._io.internal(
                f'Building context from YAML workdir={workdir}, project_prefix={prefix}, directory={path}'
            )

            return ApplicationContext(tasks=imports, aliases=tasks + aliases, directory=path,
                                      subprojects=subprojects, workdir=workdir, project_prefix=prefix)

    def _load_from_py(self, path: str, workdir: str, prefix: str):
        makefile_path = path + '/makefile.py'

        if not os.path.isfile(makefile_path):
            raise PythonContextFileNotFoundException(makefile_path)

        try:
            sys.path.append(path)

            # extra SourceFileLoader usage is due to Python bug: https://bugs.python.org/issue20178
            # noinspection PyArgumentList
            SourceFileLoader("makefile", RKD_CORE_PATH + '/misc/internal/empty/makefile.py').load_module()

            # noinspection PyArgumentList
            makefile = SourceFileLoader("makefile", makefile_path).load_module()

        except ImportError as e:
            print_exc()
            raise NotImportedClassException(e)

        # Issue 33: Support mixed declarations in imports()
        # noinspection PyUnresolvedReferences
        imports, aliases = distinct_imports(makefile_path, makefile.IMPORTS if "IMPORTS" in dir(makefile) else [])
        # noinspection PyUnresolvedReferences
        subprojects = makefile.SUBPROJECTS if "SUBPROJECTS" in dir(makefile) else []

        if "TASKS" in dir(makefile):
            # noinspection PyUnresolvedReferences
            aliases += makefile.TASKS

        if "PIPELINES" in dir(makefile):
            # noinspection PyUnresolvedReferences
            aliases += makefile.PIPELINES

        self._io.internal(
            f'Building context from PY workdir={workdir}, project_prefix={prefix}, directory={path}, path={makefile_path}'
        )

        return ApplicationContext(
            tasks=imports,
            aliases=aliases,
            directory=path,
            subprojects=subprojects,
            workdir=workdir,
            project_prefix=prefix
        )

    def _load_context_from_list_of_imports(self, additional_imports: List[str]) -> ApplicationContext:
        """
        Creates ApplicationContext from simple list of imports

        :param additional_imports:
        :return:
        """

        self._io.internal(
            f'Building context from shell --imports={additional_imports}'
        )

        declarations = SyntaxParsing.parse_imports_by_list_of_classes(additional_imports)
        ctx = ApplicationContext(declarations, [], '', subprojects=[], workdir='', project_prefix='')

        return ctx

    def create_unified_context(self, chdir: str = '', additional_imports: List[str] = None) -> ApplicationContext:
        """
        Creates a merged context in order:
        - Internal/Core (this package)
        - System-wide (/usr/lib/rkd and /usr/share/rkd)
        - User-home ~/.rkd
        - Application (current directory ./.rkd)
        :return:
        """

        paths = [
            RKD_CORE_PATH + '/misc/internal',
            '/usr/lib/rkd',
            '/usr/share/rkd/internal',
            get_user_site_packages() + '/usr/share/rkd/internal',
            os.path.expanduser('~/.rkd'),
            os.getcwd() + '/.rkd'
        ]

        if chdir:
            paths += chdir + '/.rkd'

        paths += env.rkd_paths()

        # export for usage inside in makefiles
        os.environ['RKD_PATH'] = ":".join(paths)

        ctx = ApplicationContext([], [], '', subprojects=[], workdir='', project_prefix='')
        ctx.io = self._io

        for path in paths:
            # not all paths could exist, we consider this, we look where it is possible
            if not os.path.isdir(path):
                continue

            try:
                contexts = self._load_context_from_directory(path)
            except ContextFileNotFoundException:
                continue

            for second_ctx in contexts:
                try:
                    self._io.internal(f'Context.merge({ctx}, {second_ctx}')
                    ctx = ApplicationContext.merge(ctx, second_ctx)
                except ContextFileNotFoundException:
                    pass

        # imports added by eg. environment variable
        if additional_imports:
            ctx = ApplicationContext.merge(ctx, self._load_context_from_list_of_imports(additional_imports))

        ctx.io = self._io
        ctx.compile()

        return ctx


def distinct_imports(file_path: str, imported: List[Union[TaskDeclaration, TaskAliasDeclaration]]) \
        -> Tuple[List[TaskDeclaration], List[TaskAliasDeclaration]]:

    """Separates TaskDeclaration and TaskAliasDeclaration into separate lists, doing validation by the way

    :url: https://github.com/riotkit-org/riotkit-do/issues/33
    """

    aliases = []
    imports = []

    for declaration in imported:
        if isinstance(declaration, TaskAliasDeclaration):
            aliases.append(declaration)
        elif isinstance(declaration, TaskDeclaration):
            imports.append(declaration)
        else:
            raise ContextException('"imports()" from "%s" contains invalid type declaration "%s"' % (
                file_path, str(declaration)
            ))

    return imports, aliases
