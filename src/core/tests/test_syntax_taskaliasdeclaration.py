#!/usr/bin/env python3

from rkd.core.api.testing import BasicTestingCase
from rkd.core.api.syntax import TaskAliasDeclaration


class TestTaskAliasDeclaration(BasicTestingCase):
    def test_get_name(self):
        ta = TaskAliasDeclaration(':bakunin', [':list'])
        self.assertEqual(':bakunin', ta.get_name())

    def test_get_name_includes_subproject(self):
        ta = TaskAliasDeclaration(':bakunin', [':list'])
        ta_subproject = ta.as_part_of_subproject('books', ':books')

        self.assertEqual(':books:bakunin', ta_subproject.get_name())
        self.assertNotEqual(ta, ta_subproject)

    def test_is_part_of_subproject(self):
        ta = TaskAliasDeclaration(':bakunin', [':list'])
        ta_subproject = ta.as_part_of_subproject('books', ':books')

        self.assertTrue(ta_subproject.is_part_of_subproject())
        self.assertFalse(ta.is_part_of_subproject())
