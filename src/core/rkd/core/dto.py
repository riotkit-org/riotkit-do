"""
Internal Data Transfer Objects used inside RKD
==============================================

Place for internal types such as named tuples returning named values.
All types that are present in the tasks should go into the rkd.core.api.contract (as a part of RKD API)
"""
from dataclasses import dataclass
from typing import List, Union, Dict
from rkd.core.api.contract import ArgparseArgument
from rkd.core.api.syntax import TaskDeclaration, TaskAliasDeclaration


@dataclass
class ParsedTaskDeclaration(object):
    """
    Represents a parsed task declaration from any source - YAML/other
    it is a raw declaration without any bound methods or closures

    TaskFactory responsibility is to understand this object and create a TaskDeclaration(TaskInterface implementation)
    basing on this object.
    """

    # task attributes
    name: str
    group: str
    description: str
    argparse_options: List[ArgparseArgument]
    task_type: str

    # declaration attributes
    become: str
    workdir: str
    internal: bool

    # methods source code
    steps: List[str]  # source code as a list in possibly different languages
    execute: str
    task_input: str

    # environment declared for THIS task, should NOT include GLOBAL (document) ENVIRONMENT
    # and should NOT include SYSTEM ENVIRONMENT
    environment: Dict[str, any]


@dataclass
class StaticFileContextParsingResult(object):
    """
    Result of parsing a single context - a static file (eg. YAML/XML/etc. syntax)
    """

    imports: List[Union[TaskDeclaration, TaskAliasDeclaration]]
    parsed: List[ParsedTaskDeclaration]
    subprojects: List[str]

    # environment defined in scope of WHOLE document (YAML/XML/etc.) for all tasks
    # should NOT include a SYSTEM ENVIRONMENT
    global_environment: Dict[str, any]
