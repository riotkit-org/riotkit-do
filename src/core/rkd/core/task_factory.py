import importlib
from argparse import ArgumentParser
from types import FunctionType
from typing import Dict, Type, Tuple, Optional, List, Union
from rkd.core.api.contract import TaskInterface, ExtendableTaskInterface, ExecutionContext, ArgumentEnv
from rkd.core.api.inputoutput import ReadableStreamType, IO
from rkd.core.api.syntax import TaskDeclaration
from rkd.core.dto import ParsedTaskDeclaration, StaticFileContextParsingResult
from rkd.core.exception import TaskFactoryException
from rkd.core.taskutil import evaluate_code

ALLOWED_METHODS_TO_DEFINE = [
    'configure', 'stdin', 'inner_execute', 'configure_argparse', 'compile', 'execute', 'get_steps',
    'get_name', 'get_description', 'get_group_name', 'get_declared_envs'
]

ALLOWED_METHODS_TO_INHERIT = [
    'configure', 'inner_execute', 'configure_argparse', 'compile', 'execute', 'get_steps',
    'get_name', 'get_description', 'get_group_name', 'get_declared_envs'
]

METHODS_THAT_RETURNS_NON_BOOLEAN_VALUES = ['steps', 'get_name', 'get_description']

MARKER_SKIP_PARENT_CALL = 'no_parent_call_wrapper'
MARKER_CALL_PARENT_FIRST = 'call_parent_first_wrapper'

ALLOWED_MARKERS = [
    MARKER_SKIP_PARENT_CALL, MARKER_CALL_PARENT_FIRST
]

MARKERS_MAPPING = {
    'no_parent_call': MARKER_SKIP_PARENT_CALL,
    'call_parent_first': MARKER_CALL_PARENT_FIRST
}


