from inspect import signature as get_signature
from types import FunctionType
from typing import Dict, Type, Tuple, Optional, List
from rkd.core.api.contract import TaskInterface
from rkd.core.api.inputoutput import ReadableStreamType
from rkd.core.exception import TaskFactoryException


class TaskFactory(object):
    """
    Produces TaskInterface from FunctionType, YAML, etc.
    """

    ALLOWED_METHODS_TO_DEFINE = [
        'configure', 'stdin', 'inner_execute'
    ]

    ALLOWED_METHODS_TO_INHERIT = [
        'configure', 'inner_execute'
    ]

    MARKER_SKIP_PARENT_CALL = 'no_parent_call_wrapper'
    MARKER_CALL_PARENT_FIRST = 'call_parent_first_wrapper'

    ALLOWED_MARKERS = [
        MARKER_SKIP_PARENT_CALL, MARKER_CALL_PARENT_FIRST
    ]

    @classmethod
    def create_task_from_func(cls, func: FunctionType) -> Tuple[TaskInterface, Optional[FunctionType]]:
        """
        Create a class that will inherit from base task (taken from 'extends' type hint)
        and all returned inner methods of func() will cover new class methods (with super() calls at the beginning)

        :param func:
        :return: Tuple of [task, stdin() method]
        """

        try:
            extended_class = func.__dict__.get('extends')

        except KeyError:
            raise TaskFactoryException.from_missing_extends(func)

        stdin_method = None
        exports = cls._extract_exported_methods(func)

        cls._validate_methods_allowed(list(exports.keys()), cls.ALLOWED_METHODS_TO_DEFINE, after_filtering=False)

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

        cls._validate_methods_allowed(list(exports.keys()), cls.ALLOWED_METHODS_TO_INHERIT, after_filtering=True)

        methods = cls._create_inheritance_proxy(exports, extended_class)
        task = type(f'Extended_{func.__name__}_{extended_class.__name__}', (extended_class,), methods)()

        return task, stdin_method

    @classmethod
    def _validate_methods_allowed(cls, methods: List[str], allowed: List[str], after_filtering: bool):
        for method in methods:
            if method not in allowed:
                if after_filtering:
                    raise TaskFactoryException.from_method_not_allowed_to_be_inherited(method)
                else:
                    raise TaskFactoryException.from_method_not_allowed_to_be_defined_for_inheritance(method)

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
            if current_method.marker == cls.MARKER_SKIP_PARENT_CALL:
                return current_method(self, *args, **kwargs)

            # call parent() first
            elif current_method.marker == cls.MARKER_CALL_PARENT_FIRST:
                parent_result = parent_method(self, *args, **kwargs)
                current_result = current_method(self, *args, **kwargs)

            # call children() then parent()
            else:
                current_result = current_method(self, *args, **kwargs)
                parent_result = parent_method(self, *args, **kwargs)

            return parent_result and current_result

        return _inner_proxy_method

    @classmethod
    def _extract_exported_methods(cls, func: FunctionType) -> Dict[str, FunctionType]:
        exported = {}

        for function in func():
            function.marker = None

            # interpret the decorator
            if function.__name__ in cls.MARKER_CALL_PARENT_FIRST:
                marker = function.__name__
                function = function()
                function.marker = marker

            exported[function.__name__] = function

        return exported
