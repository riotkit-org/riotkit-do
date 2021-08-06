#!/usr/bin/env python3

import os
import yaml
from collections import OrderedDict
from io import StringIO
from rkd.core.exception import StaticFileParsingException
from rkd.core.yaml_context import StaticFileSyntaxInterpreter
from rkd.core.yaml_parser import YamlFileLoader
from rkd.core.api.inputoutput import IO
from rkd.core.api.inputoutput import NullSystemIO
from rkd.core.api.inputoutput import BufferedSystemIO
from rkd.core.api.testing import BasicTestingCase
from rkd.core.api.contract import ExecutionContext

SCRIPT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class TestYamlContext(BasicTestingCase):
    def test_parse_tasks_successful_case(self):
        """Successful case with description, arguments and bash steps
        """

        input_tasks = {
            ':resistentia': {
                'description': 'Against moving the costs of the crisis to the workers!',
                'arguments': {
                    '--picket': {
                        'help': 'Picket form',
                        'required': False,
                        'action': 'store_true'
                    }
                },
                'steps': [
                    'echo "Resistentia!"'
                ]
            }
        }

        io = IO()
        out = StringIO()
        factory = StaticFileSyntaxInterpreter(io, YamlFileLoader([]))
        parsed_tasks = factory.parse_tasks(input_tasks, '', './makefile.yaml')

        self.assertEqual(':resistentia', parsed_tasks[0].name,
                         msg='Expected that the task name will be present')
        self.assertEqual('echo "Resistentia!"', parsed_tasks[0].steps[0])

    def test_internal_task_can_be_defined(self):
        """
        Internal/Normal tasks definition in YAML

        A task can be marked internal, so it will be unlisted on ":tasks" listing
        """

        input_tasks = {
            ':resistentia': {
                'description': 'Against moving the costs of the crisis to the workers!',
                'internal': True,
                'arguments': {},
                'steps': [
                    'echo "Resistentia!"'
                ]
            },
            ':resistentia-2': {
                'description': 'Against moving the costs of the crisis to the workers!',
                'arguments': {},
                'steps': [
                    'echo "Resistentia!"'
                ]
            }
        }

        io = IO()
        factory = StaticFileSyntaxInterpreter(io, YamlFileLoader([]))
        parsed_tasks = factory.parse_tasks(input_tasks, '', './makefile.yaml')

        self.assertTrue(parsed_tasks[0].internal)
        self.assertFalse(parsed_tasks[1].internal)

    def test_parse_env_parses_environment_variables_added_manually(self):
        """Test "environment" block
        """

        io = IO()
        factory = StaticFileSyntaxInterpreter(io, YamlFileLoader([]))
        envs = factory.parse_env({
            'environment': {
                'EVENT_NAME': 'In memory of Maxwell Itoya, an Nigerian immigrant killed by police at flea market.' +
                              ' He was innocent, and left wife with 3 kids.'
            }
        }, 'make/file/path/makefile.yaml')

        self.assertIn('EVENT_NAME', envs)
        self.assertIn('Maxwell Itoya', envs['EVENT_NAME'])

    def test_parse_env_parses_environment_variables_from_file(self):
        """Check if envs are loaded from file correctly
        """

        io = IO()
        factory = StaticFileSyntaxInterpreter(io, YamlFileLoader([]))
        envs = factory.parse_env({
            'env_files': [
                SCRIPT_DIR_PATH + '/../../../docs/examples/env-in-yaml/.rkd/env/global.env'
            ]
        }, SCRIPT_DIR_PATH + '/../../../docs/examples/env-in-yaml/.rkd/makefile.yml')

        self.assertIn('TEXT_FROM_GLOBAL_ENV', envs)
        self.assertIn('Jolanta Brzeska was a social activist against evictions, ' +
                      'she was murdered - burned alive by reprivatization mafia', envs['TEXT_FROM_GLOBAL_ENV'])

    def test_parse_env_preserves_variables_order(self):
        """Make sure that the environment variables are loaded in order they were defined
        """

        yaml_content = '''
environment:
    FIRST:  "Jolanta Brzeska"
    SECOND: "Maxwell Itoya"
    THIRD:  "August Spies"
    FOURTH: "Samuel Fielden"
        '''

        expected_order = [
            "Jolanta Brzeska",
            "Maxwell Itoya",
            "August Spies",
            "Samuel Fielden"
        ]

        for i in range(1, 10000):
            parsed = yaml.load(yaml_content, yaml.FullLoader)

            io = IO()
            factory = StaticFileSyntaxInterpreter(io, YamlFileLoader([]))
            envs = factory.parse_env(parsed, 'makefile.yaml')

            names_in_order = []

            for env_name, value in envs.items():
                names_in_order.append(env_name)

            self.assertEqual(expected_order, list(envs.values()))

    def test_parse_subprojects_checks_typing_is_list(self):
        io = IO()
        factory = StaticFileSyntaxInterpreter(io, YamlFileLoader([]))

        with self.assertRaises(StaticFileParsingException):
            # noinspection PyTypeChecker
            factory.parse_subprojects('')  # typo for purpose, should be a list

    def test_parse_subprojects_checks_typing_each_element(self):
        io = IO()
        factory = StaticFileSyntaxInterpreter(io, YamlFileLoader([]))

        with self.assertRaises(StaticFileParsingException):
            # noinspection PyTypeChecker
            factory.parse_subprojects(['subproject1', True, None])

    def test_parse_subprojects(self):
        io = IO()
        factory = StaticFileSyntaxInterpreter(io, YamlFileLoader([]))

        sample = ['subproject1', 'subproject2']

        # noinspection PyTypeChecker
        self.assertEqual(sample, factory.parse_subprojects(sample))
