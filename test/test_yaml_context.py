#!/usr/bin/env python3

import unittest
from rkd.yaml_context import YamlParser
from rkd.inputoutput import NullSystemIO
from rkd.exception import DeclarationException, YamlParsingException


class TestYamlContext(unittest.TestCase):
    def test_parse_imports_successful_case(self):
        factory = YamlParser(NullSystemIO())
        imported = factory.parse_imports(['rkd.standardlib.python.PublishTask'])

        self.assertEqual(':py:publish', imported[0].to_full_name())

    def test_parse_imports_wrong_class_type_but_existing(self):
        def test():
            factory = YamlParser(NullSystemIO())
            factory.parse_imports(['rkd.exception.ContextException'])

        self.assertRaises(DeclarationException, test)

    def test_parse_imports_cannot_import_non_existing_class(self):
        def test():
            factory = YamlParser(NullSystemIO())
            factory.parse_imports(['rkd.standardlib.python.WRONG_NAME'])

        self.assertRaises(YamlParsingException, test)
