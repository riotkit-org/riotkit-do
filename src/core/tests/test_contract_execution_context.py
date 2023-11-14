#!/usr/bin/env python3

from rkd.core.api.contract import ExecutionContext
from rkd.core.api.contract import ArgumentEnv
from rkd.core.api.syntax import TaskDeclaration
from rkd.core.api.inputoutput import IO
from rkd.core.api.testing import BasicTestingCase
from rkd.core.exception import MissingInputException
from rkd.core.test import TaskForTesting


class TestExecutionContext(BasicTestingCase):
    def test_get_arg_or_env(self):
        """Checks logic of fetching commandline switch, with fallback to environment variable
        """

        datasets = {
            'env, switch = switch': {
                'switches': {'revolution': 'yes'},
                'envs': {'REVOLUTION': 'no'},
                'defined_args': {
                    '--revolution': {'default': None}
                },
                'declared_envs': {
                    'REVOLUTION': None
                },
                'expects': 'yes',
                'raises': None,
                'test_switch': '--revolution'
            },

            'ENV - NO switch = env': {
                'switches': {'revolution': None},
                'envs': {'REVOLUTION': 'yup'},
                'defined_args': {
                    '--revolution': {'default': None}
                },
                'declared_envs': {
                    'REVOLUTION': None
                },
                'expects': 'yup',
                'raises': None,
                'test_switch': '--revolution'
            },

            'NO env, NO switch = raise': {
                'switches': {'revolution': None},
                'envs': {},
                'defined_args': {
                    '--revolution': {'default': None}
                },
                'declared_envs': {
                    'REVOLUTION': None
                },
                'expects': '',
                'raises': MissingInputException,
                'test_switch': '--revolution'
            },

            'NO env, switch = switch': {
                'switches': {'revolution': 'yes'},
                'envs': {},
                'defined_args': {
                    '--revolution': {'default': None}
                },
                'declared_envs': {
                    'REVOLUTION': None
                },
                'expects': 'yes',
                'raises': None,
                'test_switch': '--revolution'
            },

            'ENV present, SWITCH is set to DEFAULT VALUE = env': {
                'switches': {'person': 'Nobody'},
                'defined_args': {
                    '--person': {'default': 'Nobody'}
                },
                'envs': {'PERSON': 'Gaetano Bresci'},
                'declared_envs': {
                    'PERSON': None
                },
                'expects': 'Gaetano Bresci',
                'raises': False,
                'test_switch': '--person'
            },

            'Custom ENV present, should map a switch to custom ENV name': {
                'switches': {'person': 'Nobody'},
                'defined_args': {
                    '--person': {'default': 'Nobody'}
                },
                'envs': {'PERSON_NAME': 'Luigi Lucheni'},
                'declared_envs': {
                    'PERSON_NAME': ArgumentEnv(name='PERSON_NAME', switch='--person', default='Nobody')
                },
                'expects': 'Luigi Lucheni',
                'raises': False,
                'test_switch': '--person'
            }
        }

        #
        # Actual test code
        #
        def test(dataset_name, dataset):
            task = TaskForTesting()
            task._io = IO()
            task.get_declared_envs = lambda: dataset['declared_envs']

            context = ExecutionContext(TaskDeclaration(task), args=dataset['switches'], env=dataset['envs'],
                                       defined_args=dataset['defined_args'])
            self.assertEqual(dataset['expects'], context.get_arg_or_env(dataset['test_switch']),
                             msg='Dataset failed: %s' % dataset_name)

        #
        # Iteration over datasets
        #
        for dataset_name, dataset in datasets.items():
            with self.subTest(dataset_name):
                if dataset['raises']:
                    with self.assertRaises(dataset['raises']):
                        test(dataset_name, dataset)
                else:
                    test(dataset_name, dataset)
