#!/usr/bin/env python3

from rkd.api.testing import BasicTestingCase
from rkd.standardlib import TasksListingTask
from rkd.test import get_test_declaration


class TestTasksListingTask(BasicTestingCase):
    def test_ljust_task_name(self):
        """Assert that the formatting is not breaking the description alignment
        The formatting instructions should not be considered by ljust. Only visible characters should be considered
        in padding with spaces"""

        # colored
        colored_declaration = get_test_declaration()
        colored_declaration.format_task_name = lambda text: "\x1B[93m" + text + "\x1B[0m"
        ljusted_colored = TasksListingTask.ljust_task_name(colored_declaration, ':general-strike')

        # not colored
        regular_declaration = get_test_declaration()
        regular_declaration.format_task_name = lambda text: text
        ljusted_regular = TasksListingTask.ljust_task_name(regular_declaration, ':general-strike')

        # assert: the coloring should not impact on the filling up size
        self.assertTrue(ljusted_colored.endswith((' ' * 35)), msg='Expected 35 spaces at the end (fill up)')
        self.assertTrue(ljusted_regular.endswith((' ' * 35)), msg='Expected 35 spaces at the end (fill up)')
