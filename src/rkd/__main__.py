#!/usr/bin/env python3

import sys
from .argparsing import CommandlineParsingHelper
from .context import ContextFactory, Context
from .resolver import TaskResolver
from .validator import TaskDeclarationValidator
from .executor import OneByOneTaskExecutor


class RiotKitDoApplication:
    _ctx: Context
    _tasks_to_execute = []

    def main(self):

        # load context of components
        self._ctx = ContextFactory().create_unified_context()
        resolver = TaskResolver(self._ctx)
        executor = OneByOneTaskExecutor(self._ctx)

        # iterate over each task, parse commandline arguments
        requested_tasks = CommandlineParsingHelper.create_grouped_arguments([':init'] + sys.argv[1:])

        # validate all tasks
        resolver.resolve(requested_tasks, TaskDeclarationValidator.assert_declaration_is_valid)

        # execute all tasks
        resolver.resolve(requested_tasks, executor.execute)

        # todo: Collect tasks status codes and do sys.exit() here - executor can know the code


if __name__ == '__main__':
    app = RiotKitDoApplication()
    app.main()
