#!/usr/bin/env python3

import unittest
import os
import tempfile
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

    def test_loads_from_file_is_searching_in_rkd_path(self):
        """Assert that makefile.yml will be searched in RKD_PATH"""

        yaml_loader = YamlFileLoader([])

        d = tempfile.TemporaryDirectory()
        os.environ['RKD_PATH'] = d.name

        with open(d.name + '/makefile.yml', 'w') as f:
            f.write('''
version: org.riotkit.rkd/yaml/v1
imports: []
tasks: 
    :join:iwa-ait:
        description: Subscribe to any local section of IWA-AIT, workers have common interest
        arguments:
            - not a list
            ''')

        try:
            self.assertRaises(YAMLFileValidationError,
                              lambda: yaml_loader.load_from_file('makefile.yml', 'org.riotkit.rkd/yaml/v1'))
        finally:
            d.cleanup()
            os.environ['RKD_PATH'] = ''

    def test_invalid_file_path_is_causing_exception(self):
        """Test that invalid path will be reported quickly"""

        yaml_loader = YamlFileLoader([])
        self.assertRaises(FileNotFoundError,
                          lambda: yaml_loader.load_from_file('non-existing-file.yml', 'org.riotkit.rkd/yaml/v1'))

    def test_get_lookup_paths_includes_internal_path_as_well_as_rkd_path(self):
        """Verify that lookup paths includes RKD_PATH and internal RKD directories"""

        yaml_loader = YamlFileLoader([])
        os.environ['RKD_PATH'] = 'SOME-PATH-THERE'

        try:
            paths = yaml_loader.get_lookup_paths('harbor-internal/')
        finally:
            os.environ['RKD_PATH'] = ''

        defined_by_rkd_path = paths.index('SOME-PATH-THERE/harbor-internal/')
        internal_path = paths.index(os.path.realpath(SCRIPT_DIR_PATH + '/../src') + '/harbor-internal/')

        self.assertGreater(defined_by_rkd_path, internal_path, msg='defined_by_rkd_path should be favored')

    def test_find_path_by_name_founds_path(self):
        """Assert that makefile.yml will be searched in RKD_PATH"""

        yaml_loader = YamlFileLoader([])

        d = tempfile.TemporaryDirectory()
        os.environ['RKD_PATH'] = d.name

        with open(d.name + '/makefile.yml', 'w') as f:
            f.write('''
        version: org.riotkit.rkd/yaml/v1
        imports: []
        tasks: 
            :join:iwa-ait:
                description: Subscribe to any local section of IWA-AIT, workers have common interest
                arguments:
                    - not a list
                    ''')

        try:
            path = yaml_loader.find_path_by_name('makefile.yml', '/')
            self.assertTrue(len(path) > 0)
        finally:
            d.cleanup()
            os.environ['RKD_PATH'] = ''

    def test_find_path_by_name_does_not_found_anything(self):
        """Verify that find_path_by_name() will not return anything if nothing searched was found"""

        yaml_loader = YamlFileLoader([])
        self.assertEqual('', yaml_loader.find_path_by_name('some-file-that-does-not-exists', ''))
