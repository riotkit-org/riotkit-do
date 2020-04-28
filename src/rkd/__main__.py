#!/usr/bin/env python3

import sys
from .argparsing import CommandlineParsingHelper, TaskArguments
from .context import ContextFactory, Context
from .task import TaskGroup


class RiotKitDoApplication:
    _ctx: Context
    _tasks_to_execute = []

    def main(self):

        # load context of components
        self._ctx = ContextFactory().create_unified_context()

        # iterate over each task, parse commandline arguments
        requested_tasks = CommandlineParsingHelper.create_grouped_arguments(sys.argv[1:])

        for task_request in requested_tasks:
            self._resolve(task_request)

    def _resolve(self, task_request: TaskArguments):
        declaration = self._ctx.find_task_by_name(task_request.name())
        task = declaration.get_task_to_execute()

        if isinstance(task, TaskGroup):
            print(task)


if __name__ == '__main__':
    app = RiotKitDoApplication()
    app.main()
