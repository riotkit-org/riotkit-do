#!/usr/bin/env python3
import pytest
from rkd.core.api.testing import BasicTestingCase
from rkd.core.test import get_test_declaration


class TestTaskDeclaration(BasicTestingCase):
    def test_get_full_description_returns_docstring_when_description_method_does_not_return_anything(self):
        """TaskDeclaration.get_full_description() returns docstring of task to execute, when the task does not implement
        get_description() by itself
        """

        declaration = get_test_declaration()
        declaration.get_task_to_execute().get_description = lambda: ''

        declaration.get_task_to_execute().__doc__ = '''
            10 Jun 1973 a strike of gravediggers at 3 cemeteries in the New York metropolitan area was expanded 
            to include 44 others. Strikers defied a court order, the jailing of their union leader and after 
            27 days they won a pension scheme and pay increase
        '''

        self.assertIn('27 days they won a pension scheme and pay increase', declaration.get_full_description())

    def test_get_full_description_returns_result_of_tasks_get_description_if_defined(self):
        """TaskDeclaration.get_full_description() returns get_task_to_execute().get_description() if response is not
        empty
        """

        declaration = get_test_declaration()
        declaration.get_task_to_execute().get_description = lambda: '10 June 1942 Polish prisoners on work detail ' + \
                                                                    'at Auschwitz Birkenau managed to escape while ' + \
                                                                    'digging a drainage ditch.'

        self.assertIn('Polish prisoners', declaration.get_full_description())
        self.assertIn('Auschwitz Birkenau', declaration.get_full_description())
        self.assertIn('managed to escape', declaration.get_full_description())

    def test_get_full_description_allows_empty_doc(self):
        """Test that description can be not defined at all"""

        declaration = get_test_declaration()
        declaration.get_task_to_execute().get_description = lambda: None
        declaration.get_task_to_execute().__doc__ = None

        self.assertEqual('', declaration.get_full_description())

    def test_to_full_name_includes_subproject(self):
        declaration = get_test_declaration()
        declaration._project_name = ':docs'

        # :rkd:test comes from get_test_declaration()
        self.assertEqual(':docs:rkd:test', declaration.to_full_name())

    def test_as_part_of_subproject_appends_required_attributes(self):
        declaration = get_test_declaration()

        subproject_declaration = declaration.as_part_of_subproject('/tmp', ':docs')

        # new declaration
        self.assertEqual(':docs:rkd:test', subproject_declaration.to_full_name())
        self.assertEqual('/tmp/', subproject_declaration.workdir)

        # old should be NOT TOUCHED
        self.assertEqual(':rkd:test', declaration.to_full_name())
        self.assertEqual('.', declaration.workdir)

    def test_is_internal_inherits_from_task_when_not_defined(self) -> None:
        declaration = get_test_declaration(internal=True)
        declaration._is_internal = None

        self.assertTrue(declaration.is_internal)

    def test_is_internal_is_not_inherited_from_task_when_defined_in_taskdeclaration(self) -> None:
        declaration = get_test_declaration(internal=True)  # this one is overridden
        declaration._is_internal = False       # this one overrides the second one

        self.assertFalse(declaration.is_internal)
