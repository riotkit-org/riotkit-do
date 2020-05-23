#!/usr/bin/env python3

import unittest
import os
import yaml
from io import StringIO
from rkd.yaml_context import YamlParser
from rkd.inputoutput import IO, NullSystemIO, BufferedSystemIO
from rkd.exception import DeclarationException, YamlParsingException
from rkd.contract import ExecutionContext
from rkd.test import get_test_declaration

SCRIPT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class TestYamlContext(unittest.TestCase):
    def test_parse_imports_successful_case_single_task(self):
        factory = YamlParser(NullSystemIO())
        imported = factory.parse_imports(['rkd.standardlib.docker.PushTask'])

        self.assertEqual(':docker:push', imported[0].to_full_name())

    def test_parse_imports_successful_case_module(self):
        factory = YamlParser(NullSystemIO())
        imported = factory.parse_imports(['rkd.standardlib.docker'])

        names_of_imported_tasks = []

        for task in imported:
            names_of_imported_tasks.append(task.to_full_name())

        self.assertIn(':docker:tag', names_of_imported_tasks)
        self.assertIn(':docker:push', names_of_imported_tasks)

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

    def test_parse_imports_importing_whole_module_without_submodules(self):
        factory = YamlParser(NullSystemIO())
        imported = factory.parse_imports(['rkd_python'])

        names_of_imported_tasks = []

        for task in imported:
            names_of_imported_tasks.append(task.to_full_name())

        self.assertIn(':py:build', names_of_imported_tasks)
        self.assertIn(':py:publish', names_of_imported_tasks)

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
        factory = YamlParser(io)
        parsed_tasks = factory.parse_tasks(input_tasks, '', './makefile.yaml', {})

        self.assertEqual(':resistentia', parsed_tasks[0].to_full_name(),
                         msg='Expected that the task name will be present')

        declaration = parsed_tasks[0]
        declaration.get_task_to_execute()._io = NullSystemIO()

        with io.capture_descriptors(stream=out, enable_standard_out=False):
            declaration.get_task_to_execute().execute(ExecutionContext(declaration))

        self.assertIn('Resistentia!', out.getvalue(), msg='Expected that echo contents will be visible')

    def test_parse_tasks_signals_error_instead_of_throwing_exception(self):
        """
        Test that error thrown by executed Python code will
        """

        input_tasks = {
            ':song': {
                'description': 'Bella Ciao is an Italian protest folk song that originated in the hardships of the ' +
                               'mondina women, the paddy field workers in the late 19th century who sang it to ' +
                               'protest against harsh working conditions in the paddy fields of North Italy',
                'steps': [
                    '''#!python
print(syntax-error-here)
                    '''
                ]
            }
        }

        io = BufferedSystemIO()
        factory = YamlParser(io)
        parsed_tasks = factory.parse_tasks(input_tasks, '', 'makefile.yaml', {})

        declaration = parsed_tasks[0]
        declaration.get_task_to_execute()._io = IO()
        task = declaration.get_task_to_execute()
        task._io = io

        # execute prepared task
        result = task.execute(ExecutionContext(declaration))

        self.assertEqual(False, result, msg='Expected that syntax error would result in a failure')
        self.assertIn("NameError: name 'syntax' is not defined", io.get_value(), msg='Error message should be attached')
        self.assertIn('File ":song@step 1", line 1', io.get_value(), msg='Stacktrace should be attached')

    def _create_callable_tester(self, code: str, language: str, io: IO = None) -> bool:
        if not io:
            io = BufferedSystemIO()

        factory = YamlParser(io)

        declaration = get_test_declaration()

        if language == 'python':
            execute_callable = factory.create_python_callable(code, 500, ':test', '/some/path', {})
        else:
            execute_callable = factory.create_bash_callable(code, 500, ':test', '/some/path', {})

        result = execute_callable(ExecutionContext(declaration), declaration.get_task_to_execute())

        return result

    def test_create_bash_callable_successful_case(self):
        """ Bash callable test: Successful case """

        io = IO()
        out = StringIO()

        with io.capture_descriptors(stream=out, enable_standard_out=False):
            self._create_callable_tester('python --version', language='bash')

        self.assertIn("Python", out.getvalue())
        self.assertTrue(out.getvalue(), msg='python --version should result with a True')

    def test_create_bash_callable_failure_case_on_invalid_exit_code(self):
        """ Bash callable test: Check if failures are correctly catched """

        result = self._create_callable_tester('exit 161', language='bash')

        self.assertFalse(result)

    def test_create_python_callable_case_syntax_error(self):

        result = self._create_callable_tester('''
impppport os
        ''', language='python')

        self.assertFalse(result)

    def test_create_python_callable_case_multiline_with_imports_and_call_to_this(self):
        result = self._create_callable_tester('''
import os

# do a very simple verification of class names, if not defined then it would fail
return "ExecutionContext" in str(ctx) and "Task" in str(this)
''', language='python')

        self.assertTrue(result)

    def test_create_bash_callable_case_verify_env_variables_are_present(self):

        io = IO()
        out = StringIO()

        with io.capture_descriptors(stream=out, enable_standard_out=False):
            self._create_callable_tester('echo "Boolean: ${ARG_TEST}, Text: ${ARG_MESSAGE}"', language='bash')

        self.assertIn('ARG_TEST: unbound variable', out.getvalue())

    def test_parse_env_parses_environment_variables_added_manually(self):
        """Test "environment" block
        """

        io = IO()
        factory = YamlParser(io)
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
        factory = YamlParser(io)
        envs = factory.parse_env({
            'env_files': [
                SCRIPT_DIR_PATH + '/../docs/examples/env-in-yaml/.rkd/env/global.env'
            ]
        }, SCRIPT_DIR_PATH + '/../docs/examples/env-in-yaml/.rkd/makefile.yml')

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
            factory = YamlParser(io)
            envs = factory.parse_env(parsed, 'makefile.yaml')

            names_in_order = []

            for env_name, value in envs.items():
                names_in_order.append(env_name)

            self.assertEqual(expected_order, list(envs.values()))
