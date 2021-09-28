
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
from .api.syntax import TaskDeclaration, parse_path_into_subproject_prefix, ExtendedTaskDeclaration, Pipeline, \
    DeclarationBelongingToPipeline
from .api.syntax import TaskAliasDeclaration
from .api.syntax import GroupDeclaration
from .api.contract import ContextInterface
from .api.parsing import SyntaxParsing
from .argparsing.parser import CommandlineParsingHelper
from .api.inputoutput import SystemIO
from .exception import TaskNotFoundException, BlockAlreadyConnectedException
from .exception import ContextFileNotFoundException
from .exception import PythonContextFileNotFoundException
from .exception import NotImportedClassException
from .exception import ContextException
from .execution.lifecycle import CompilationLifecycleEvent
from .packaging import get_user_site_packages
from .task_factory import TaskFactory
from .yaml_context import StaticFileSyntaxInterpreter
from .dto import StaticFileContextParsingResult
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
    _task_aliases: Dict[str, Pipeline]
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
                 aliases: List[Pipeline],
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
            raise TaskNotFoundException(('Task "%s" is not defined. Check the import, definition '
                                         'and typed command.') % name)

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

    def _add_pipeline(self, pipeline: Pipeline, parent_ctx: Optional['ApplicationContext'] = None) -> None:
        if not parent_ctx:
            parent_ctx = self

        if parent_ctx.workdir and parent_ctx.project_prefix:
            pipeline = pipeline.as_part_of_subproject(parent_ctx.workdir, subproject_name=parent_ctx.project_prefix)

        self._task_aliases[pipeline.get_name()] = pipeline

    def _resolve_pipeline(self, name: str, pipeline: Pipeline, depth: int = 0) -> GroupDeclaration:
        """
        Parse commandline args to fetch list of tasks to join into a group

        Produced result will be available to fetch via find_task_by_name()
        This brings a support for "Pipelines" (also called Task Aliases)

        Pipelines inherited in Pipelines will be resolved as one long set of tasks with merged
        blocks, arguments and environment.

        Scenario:
            Given as input a list of chained tasks eg. ":task1 :task2 --arg1=value :task3"
            Expected to resolve as TaskDeclaration objects with injected arguments
        """

        cmdline_parser = CommandlineParsingHelper(self.io)

        self.io.internal(f'Resolving pipeline {pipeline} (depth={depth})')
        args = cmdline_parser.create_grouped_arguments(pipeline.get_arguments())
        resolved_tasks = []

        for block in args:
            for argument_group in block.tasks():
                is_a_sub_pipeline = argument_group.name() in self._task_aliases

                # inherit tasks from Pipeline defined inside currently processed Pipeline (do a recursion)
                if is_a_sub_pipeline:
                    inherited_pipeline = self._resolve_pipeline(
                        argument_group.name(),
                        self._task_aliases[argument_group.name()],
                        depth=depth + 1
                    )
                    resolved_declarations = inherited_pipeline.get_declarations()

                # just include Tasks for this Pipeline
                else:
                    resolved_declarations = [self.find_task_by_name(argument_group.name())]

                # create wrappers that will contain inherited environment, arguments etc.
                for resolved_declaration in resolved_declarations:
                    resolved_declaration: Union[TaskDeclaration, DeclarationBelongingToPipeline]

                    pipeline_env = pipeline.get_env()
                    pipeline_env['RKD_PIPELINE_DEPTH'] = str(depth)

                    if isinstance(resolved_declaration, TaskDeclaration):
                        pipeline_partial = DeclarationBelongingToPipeline(
                            declaration=resolved_declaration,
                            runtime_arguments=argument_group.args(),
                            parent=None,
                            env=pipeline_env,
                            user_overridden_env=pipeline.get_user_overridden_envs()
                        )
                    else:
                        # we have a Pipeline in Pipeline that needs to have Tasks merged
                        resolved_declaration.append(
                            runtime_arguments=argument_group.args(),
                            env=pipeline_env,
                            user_overridden_env=pipeline.get_user_overridden_envs()
                        )

                        pipeline_partial = resolved_declaration

                    pipeline_partial.connect_block(block)

                    self.io.internal(f'Resolved pipeline {pipeline_partial} inside {block} (depth={depth})')
                    resolved_tasks.append(pipeline_partial)

        # release all collected Tasks as a group with blocks connected, environment and arguments merged
        return GroupDeclaration(name, resolved_tasks, pipeline.get_description())

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

    _task_factory: TaskFactory
    _io: SystemIO

    def __init__(self, io: SystemIO):
        self._io = io
        self._task_factory = TaskFactory(io)

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
            contexts += self._expand_contexts(self._load_from_static_file(path, 'makefile.yaml',
                                                                          workdir=workdir,
                                                                          prefix=subproject))

        if os.path.isfile(path + '/makefile.yml'):
            contexts += self._expand_contexts(self._load_from_static_file(path, 'makefile.yml',
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

    def _load_from_static_file(self, path: str, filename: str, workdir: str, prefix: str) -> ApplicationContext:
        """
        Load Tasks and build an ApplicationContext basing on a static configuration file (eg. YAML)

        :param path:
        :param filename:
        :param workdir:
        :param prefix:
        :return:
        """

        makefile_path = path + '/' + filename

        with open(makefile_path, 'rb') as handle:
            parsing_result: StaticFileContextParsingResult = StaticFileSyntaxInterpreter(self._io, YamlFileLoader([]))\
                .parse(
                    content=handle.read().decode('utf-8'),
                    rkd_path=path,
                    file_path=makefile_path
                )

            imported = parsing_result.imports

            for parsed in parsing_result.parsed:
                imported.append(self._task_factory.create_task_with_declaration_after_parsing(parsed, parsing_result))

            imported = unpack_extended_task_declarations(imported, self._task_factory)

            # Issue 33: Support mixed declarations in imports()
            imports, aliases = distinct_imports(makefile_path, imported)

            self._io.internal(
                f'Building context from YAML workdir={workdir}, project_prefix={prefix}, directory={path}'
            )

            return ApplicationContext(tasks=imports, aliases=aliases, directory=path,
                                      subprojects=parsing_result.subprojects, workdir=workdir, project_prefix=prefix)

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
        imports, aliases = distinct_imports(
            makefile_path,
            unpack_extended_task_declarations(makefile.IMPORTS, self._task_factory) if "IMPORTS" in dir(makefile) else []
        )
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


def unpack_declaration(declaration: Union[TaskDeclaration, ExtendedTaskDeclaration],
                       task_factory: TaskFactory) -> TaskDeclaration:
    """
    Converts ExtendedTaskDeclaration into a regular TaskDeclaration.
    Existing TaskDeclarations are not touched.

    :param declaration:
    :param task_factory:
    :return:
    """

    if isinstance(declaration, ExtendedTaskDeclaration):
        task, stdin = task_factory.create_task_from_func(declaration.func, name=declaration.name)

        return declaration.create_declaration(task, stdin)

    return declaration


def unpack_extended_task_declarations(declarations: List[Union[TaskDeclaration, ExtendedTaskDeclaration]],
                                      task_factory: TaskFactory) -> List[TaskDeclaration]:

    return list(map(lambda x: unpack_declaration(x, task_factory), declarations))


def distinct_imports(file_path: str, imported: List[Union[TaskDeclaration, TaskAliasDeclaration, Pipeline]]) \
        -> Tuple[List[TaskDeclaration], List[Union[Pipeline, TaskAliasDeclaration]]]:

    """Separates TaskDeclaration and TaskAliasDeclaration into separate lists, doing validation by the way

    :url: https://github.com/riotkit-org/riotkit-do/issues/33
    """

    aliases = []
    imports = []

    for declaration in imported:
        if isinstance(declaration, TaskAliasDeclaration) or isinstance(declaration, Pipeline):
            aliases.append(declaration)
        elif isinstance(declaration, TaskDeclaration):
            imports.append(declaration)
        else:
            raise ContextException('"imports()" from "%s" contains invalid type declaration "%s"' % (
                file_path, str(declaration)
            ))

    return imports, aliases
