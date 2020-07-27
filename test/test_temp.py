#!/usr/bin/env python3

"""

Test temporary files management
===============================

RKD has a principle to work with a workspace. This rule is best for Continuous Integration systems, where
we often want to work only inside of given directory, never outside.

"""

import os
import unittest
from rkd.temp import TempManager


class TestTempManager(unittest.TestCase):
    oldCwd: str = ''

    def setUp(self) -> None:
        super().setUp()
        self.oldCwd = os.getcwd()
        os.chdir('/tmp')

        try:
            os.mkdir('.rkd')
        except FileExistsError:
            pass

    def tearDown(self) -> None:
        super().tearDown()
        os.chdir(self.oldCwd)

    def test_create_tmp_file_path_assigns_an_unique_filename(self):
        path, filename = TempManager().create_tmp_file_path()

        self.assertFalse(os.path.isfile(path))

    def test_assign_temporary_file_creates_a_file_and_finally_clean_up_removes_file(self):
        manager = TempManager()

        with self.subTest('Creation'):
            path = manager.assign_temporary_file()
            self.assertTrue(os.path.isfile(path))

        with self.subTest('Deletion'):
            manager.finally_clean_up()
            self.assertFalse(os.path.isfile(path))

    def test_assign_temporary_file_sets_correct_chmod(self):
        manager = TempManager()
        path = manager.assign_temporary_file()

        try:
            st = os.stat(path)

            self.assertEqual('0755', str(oct(st.st_mode))[-4:])
        finally:
            manager.finally_clean_up()
