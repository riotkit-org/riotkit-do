#!/usr/bin/env python3

import os
from textwrap import dedent
import pytest
from rkd.core.api.testing import FunctionalTestingCase

SAMPLES_PATH = os.path.dirname(os.path.realpath(__file__)) + '/internal-samples'


@pytest.mark.e2e
class PhpIntegrationFunctionalTest(FunctionalTestingCase):
    def test_php_can_be_executed_from_input(self):
        makefile = dedent('''
            version: org.riotkit.rkd/yaml/v1
            tasks:
                :exec:
                    extends: rkd.php.script.PhpLanguage
                    configure@before_parent: |
                        self.version = '8.0-alpine'
                    input: |
                        phpinfo();
        ''')

        with self.with_temporary_workspace_containing({'.rkd/makefile.yaml': makefile}):
            out, exit_code = self.run_and_capture_output([':exec'])

        self.assertIn("$_ENV['PHP_VERSION'] => 8.0", out)

    def test_switching_php_version_works(self):
        """
        Default version is PHP 8.0, test that switching to e.g. 7.4 works

        :return:
        """

        makefile = dedent('''
            version: org.riotkit.rkd/yaml/v1
            tasks:
                :exec:
                    extends: rkd.php.script.PhpLanguage
                    environment:
                        PHP: '7.4'
                    input: |
                        phpinfo();
        ''')

        with self.with_temporary_workspace_containing({'.rkd/makefile.yaml': makefile}):
            out, exit_code = self.run_and_capture_output([':exec'])

        self.assertIn("$_ENV['PHP_VERSION'] => 7.4", out)

    def test_using_php_language_inside_multi_step_language_agnostic_task(self):
        makefile = dedent('''
            version: org.riotkit.rkd/yaml/v1
            tasks:
                :exec:
                    environment:
                        PHP: '7.4'
                        IMAGE: 'php'
                    steps: |
                        #!rkd.php.script.PhpLanguage
                        phpinfo();
        ''')

        with self.with_temporary_workspace_containing({'.rkd/makefile.yaml': makefile}):
            out, exit_code = self.run_and_capture_output([':exec', '-rl', 'debug'])

        self.assertIn("$_ENV['PHP_VERSION'] => 7.4", out)
