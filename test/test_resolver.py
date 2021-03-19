#!/usr/bin/env python3

from typing import Union

from rkd.api.inputoutput import IO

from rkd.api.testing import BasicTestingCase
from rkd.context import ApplicationContext
from rkd.resolver import TaskResolver
from rkd.standardlib.shell import ShellCommandTask
from rkd.syntax import TaskDeclaration, GroupDeclaration, TaskAliasDeclaration
from rkd.argparsing.model import TaskArguments, ArgumentBlock
from rkd.aliasgroups import parse_alias_groups_from_env


class TestResolver(BasicTestingCase):
    def test_resolves_two_same_type_tasks_group_into_regular_tasks(self):
        """
        Tests that we can make an alias :test that will execute two times :sh command, but with different parameters
        :return:
        """

        # test data
        context = ApplicationContext(
            tasks=[TaskDeclaration(ShellCommandTask())],
            aliases=[
                # note: there is 2x :sh with DIFFERENT arguments
                TaskAliasDeclaration(':test', [':sh', '-c', 'uname -a', ':sh', '-c', 'ps aux'],
                                     description='Task for testing')
            ],
            directory=''
        )
        context.io = IO()
        context.compile()

        # results collection
        result_tasks = []

        def assertion_callback(declaration: TaskDeclaration,
                               task_num: int,
                               parent: Union[GroupDeclaration, None] = None,
                               args: list = []):
            result_tasks.append(declaration.to_full_name() + ' ' + (' '.join(declaration.get_args())))

        # action
        resolver = TaskResolver(context, [])
        resolver.resolve(
            [ArgumentBlock([':test', '--short']).clone_with_tasks([TaskArguments(':test', ['--short'])])],
            assertion_callback
        )

        self.assertEqual([':sh -c uname -a', ':sh -c ps aux'], result_tasks)

    def test_resoles_regular_task(self):
        """Checks that :sh resolution works fine"""

        context = ApplicationContext(
            tasks=[TaskDeclaration(ShellCommandTask())],
            aliases=[],
            directory=''
        )
        context.io = IO()
        context.compile()

        result_tasks = []

        def assertion_callback(declaration: TaskDeclaration,
                               task_num: int,
                               parent: Union[GroupDeclaration, None] = None,
                               args: list = []):
            result_tasks.append(declaration.to_full_name())

        resolver = TaskResolver(context, [])
        resolver.resolve([ArgumentBlock([':sh']).clone_with_tasks([TaskArguments(':sh', [])])], assertion_callback)

        self.assertEqual([':sh'], result_tasks)

    def test_resolves_aliased_task(self):
        """Checks 'alias groups' feature about to resolve some group name to other group name

        Example:
            :bella-ciao:sh -> :sh
        """

        context = ApplicationContext(
            tasks=[TaskDeclaration(ShellCommandTask())],
            aliases=[],
            directory=''
        )
        context.io = IO()
        context.compile()
        result_tasks = []

        def assertion_callback(declaration: TaskDeclaration,
                               task_num: int,
                               parent: Union[GroupDeclaration, None] = None,
                               args: list = []):
            result_tasks.append(declaration.to_full_name())

        resolver = TaskResolver(context, parse_alias_groups_from_env(':bella-ciao->'))
        resolver.resolve([ArgumentBlock([':bella-ciao:sh'])
                         .clone_with_tasks([TaskArguments(':bella-ciao:sh', [])])], assertion_callback)

        self.assertEqual([':sh'], result_tasks)
