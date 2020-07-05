"""
Generic YAML file parsing module

Uses standard YAML parser, adds additional features, such as:
  - Schema validation
  - RKD lookup paths integration
"""

import os
from typing import List
from yaml import load as yaml_load
from yaml import Loader as YamlLoader
from json import load as json_load
from jsonschema import validate
from jsonschema import ValidationError
from jsonschema import draft7_format_checker
from .exception import YAMLFileValidationError

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class YamlFileLoader(object):
    """YAML loader extended by schema validation support

    YAML schema is stored as JSON files in .rkd/schema directories.
    The Loader looks in all paths defined in RKD_PATH as well as in paths provided by ApplicationContext
    """

    paths: List[str]

    def __init__(self, paths: List[str]):
        self.paths = paths

    def load(self, stream, schema_name: str):
        """Loads a YAML, validates and return parsed as dict/list """

        schema_name = schema_name.replace('/', '-') + '.json'
        schema_path = self.find_schema_path_by_name(schema_name)

        if not schema_path:
            raise FileNotFoundError('Schema "%s" cannot be found, looked in: %s' % (
                schema_name, str(self.get_schema_lookup_paths())
            ))

        parsed = yaml_load(stream, YamlLoader)

        with open(schema_path, 'rb') as f:
            try:
                validate(instance=parsed, schema=json_load(f), format_checker=draft7_format_checker)
            except ValidationError as e:
                raise YAMLFileValidationError(e)

        return parsed

    def find_schema_path_by_name(self, schema_name: str) -> str:
        """Find schema in one of RKD directories or in current path
        """

        for path in self.get_schema_lookup_paths():
            file_path = path + '/' + schema_name

            if os.path.isfile(file_path):
                return file_path

        return ''

    def get_schema_lookup_paths(self) -> List[str]:
        paths = ['./', './schema', './.rkd/schema']
        global_paths = os.getenv('RKD_PATH', '').split(':')
        global_paths.reverse()

        for path in self.paths:
            paths.append(path + '/.rkd/schema')

        for path in global_paths:
            paths.append(path + '/schema')

        paths.append(CURRENT_SCRIPT_PATH + '/internal/schema')

        return paths
