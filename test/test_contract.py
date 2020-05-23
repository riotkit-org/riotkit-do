#!/usr/bin/env python3

import unittest
import os
from rkd.standardlib import InitTask
from rkd.contract import ExecutionContext
from rkd.syntax import TaskDeclaration
from rkd.exception import MissingInputException

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class TestTaskInterface(unittest.TestCase):
    def test_get_arg_or_env(self):
        """Checks logic of fetching commandline switch, with fallback to environment variable
        """

        datasets = {
            'env, switch = switch': {
                'switches': {'revolution': 'yes'},
                'envs': {'REVOLUTION': 'no'},
                'expects': 'yes',
                'raises': None
            },

            'ENV - NO switch = env': {
                'switches': {'revolution': None},
                'envs': {'REVOLUTION': 'yup'},
                'expects': 'yup',
                'raises': None
            },

            'NO env, NO switch = raise': {
                'switches': {'revolution': None},
                'envs': {},
                'expects': '',
                'raises': MissingInputException
            },

            'NO env, switch = switch': {
                'switches': {'revolution': 'yes'},
                'envs': {},
                'expects': 'yes',
                'raises': None
            }
        }

        task = InitTask()
        task.get_declared_envs = lambda: {
            'REVOLUTION': None
        }

        #
        # Actual test code
        #
        def test(dataset_name, dataset):
            context = ExecutionContext(TaskDeclaration(task), args=dataset['switches'], env=dataset['envs'])
            self.assertEqual(dataset['expects'], context.get_arg_or_env('--revolution'),
                             msg='Dataset failed: %s' % dataset_name)

        #
        # Iteration over datasets
        #
        for dataset_name, dataset in datasets.items():
            if dataset['raises']:
                with self.assertRaises(dataset['raises']):
                    test(dataset_name, dataset)
            else:
                test(dataset_name, dataset)