class TaskFactory(object):
    """
    Produces TaskInterface from FunctionType, YAML, etc.
    ----------------------------------------------------

    Responsibility:
        - From a parsed and pre-validated static declarations can create a class with methods using a proxy
        - From a function with inner functions can create a class with methods using a proxy
    """

    @classmethod
    def create_task_with_declaration_after_parsing(cls, source: ParsedTaskDeclaration,
                                                   parsing_context: StaticFileContextParsingResult,
                                                   io: IO) -> TaskDeclaration:
        """
        Creates executable methods from already prepared code (parsed from a document eg. YAML)
        as a result _create_task() is called to construct dynamically a class with prepared methods

        :param source:
        :param parsing_context:
        :param io: Used ONLY for task creation stage. On runtime each task is given its own IO() instance
        :return: TaskDeclaration
        """

        # build methods list
        methods = {}

        # all overridden methods: those are not generated fully automatically for purpose of the static analysis
        #                         so the interpreter will not be lost, and stacktrace could be more readable
        #                         as we are doing some meta programming there

        # <python executable code methods>
        if source.inner_execute is not None:
            def inner_execute(self, ctx: ExecutionContext) -> bool:
                return evaluate_code(
                    code=source.inner_execute,
                    full_task_name=source.name,
                    returns_boolean=True,
                    ctx=ctx,
                    self=self,
                    io=io
                )

            methods['inner_execute'] = inner_execute

        if source.execute is not None:
            def execute(self, ctx: ExecutionContext) -> bool:
                return evaluate_code(
                    code=source.execute,
                    full_task_name=source.name,
                    returns_boolean=True,
                    ctx=ctx,
                    self=self,
                    io=io
                )

            methods['execute'] = execute

        if source.configure is not None:
            def execute(self, ctx: ExecutionContext) -> bool:
                return evaluate_code(
                    code=source.configure,
                    full_task_name=source.name,
                    returns_boolean=False,
                    ctx=ctx,
                    self=self,
                    io=io
                )

            methods['configure'] = execute

        # </python executable code methods>

        # <string/list methods>
        if source.task_input:
            def stdin(self):
                return source.task_input

            stdin.marker = MARKER_SKIP_PARENT_CALL
            methods['stdin'] = stdin

        if source.steps:
            def steps(self):
                return source.steps

            steps.marker = MARKER_SKIP_PARENT_CALL
            methods['get_steps'] = steps

        if source.group:
            def group(self):
                return source.group

            group.marker = MARKER_SKIP_PARENT_CALL
            methods['get_group_name'] = group
        # </string/list methods>

        # <specific syntax: argparse args and kwargs>
        if source.argparse_options:
            def configure_argparse(self, parser: ArgumentParser):
                for argument in source.argparse_options:
                    parser.add_argument(*argument.args, **argument.kwargs)

            # todo: test case - are arguments inherited from parent?
            methods['configure_argparse'] = configure_argparse

        # </specific syntax: argparse args and kwargs>

        # <decorators appended to methods - one decorator only allowed>
        # append decorators to all methods
        for method_name, decorator in source.method_decorators.items():
            if method_name in methods:
                methods[method_name].__setattr__('marker', MARKERS_MAPPING[decorator])

        # append empty decorators if no decorator was used
        for method_name, method in methods.items():
            try:
                method.marker
            except AttributeError:
                method.__setattr__('marker', None)

        # </decorators appended to methods - one decorator only allowed>

        # import type (class) that will be extended - TaskInterface to extend
        extended_class = cls._import_type(source.task_type)

        # build an environment hierarchy, task local environment should always overwrite the global and system scope
        environment = {}
        environment.update(cls._unpack_envs(extended_class.get_declared_envs()))  # prepend parent task environment
        environment.update(parsing_context.global_environment)                # add global environment (whole document)
        environment.update(source.environment)                                # add THIS TASK-defined environment

        # allow all used environment variables in YAML document declaration
        def get_declared_envs(self):
            return environment

        # we do not call parent actually, as we already merged the dicts in {environment} variable
        get_declared_envs.marker = MARKER_SKIP_PARENT_CALL
        methods['get_declared_envs'] = get_declared_envs

        # dummy task for static analysis
        def task_created_from_yaml_document():
            pass

        task, stdin_method = cls._create_task(
            extended_class=extended_class,
            exports=methods,
            func=task_created_from_yaml_document,
            name=source.name
        )

        declaration_methods = {}

        if stdin_method:
            declaration_methods['get_input'] = stdin_method

        declaration_type = type(
            f'TaskDeclaration_generated_{source.task_type}', (TaskDeclaration,), declaration_methods
        )
        declaration = declaration_type(
            task=task,
            env=environment,
            workdir=source.workdir,
            internal=source.internal,
            name=source.group + source.name
        )

        return declaration

    @classmethod
    def create_task_from_func(cls, func: FunctionType, name: Optional[str] = None) \
            -> Tuple[TaskInterface, Optional[FunctionType]]:
        """
        Create a class that will inherit from base task (taken from 'extends' type hint)
        and all returned inner methods of func() will cover new class methods (with super() calls at the beginning)

        :param func:
        :param name:
        :return: Tuple of [task, stdin() method]
        """

        try:
            extended_class: Type = func.__dict__.get('extends')

        except KeyError:
            raise TaskFactoryException.from_missing_extends(func)

        if not issubclass(extended_class, ExtendableTaskInterface):
            raise TaskFactoryException.from_not_extendable_base_task(extended_class, func)

        exports = cls._extract_exported_methods(func)

        return cls._create_task(
            extended_class=extended_class,
            exports=exports,
            func=func,
            name=name
        )

    @classmethod
    def _create_task(cls, extended_class: Type[TaskInterface], exports: Dict[str, FunctionType],
                     func: Optional[FunctionType], name: str) -> Tuple[TaskInterface, Optional[FunctionType]]:

        """
        Creates a Task from just a dictionary of inner methods (or lambdas) and a TaskInterface type

        :param extended_class:
        :param exports:
        :param func:
        :param name:
        :return:
        """

        cls._validate_methods_allowed(list(exports.keys()), ALLOWED_METHODS_TO_DEFINE,
                                      after_filtering=False, func=func)

        # make get_name() return same value as TaskDeclaration does (IMPORTANT for compilation-time created tasks)
        if name:
            def get_name(self):
                return name

            get_name.marker = None
            exports['get_name'] = get_name

        if 'execute' in exports:
            exports['execute'] = exports['execute']
            del exports['execute']

        if 'inner_execute' in exports:
            exports['inner_execute'] = exports['inner_execute']
            del exports['inner_execute']

        # move from dict to locals(), so the validation could not reach it - it is on declaration level, not task level
        stdin_method = None
        if 'stdin' in exports:
            stdin_method = exports['stdin']
            del exports['stdin']

        cls._validate_methods_allowed(list(exports.keys()), ALLOWED_METHODS_TO_INHERIT,
                                      after_filtering=True, func=func)

        methods = cls._create_inheritance_proxy(exports, extended_class)
        task = type(f'Extended_{func.__name__}_{extended_class.__name__}', (extended_class,), methods)()

        # stdin method is inherited at TaskDeclaration level, not TaskInterface
        if stdin_method:
            stdin_export = stdin_method

            def stdin_readable_stream(self):
                return ReadableStreamType(stdin_export(self=task))

            stdin_method = stdin_readable_stream

        return task, stdin_method

    @staticmethod
    def _import_type(class_full_path: str) -> Type[TaskInterface]:
        """
        Import a TaskInterface implementation from a full import path eg. rkd.core.standardlib.sh.ShellTask

        :param class_full_path:
        :return:
        """

        split = class_full_path.split('.')
        class_name = split[-1]
        import_path = '.'.join(split[:-1])

        try:
            module = importlib.import_module(import_path)
            imported_type: Type[TaskInterface] = module.__getattribute__(class_name)
        except ModuleNotFoundError:
            raise Exception(f'Cannot import {class_full_path}. No such class? Check if package is installed in current environment')

        if not isinstance(imported_type, type):
            # @todo: Use better exception
            raise Exception(f'Cannot import {class_full_path}. No such class? Check if package is installed in current environment')

        return imported_type

    @classmethod
    def _unpack_envs(cls, environment: Dict[str, Union[str, ArgumentEnv]]):
        """
        From environment declaration make list of environment with default values

        :param environment:
        :return:
        """

        copy = {}

        for name, value in environment.items():
            if isinstance(value, ArgumentEnv):
                value = value.default

            copy[name] = value

        return copy


    @classmethod
    def _validate_methods_allowed(cls, methods: List[str], allowed: List[str],
                                  after_filtering: bool, func: FunctionType = None):
        for method in methods:
            if method not in allowed:
                if after_filtering:
                    raise TaskFactoryException.from_method_not_allowed_to_be_inherited(method, func)
                else:
                    raise TaskFactoryException.from_method_not_allowed_to_be_defined_for_inheritance(method, func)

    @classmethod
    def _create_inheritance_proxy(cls, attributes: Dict[str, FunctionType],
                                  extended_class: Type[TaskInterface]) -> Dict[str, FunctionType]:
        """
        Create methods that will inherit call to parent `super()`

        :param attributes:
        :param extended_class:
        :return:
        """

        inherited_attributes = {}

        for name, method in attributes.items():
            method: FunctionType

            inherited_attributes[name] = cls._create_proxy_method(
                method,
                extended_class.__dict__.get(name)
            )

        return inherited_attributes

    @classmethod
    def _create_proxy_method(cls, current_method, parent_method):
        def _inner_proxy_method(self, *args, **kwargs):
            """
            Proxy method to call method + parent in proper order

            :param self:
            :param args:
            :param kwargs:
            :return:
            """

            # do not call parent() at all
            if current_method.marker == MARKER_SKIP_PARENT_CALL:
                return current_method(self, *args, **kwargs)

            # call parent() first
            elif current_method.marker == MARKER_CALL_PARENT_FIRST:
                parent_result = parent_method(self, *args, **kwargs) if parent_method else True
                current_result = current_method(self, *args, **kwargs)

            # call children() then parent()
            else:
                current_result = current_method(self, *args, **kwargs)
                parent_result = parent_method(self, *args, **kwargs) if parent_method else True

            if current_method.__name__ in METHODS_THAT_RETURNS_NON_BOOLEAN_VALUES:
                return current_result

            return parent_result and current_result

        return _inner_proxy_method

    @classmethod
    def _extract_exported_methods(cls, func: FunctionType) -> Dict[str, FunctionType]:
        exported = {}

        for function in func():
            function.marker = None

            # interpret the decorator
            if function.__name__ in MARKER_CALL_PARENT_FIRST:
                marker = function.__name__
                function = function()
                function.marker = marker

            exported[function.__name__] = function

        return exported
