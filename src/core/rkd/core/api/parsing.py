import importlib
from types import FunctionType
from typing import List, Type

from rkd.core.api.contract import TaskInterface

from ..exception import ParsingException
from .syntax import TaskDeclaration


class SyntaxParsing(object):
    @staticmethod
    def parse_import_as_type(import_str: str) -> Type[TaskInterface]:
        """
        Import a Python class as a type

        Example: rkd.core.standardlib.jinja.FileRendererTask

        :param import_str:
        :return:
        """

        parts = import_str.split('.')
        class_name = parts[-1]
        import_path = '.'.join(parts[:-1])

        # importing just a full module name eg. "rkd_python"
        if len(parts) == 1:
            import_path = import_str
            class_name = 'imports'
        # Test if it's not a class name
        # In this case we treat is as a module and import an importing method imports()
        elif class_name.lower() == class_name:
            import_path += '.' + class_name
            class_name = 'imports'

        try:
            module = importlib.import_module(import_path)
        except ImportError as e:
            raise ParsingException.from_import_error(import_str, class_name, e)

        if class_name not in dir(module):
            raise ParsingException.from_class_not_found_in_module_error(import_str, class_name, import_path)

        return module.__getattribute__(class_name)

    @classmethod
    def parse_imports_by_list_of_classes(cls, classes_or_modules: List[str]) -> List[TaskDeclaration]:
        """
        Parses a List[str] of imports, like in YAML syntax.
        Produces a List[TaskDeclaration] with imported list of tasks.

        Could be used to import & validate RKD tasks.

        Examples:
            - rkd.core.standardlib
            - rkd.core.standardlib.jinja.FileRendererTask

        :raises ParsingException
        :return:
        """

        parsed: List[TaskDeclaration] = []

        for import_str in classes_or_modules:
            imported_type = cls.parse_import_as_type(import_str)

            if isinstance(imported_type, FunctionType):
                parsed += imported_type()
            else:
                parsed.append(TaskDeclaration(imported_type()))

        return parsed
