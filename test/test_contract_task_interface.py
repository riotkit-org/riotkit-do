#!/usr/bin/env python3

import unittest
import os

from rkd.api.testing import BasicTestingCase
from rkd.test import TestTask
from rkd.contract import ArgumentEnv

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class TestTaskInterface(BasicTestingCase):
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

    def test_internal_normalized_get_declared_envs_maps_primitive_types_into_class_instances(self):
        task = TestTask()
        task.get_declared_envs = lambda: {
            'SOME_ENV': 'primitive',
            'SOME_OTHER_ENV': ArgumentEnv(name='SOME_OTHER_ENV', switch='--cmd', default='not primitive')
        }

        normalized = task.internal_normalized_get_declared_envs()

        with self.subTest('Verify converted string -> ArgumentEnv'):
            self.assertTrue(isinstance(normalized['SOME_ENV'], ArgumentEnv))
            self.assertEqual('SOME_ENV', normalized['SOME_ENV'].name)
            self.assertEqual('--some-env', normalized['SOME_ENV'].switch)
            self.assertEqual('primitive', normalized['SOME_ENV'].default)

        with self.subTest('Verify not converted'):
            self.assertTrue(isinstance(normalized['SOME_OTHER_ENV'], ArgumentEnv))

    def test_internal_getenv_finds_mapped_environment_variable_by_switch_name(self):
        task = TestTask()
        task.get_declared_envs = lambda: {
            'SOME_OTHER_ENV': ArgumentEnv(name='SOME_OTHER_ENV', switch='--cmd', default='not primitive')
        }

        self.assertEqual('not primitive', task.internal_getenv('', envs={}, switch='--cmd'))

    def test_internal_getenv_finds_envronment_variable_by_its_not_mapped_name(self):
        task = TestTask()
        task.get_declared_envs = lambda: {
            'SOME_ENV': 'primitive'
        }

        with self.subTest('Should find by first argument SOME_ENV'):
            self.assertEqual('primitive', task.internal_getenv('SOME_ENV', envs={}, switch=''))

        with self.subTest('Should find by first argument, even if will not find for valid switch'):
            self.assertEqual('primitive', task.internal_getenv('SOME_ENV', envs={}, switch='--some-env'))

        with self.subTest('Should find by first argument, even if will not find for invalid switch'):
            self.assertEqual('primitive', task.internal_getenv('SOME_ENV', envs={}, switch='--some-non-existing'))

