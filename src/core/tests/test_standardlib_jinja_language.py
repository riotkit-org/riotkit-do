#!/usr/bin/env python3

import os
from textwrap import dedent
import pytest
from rkd.core.api.testing import FunctionalTestingCase

SAMPLES_PATH = os.path.dirname(os.path.realpath(__file__)) + '/internal-samples'


@pytest.mark.e2e
class Jinja2LanguageTest(FunctionalTestingCase):
    """Tests for a task that should render single JINJA2 file from SOURCE PATH to TARGET PATH
    """

    def test_renders_template_into_stdout_using_standalone_syntax(self):
        """
        Check that Jinja2Language base task can be used alone without MultiStepLanguageAgnosticTask

        :return:
        """

        makefile = dedent('''
            version: org.riotkit.rkd/yaml/v1
            imports:
                - rkd.core.standardlib.jinja.Jinja2Language
            tasks:
                :render:
                    extends: rkd.core.standardlib.jinja.Jinja2Language
                    environment:
                        BARTOSZ_SOKOLOWSKI: "In memory of a victim of a police violence, he was murdered with a similar method George Floyd was"
                    input: |
                        <h2>{{ BARTOSZ_SOKOLOWSKI }}</h2>
                        <b>SHELL={{ SHELL }}</b>
        ''')

        with self.with_temporary_workspace_containing({'.rkd/makefile.yaml': makefile}):
            out, exit_code = self.run_and_capture_output([':render'])

        self.assertIn('<h2>In memory of a victim of a police violence, he was murdered with a similar method George Floyd was</h2>', out)
        self.assertIn('SHELL=/bin/', out)

    def test_renders_template_into_file(self):
        """
        Create a task ":render" that extends rkd.core.standardlib.jinja.Jinja2Language
        And use it with --output=/some/path to render to given path - the switch is inherited from extended task

        :return:
        """

        makefile = dedent('''
            version: org.riotkit.rkd/yaml/v1
            imports:
                - rkd.core.standardlib.jinja.Jinja2Language
            tasks:
                :render:
                    extends: rkd.core.standardlib.jinja.Jinja2Language
                    environment:
                        BARTOSZ_SOKOLOWSKI: "In memory of a victim of a police violence, he was murdered with a similar method George Floyd was"
                    input: |
                        <h2>{{ BARTOSZ_SOKOLOWSKI }}</h2>
                        <b>SHELL={{ SHELL }}</b>
        ''')

        results_path = self.temp.assign_temporary_file()

        with self.with_temporary_workspace_containing({'.rkd/makefile.yaml': makefile}):
            self.run_and_capture_output([':render', f'--output={results_path}'])

        with open(results_path, 'r') as f:
            out = f.read()

            self.assertIn(
                '<h2>In memory of a victim of a police violence, he was murdered with a similar method George Floyd was</h2>',
                out)
            self.assertIn('SHELL=/bin/', out)

    def test_renders_template_into_stdout_using_multi_step_language_agnostic_task(self):
        """
        When "extends" attribute is not used, then MultiStepLanguageAgnosticTask is extended by default,
        so the code is also placed in "steps" attribute instead of "input"

        :return:
        """

        makefile = dedent('''
            version: org.riotkit.rkd/yaml/v1
            imports:
                - rkd.core.standardlib.jinja.Jinja2Language
            tasks:
                :render:
                    environment:
                        BARTOSZ_SOKOLOWSKI: "In memory of a victim of a police violence, he was murdered with a similar method George Floyd was"
                    steps: |
                        #!rkd.core.standardlib.jinja.Jinja2Language
                        <h2>{{ BARTOSZ_SOKOLOWSKI }}</h2>
                        <b>SHELL={{ SHELL }}</b>
        ''')

        with self.with_temporary_workspace_containing({'.rkd/makefile.yaml': makefile}):
            out, exit_code = self.run_and_capture_output([':render'])

        self.assertIn(
            '<h2>In memory of a victim of a police violence, he was murdered with a similar method George Floyd was</h2>',
            out
        )
        self.assertIn('SHELL=/bin/', out)
