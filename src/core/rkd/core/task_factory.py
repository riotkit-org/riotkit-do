from types import FunctionType
from typing import Dict, Type, Tuple, Optional, List
from rkd.core.api.contract import TaskInterface, ExtendableTaskInterface
from rkd.core.api.inputoutput import ReadableStreamType, get_environment_copy
from rkd.core.dto import ParsedTaskDeclaration, StaticFileContextParsingResult
from rkd.core.exception import TaskFactoryException


ALLOWED_METHODS_TO_DEFINE = [
    'configure', 'stdin', 'inner_execute', 'configure_argparse', 'compile', 'execute', 'get_steps',
    'get_name', 'get_description'
]

ALLOWED_METHODS_TO_INHERIT = [
    'configure', 'inner_execute', 'configure_argparse', 'compile', 'execute', 'get_steps',
    'get_name', 'get_description'
]

METHODS_THAT_RETURNS_NON_BOOLEAN_VALUES = ['get_steps', 'get_name', 'get_description']

MARKER_SKIP_PARENT_CALL = 'no_parent_call_wrapper'
MARKER_CALL_PARENT_FIRST = 'call_parent_first_wrapper'

ALLOWED_MARKERS = [
    MARKER_SKIP_PARENT_CALL, MARKER_CALL_PARENT_FIRST
]


class TaskFactory(object):
    """
    Produces TaskInterface from FunctionType, YAML, etc.
    ----------------------------------------------------

    Responsibility:
        - From a parsed and pre-validated static declarations can create a class with methods using a proxy
        - From a function with inner functions can create a class with methods using a proxy
    """

    @classmethod
    def create_task_after_parsing(cls, source: ParsedTaskDeclaration, parsing_context: StaticFileContextParsingResult):

        # build an environment hierarchy, task local environment should always overwrite the global and system scope
        environment = {}
        environment.update(get_environment_copy())
        environment.update(parsing_context.global_environment)
        environment.update(source.environment)



        print('!!!', source)

        pass

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

        stdin_method = None
        exports = cls._extract_exported_methods(func)

        # @todo: Extract YAML-like syntax + description

        cls._validate_methods_allowed(list(exports.keys()), ALLOWED_METHODS_TO_DEFINE,
                                      after_filtering=False, func=func)

        # make get_name() return same value as TaskDeclaration does (IMPORTANT for compilation-time created tasks)
        if name:
            def get_name(self):
                return name

            get_name.marker = None
            exports['get_name'] = get_name

        # we do not support overriding of `execute()` method, but we do for `inner_execute()`
        if 'execute' in exports:
            exports['inner_execute'] = exports['execute']
            del exports['execute']

        # stdin method is inherited at TaskDeclaration level, not TaskInterface
        if 'stdin' in exports:
            stdin_export = exports['stdin']

            def stdin_readable_stream():
                return ReadableStreamType(stdin_export())

            stdin_method = stdin_readable_stream
            del exports['stdin']

        cls._validate_methods_allowed(list(exports.keys()), ALLOWED_METHODS_TO_INHERIT,
                                      after_filtering=True, func=func)

        methods = cls._create_inheritance_proxy(exports, extended_class)
        task = type(f'Extended_{func.__name__}_{extended_class.__name__}', (extended_class,), methods)()

        return task, stdin_method

    @classmethod
    def _validate_methods_allowed(cls, methods: List[str], allowed: List[str],
                                  after_filtering: bool, func: FunctionType):
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
