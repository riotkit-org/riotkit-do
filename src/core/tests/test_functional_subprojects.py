#!/usr/bin/env python3

import pytest
import os
from rkd.core.api.testing import FunctionalTestingCase
from rkd.process import switched_workdir

TESTS_DIR = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.e2e
class TestFunctionalSubprojects(FunctionalTestingCase):
    def test_subproject_tasks_are_included(self):
        """
        The structure:
        - ROOT PROJECT (makefile.yaml)
            -> testsubproject1 (makefile.yaml)
                -> docs (makefile.yaml)
                -> infrastructure (makefile.py)
                    -> terraform (makefile.py)
        """

        with switched_workdir(TESTS_DIR + '/internal-samples/subprojects'):
            full_output, exit_code = self.run_and_capture_output([':tasks', '-a'])

            # tasks are defined in internal-samples/subprojects directory
            self.assertIn('[testsubproject1]', full_output)
            self.assertIn(':testsubproject1:hello', full_output)
            self.assertIn(':testsubproject1:docs:build-docs', full_output)
            self.assertIn(':testsubproject1:infrastructure:list', full_output)
            self.assertIn(':testsubproject1:infrastructure:terraform:apply', full_output)

    def test_subproject_in_yaml(self):
        """
        The structure:
        - ROOT PROJECT (makefile.yaml)
            -> testsubproject1 (makefile.yaml)
                -> docs (makefile.yaml)
                -> infrastructure (makefile.py)
                    -> terraform (makefile.py)
        """

        with switched_workdir(TESTS_DIR + '/internal-samples/subprojects'):
            full_output, exit_code = self.run_and_capture_output([':testsubproject1:test-pwd'])

            self.assertIn('Hello from testsubproject1', full_output)

    def test_subproject_in_python_syntax_has_correct_workdir(self):
        """
        The structure:
        - ROOT PROJECT (makefile.yaml)
            -> testsubproject1 (makefile.yaml)
                -> docs (makefile.yaml)
                -> infrastructure (makefile.py)
                    -> terraform (makefile.py)
        """

        with switched_workdir(TESTS_DIR + '/internal-samples/subprojects'):
            full_output, exit_code = self.run_and_capture_output([':testsubproject1:infrastructure:terraform:pwd'])

            self.assertIn('internal-samples/subprojects/testsubproject1/infrastructure/terraform', full_output)
            self.assertIn('from terraform', full_output)
