#!/usr/bin/env python3

from typing import List

from rkd.core.api.inputoutput import IO
from rkd.core.api.testing import BasicTestingCase
from rkd.core.context import ApplicationContext
from rkd.core.resolver import TaskResolver
from rkd.core.resolver_result import ResolvedTaskBag
from rkd.core.standardlib.shell import ShellCommandTask
from rkd.core.api.syntax import TaskDeclaration, TaskAliasDeclaration
from rkd.core.argparsing.model import TaskArguments, ArgumentBlock
from rkd.core.aliasgroups import parse_alias_groups_from_env


def repr_list_as_invoked_task(bag: ResolvedTaskBag) -> List[str]:
    return list(map(
        lambda declaration: declaration.repr_as_invoked_task,
        bag.scheduled_declarations_to_run
    ))


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
            directory='',
            subprojects=[],
            workdir='',
            project_prefix=''
        )
        context.io = IO()
        context.compile()

        # action
        resolver = TaskResolver(context, [])
        resolved_tasks = resolver.resolve(
            [ArgumentBlock([':test', '--short']).clone_with_tasks([TaskArguments(':test', ['--short'])])],
        )

        self.assertEqual(
            [':sh -c uname -a --short', ':sh -c ps aux --short'],
            repr_list_as_invoked_task(resolved_tasks)
        )

    def test_resolves_regular_task(self):
        """Checks that :sh resolution works fine"""

        context = ApplicationContext(
            tasks=[TaskDeclaration(ShellCommandTask())],
            aliases=[],
            directory='',
            subprojects=[],
            workdir='',
            project_prefix=''
        )
        context.io = IO()
        context.compile()

        resolver = TaskResolver(context, [])
        resolved_tasks = resolver.resolve([ArgumentBlock([':sh']).clone_with_tasks([TaskArguments(':sh', [])])])

        self.assertEqual(':sh', resolved_tasks.scheduled_declarations_to_run[0].repr_as_invoked_task)

    def test_resolves_aliased_task(self):
        """Checks 'alias groups' feature about to resolve some group name to other group name

        Example:
            :bella-ciao:sh -> :sh
        """

        context = ApplicationContext(
            tasks=[TaskDeclaration(ShellCommandTask())],
            aliases=[],
            directory='',
            subprojects=[],
            workdir='',
            project_prefix=''
        )
        context.io = IO()
        context.compile()

        resolver = TaskResolver(context, parse_alias_groups_from_env(':bella-ciao->'))
        resolved_tasks = resolver.resolve([
            ArgumentBlock([':bella-ciao:sh']).clone_with_tasks([TaskArguments(':bella-ciao:sh', [])])
        ])

        self.assertEqual(':sh', resolved_tasks.scheduled_declarations_to_run[0].repr_as_invoked_task)
