#!/usr/bin/env python3

import unittest
import os
from rkd.yaml_parser import YamlFileLoader
from rkd.exception import YAMLFileValidationError

SCRIPT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class TestLoader(unittest.TestCase):
    def test_validates_successfully(self):
        yaml_loader = YamlFileLoader([])

        parsed = yaml_loader.load('''
            version: org.riotkit.rkd/yaml/v1
            imports: []
            tasks: {}
            ''', schema_name='org.riotkit.rkd/yaml/v1')

        self.assertIn('version', parsed)

    def test_raises_error_when_type_does_not_match(self):
        """Expect OBJECT at .tasks path, but get ARRAY instead"""

        yaml_loader = YamlFileLoader([])

        self.assertRaises(
            YAMLFileValidationError,
            lambda: yaml_loader.load('''
                version: org.riotkit.rkd/yaml/v1
                imports: []
                tasks: []
                ''', schema_name='org.riotkit.rkd/yaml/v1')
                          )

    def test_expect_path_will_be_shown_in_exception_message(self):
        """Simply check if path to the attribute will be printed within the exception"""

        yaml_loader = YamlFileLoader([])

        try:
            yaml_loader.load('''
                version: org.riotkit.rkd/yaml/v1
                imports: []
                tasks: 
                    :join:iwa-ait: []
                ''', schema_name='org.riotkit.rkd/yaml/v1')
        except YAMLFileValidationError as e:
            self.assertIn(
                "YAML schema validation failed at path \"tasks.:join:iwa-ait\" with error: [] is not of type 'object'",
                str(e)
            )
            return

        self.fail('Expected an exception to be raised')

    def test_expect_deeper_validation_will_be_performed(self):
        """Expects that argparse arguments will be validated"""

        yaml_loader = YamlFileLoader([])

        try:
            yaml_loader.load('''
                        version: org.riotkit.rkd/yaml/v1
                        imports: []
                        tasks: 
                            :join:iwa-ait:
                                description: Subscribe to any local section of IWA-AIT, workers have common interest
                                arguments:
                                    - not a list
                        ''', schema_name='org.riotkit.rkd/yaml/v1')
        except YAMLFileValidationError as e:
            self.assertIn("tasks.:join:iwa-ait.arguments", str(e))
            self.assertIn("is not of type 'object'", str(e))
            return

        self.fail('Expected an exception to be raised')
