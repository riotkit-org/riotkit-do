#!/usr/bin/env python3

import unittest
import os
from rkd.test import TestTask

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class TestTaskInterface(unittest.TestCase):
    def test_table(self):
        """Simply test table() - the table is expected to use an external library, it is expected that external library
        will be tested already, but we need to check there if the interface matches
        """

        task = TestTask()
        out = task.table(
            header=['Activist', 'Born date'],
            body=[
                ['Mikhail Alexandrovich Bakunin', '1814'],
                ['Errico Malatesta', '1853'],
                ['José Buenaventura Durruti Dumange', '1896'],
                ['Johann Rudolf Rocker', '1873']
            ]
        )

        self.assertIn('---------------------------------', out)
        self.assertIn('Mikhail Alexandrovich Bakunin', out)
        self.assertIn('Johann Rudolf Rocker', out)
        self.assertIn('Activist', out)
        self.assertIn('Born date', out)

    def test_should_fork(self):
        task = TestTask()

        with self.subTest('Will fork'):
            task.get_become_as = lambda: 'root'
            self.assertTrue(task.should_fork())

        with self.subTest('Will not fork - no user specified'):
            task.get_become_as = lambda: ''
            self.assertFalse(task.should_fork())
