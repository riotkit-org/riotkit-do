#!/usr/bin/env python3

from typing import List


class TaskArguments:
    _name: str
    _args: list

    def __init__(self, task_name: str, args: list):
        self._name = task_name
        self._args = args

    def __repr__(self):
        return 'Task<%s (%s)>' % (self._name, str(self._args))

    def name(self):
        return self._name

    def args(self):
        return self._args


class CommandlineParsingHelper:
    """
    Extends argparse functionality by grouping arguments into tasks -> tasks arguments
    """

    @staticmethod
    def create_grouped_arguments(commandline: List[str]) -> List[TaskArguments]:
        current_group_elements = []
        current_task_name = 'rkd:initialize'
        tasks = []
        cursor = -1
        max_cursor = len(commandline)

        for part in commandline:
            cursor += 1

            is_flag = part[0:1] == "-"
            is_task = part[0:1] == ":"
            previous_is_flag = commandline[cursor-1][0:1] == "-" if cursor >= 1 else False

            # option name or flag
            if is_flag:
                current_group_elements.append(part)

            # option value
            elif not is_flag and previous_is_flag and not is_task:
                current_group_elements.append(part)

            # new task
            elif is_task:
                if current_task_name != 'rkd:initialize':
                    tasks.append(TaskArguments(current_task_name, current_group_elements))

                current_task_name = part
                current_group_elements = []
            else:
                raise Exception('Unknown task "%s"' % part)

            if cursor + 1 == max_cursor:
                tasks.append(TaskArguments(current_task_name, current_group_elements))

        return tasks
