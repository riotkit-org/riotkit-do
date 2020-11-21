#!/usr/bin/env python3

from rkd.api.testing import BasicTestingCase
from rkd.api.parsing import SyntaxParsing
from rkd.exception import DeclarationException, ParsingException


class TestApiParsing(BasicTestingCase):
    def test_parse_imports_successful_case_single_task(self):
        imported = SyntaxParsing.parse_imports_by_list_of_classes(['rkd.standardlib.jinja.RenderDirectoryTask'])

        self.assertEqual(':j2:directory-to-directory', imported[0].to_full_name())

    def test_parse_imports_successful_case_module(self):
        imported = SyntaxParsing.parse_imports_by_list_of_classes(['rkd.standardlib.jinja'])

        names_of_imported_tasks = []

        for task in imported:
            names_of_imported_tasks.append(task.to_full_name())

        self.assertIn(':j2:render', names_of_imported_tasks)
        self.assertIn(':j2:directory-to-directory', names_of_imported_tasks)

    def test_parse_imports_wrong_class_type_but_existing(self):
        def test():
            SyntaxParsing.parse_imports_by_list_of_classes(['rkd.exception.ContextException'])

        self.assertRaises(DeclarationException, test)

    def test_parse_imports_cannot_import_non_existing_class(self):
        def test():
            SyntaxParsing.parse_imports_by_list_of_classes(['rkd.standardlib.python.WRONG_NAME'])

        self.assertRaises(ParsingException, test)

    def test_parse_imports_importing_whole_module_without_submodules(self):
        imported = SyntaxParsing.parse_imports_by_list_of_classes(['rkd_python'])

        names_of_imported_tasks = []

        for task in imported:
            names_of_imported_tasks.append(task.to_full_name())

        self.assertIn(':py:build', names_of_imported_tasks)
        self.assertIn(':py:publish', names_of_imported_tasks)
