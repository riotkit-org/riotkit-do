"""
Static analysis for Python written code
=======================================

"""

import ast
import inspect
from textwrap import dedent
from typing import List, Union, Dict


class FindCalls(ast.NodeVisitor):
    __slots__ = ['__self_calls', '__self_attributes']
    __self_calls: Dict[str, bool]
    __self_attributes: Dict[str, bool]

    def __init__(self):
        self.__self_calls = {}
        self.__self_attributes = {}

    def visit_Assign(self, node: ast.Assign):
        """
        Find attributes assign on "self"

        :param node:
        :return:
        """

        for target in node.targets:
            target: ast.Attribute

            if not isinstance(target, ast.Attribute):
                continue

            value: Union[ast.Name, any] = target.value

            if value.id == 'self':
                self.__self_attributes[target.attr] = True

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """
        Find method calls on "self" object
        :param node:
        :return:
        """

        attribute: Union[ast.Attribute, any, ast.Name] = node.func

        if isinstance(attribute, ast.Attribute):
            called_attribute_name = attribute.attr

            value = attribute.value

            if isinstance(value, ast.Name) and value.id == 'self':
                self.__self_calls[called_attribute_name] = True

        # visit the children
        self.generic_visit(node)
        
    @property
    def calls(self) -> List[str]:
        return list(self.__self_calls.keys())

    @property
    def assigns(self) -> List[str]:
        return list(self.__self_attributes.keys())


class NotAllowedUsagesReport(object):
    __slots__ = '__usages'
    __usages: List[str]

    def __init__(self, usages: List[str]):
        self.__usages = usages

    def __str__(self) -> str:
        return ', '.join(self.__usages)

    def has_any_not_allowed_usage(self) -> bool:
        return len(self.__usages) > 0


def analyze_allowed_usages(method, allow_list: List[str]) -> NotAllowedUsagesReport:
    """
    Analyzes if code does not contain not allowed usages of method/attributes calling.
    Returns NotAllowedUsagesReport instance

    :param method:
    :param allow_list:
    :return: NotAllowedUsagesReport
    """

    # prepare and parse source code
    source_code_lines = inspect.getsource(method).split("\n")
    del source_code_lines[0]
    source_code = dedent("\n".join(source_code_lines))
    tree = ast.parse(source_code)

    fc = FindCalls()
    fc.visit(tree)

    actual_usage = fc.assigns + fc.calls
    not_allowed: List[str] = []

    for used in actual_usage:
        if used not in allow_list:
            not_allowed.append(used)

    return NotAllowedUsagesReport(not_allowed)
