from argparse import ArgumentParser
from copy import deepcopy
from typing import Tuple

from rkd.core.api.contract import ExecutionContext, ExtendableTaskInterface, ArgumentEnv, ArgparseArgument
from rkd.core.api.decorators import MARKER_SKIP_PARENT_CALL, MARKER_CALL_PARENT_FIRST, \
    MARKER_CALL_PARENT_LAST
from rkd.core.api.inputoutput import BufferedSystemIO, IO
from rkd.core.api.syntax import TaskDeclaration
from rkd.core.api.testing import FunctionalTestingCase
from rkd.core.dto import StaticFileContextParsingResult, ParsedTaskDeclaration
from rkd.core.standardlib import ShellCommandTask
from rkd.core.standardlib.syntax import MultiStepLanguageAgnosticTask
from rkd.core.task_factory import TaskFactory
from rkd.core.yaml_context import StaticFileSyntaxInterpreter
from rkd.core.yaml_parser import YamlFileLoader


class TestTaskFactory(FunctionalTestingCase):
    def test_no_return_means_return_false(self):
        """
        Test that error thrown by executed Python code will

        Notice: Integration test between StaticFileSyntaxInterpreter and TaskFactory
                Checks if output from StaticFileSyntaxInterpreter is valid for TaskFactory

        """

        input_tasks = {
            ':song': {
                'extends': 'rkd.core.standardlib.shell.ShellCommandTask',
                'description': 'Bella Ciao is an Italian protest folk song that originated in the hardships of the ' +
                               'mondina women, the paddy field workers in the late 19th century who sang it to ' +
                               'protest against harsh working conditions in the paddy fields of North Italy',
                'inner_execute': '''#!python
print('Bella Ciao')
                '''
            }
        }

        io = BufferedSystemIO()
        task, declaration = self._prepare(io, input_tasks)

        # execute prepared task
        result = task.inner_execute(ExecutionContext(declaration))
        result_text = io.get_value()

        self.assertEqual(False, result, msg='Expected that "return False" would be the default behavior')
        self.assertIn('Python code at task :song does not have return', result_text,
                      msg='Warning message should be printed')

    def test_steps_are_returned_as_array(self):
        input_tasks = {
            ':song': {
                'steps': ['echo "test"']
            }
        }

        task: MultiStepLanguageAgnosticTask
        task, declaration = self._prepare(BufferedSystemIO(), input_tasks)

        self.assertEqual(['echo "test"'], task.get_steps())

    def test_argparse_arguments_are_inherited_from_parent(self):
        """
        Check that "--test" switch comes from our definition, but "--cmd" comes from
        rkd.core.standardlib.shell.ShellCommandTask that is defined as a parent for this task

        :return:
        """

        input_tasks = {
            ':song': {
                'extends': 'rkd.core.standardlib.shell.ShellCommandTask',
                'arguments': {
                    '--test': {
                        'help': 'Test switch added by :song task definition'
                    }
                }
            }
        }

        task: MultiStepLanguageAgnosticTask
        task, declaration = self._prepare(BufferedSystemIO(), input_tasks)

        parser = ArgumentParser()
        task.configure_argparse(parser)

        self.assertIn('--cmd', str(parser._actions))
        self.assertIn('--test', str(parser._actions))

    def test_environment_variables_are_merged_in_order(self):
        """
        Importance of environment variables (last value has highest priority)
        1. Base class
        2. YAML document, where task is defined
        3. Task definition

        :return:
        """

        task_type = deepcopy(ShellCommandTask)
        task_type.get_declared_envs = lambda: {'INHERITED': 'PARENT TASK', 'PARENT_NOT_OVERWRITTEN': 'Stays'}

        parsed = [
            ParsedTaskDeclaration(
                name=':test',
                group=':group',
                description='...',
                argparse_options=[ArgparseArgument([], {})],
                task_type='rkd.core.standardlib.Something',
                become='root',
                workdir='/tmp',
                internal=True,
                steps=[],

                inner_execute='',
                execute='',
                task_input='',
                configure='',

                method_decorators={},
                environment={'INHERITED': 'TASK SCOPE', 'TASK_SPECIFIC': 'is there'}
            )
        ]

        parsing_context = StaticFileContextParsingResult(
            imports=[],
            parsed=parsed,
            subprojects=[],
            global_environment={'INHERITED': 'DOCUMENT SCOPE', 'DOCUMENT_SPECIFIC': 'present'}
        )

        env = TaskFactory(BufferedSystemIO())._build_environment(
            parsing_context=parsing_context,
            source=parsed[0],
            extended_class=ShellCommandTask
        )

        self.assertEqual('TASK SCOPE', env['INHERITED'])          # defined in all, task level overwrites in priority
        self.assertEqual('Stays', env['PARENT_NOT_OVERWRITTEN'])  # defined only in parent
        self.assertEqual('present', env['DOCUMENT_SPECIFIC'])     # defined only in document
        self.assertEqual('is there', env['TASK_SPECIFIC'])        # defined only in task

    def test_proxy_method_is_used_on_task_level_not_on_declaration_level(self):
        """
        TaskInterface implementation will have TaskFactory._create_proxy_method.<locals>._inner_proxy_method() used
        TaskDeclaration will have a bound method

        :return:
        """

        input_tasks = {
            ':song': {
                'extends': 'rkd.core.standardlib.shell.ShellCommandTask',
                'description': 'Rise Against - Drones',
                'inner_execute': '''#!bash
                    echo "The drones all slave away, they're working overtime \
                          They serve a faceless queen, they never question why \
                          Disciples of a God, they neither live nor breathe, (I won't come back) \
                          But we have bills to pay, yeah we have mouths to feed! (I won't come back) \
                          I won't come back!"
                '''
            }
        }

        io = BufferedSystemIO()
        task, declaration = self._prepare(io, input_tasks)

        self.assertIn('<bound method TaskDeclaration.get_input of '
                      '<abc.TaskDeclaration_generated_rkd.core.standardlib.shell.ShellCommandTask object',
                      str(declaration.get_input))

        self.assertIn('TaskFactory._create_proxy_method.<locals>._inner_proxy_method', str(task.inner_execute))

    def test_description_is_created(self):
        input_tasks = {
            ':song': {
                'extends': 'rkd.core.standardlib.shell.ShellCommandTask',
                'description': '''
                    Rise Against - The Numbers
                    This is a second line
                ''',
                'inner_execute': '''#!bash
                            echo "How long will we drag their plow? \
                                  What will continue to be \
                                  Is what we allow..."
                        '''
            }
        }

        task, declaration = self._prepare(BufferedSystemIO(), input_tasks)

        self.assertIn('Rise Against - The Numbers\n', declaration.get_description().strip())
        self.assertIn('This is a second line', declaration.get_description().strip())

    def test_class_name_in_extends_is_validated(self):
        """
        Covers TaskFactory._import_type()

        :return:
        """

        input_tasks = {
            ':song': {
                'extends': 'rkd.core.standardlib.shell.SomeTaskThatDoesNotExist',
                'description': 'Class specified in "extends" of this example does not exist'
            }
        }

        with self.assertRaises(Exception) as exc:
            self._prepare(BufferedSystemIO(), input_tasks)

        self.assertIn('Cannot import rkd.core.standardlib.shell.SomeTaskThatDoesNotExist. '
                      'No such class? Check if package is installed in current environment', str(exc.exception))

    def test_import_type_check_if_imported_thing_is_a_class(self):
        """
        Covers TaskFactory._import_type()

        :return:
        """

        with self.assertRaises(Exception) as exc:
            TaskFactory._import_type('rkd.core.test.TEST_CONSTANT')

        self.assertIn('Cannot import rkd.core.test.TEST_CONSTANT. Imported element is not a type (class)',
                      str(exc.exception))

    def test_unpack_envs_unpacks_argument_env_to_default_values(self):
        """
        Covers TaskFactory._unpack_envs()

        :return:
        """

        envs = TaskFactory._unpack_envs({
            # example 1: in plaintext format
            'WHAT_IMPORTANT_HAPPENED_IN_1936': 'Spanish social revolution. Masses of ordinary people liberated'
                                               ' themselves from fascist army and from government. They also'
                                               ' reorganized their lives in peace and equality,'
                                               ' using a concept of direct democracy, and'
                                               ' employee cooperatives without employers.',

            # example 2: in wrapped format
            'IN_1944': ArgumentEnv(name='IN_1944',
                                   default='A failed uprising took place. Underground army, '
                                           'including anarchosyndicalists organized an'
                                           'uprising in Warsaw against nazi invaders from German Reich')
        })

        self.assertIn('They also reorganized their lives in peace and equality, using a concept of direct democracy, '
                      'and employee cooperatives without employers.',
                      envs['WHAT_IMPORTANT_HAPPENED_IN_1936'])
        self.assertIn('uprising in Warsaw against nazi invaders', envs['IN_1944'])
        self.assertTrue(isinstance(envs['WHAT_IMPORTANT_HAPPENED_IN_1936'], str))
        self.assertTrue(isinstance(envs['IN_1944'], str))

    def test_create_proxy_method_checks_if_method_decorator_does_not_contain_unsupported_decoration(self):
        """
        Covers TaskFactory._create_proxy_method()
        Unsupported decorator (marker) will cause a exception

        :return:
        """

        def test_decorator(func):
            func.marker = 'unsupported-marker-name'
            return func

        @test_decorator
        def current_method():
            pass

        with self.assertRaises(Exception) as exc:
            TaskFactory(BufferedSystemIO())._create_proxy_method(current_method, parent_method=None)

        self.assertIn('uses unsupported annotation/marker.', str(exc.exception))

    def test_create_proxy_method_skips_parent_call_when_annotation_forbids(self):
        """
        Checks that parent call is skipped by the proxy method
        Marker: @without_parent

        :return:
        """

        invoked = {
            'child': False,
            'parent': False
        }

        def current_method(f_self):
            invoked['child'] = True

        def parent_method(f_self):
            invoked['parent'] = True

        current_method.marker = MARKER_SKIP_PARENT_CALL

        method = TaskFactory(BufferedSystemIO())._create_proxy_method(current_method, parent_method)
        method(self)

        self.assertTrue(invoked['child'])
        self.assertFalse(invoked['parent'])

    def test_create_proxy_method_calls_parent_first(self):
        """
        Checks that parent method - super() is called first, then child method\
        Marker: @after_parent

        :return:
        """

        invoked = []

        def current_method(f_self):
            invoked.append('child')

        def parent_method(f_self):
            invoked.append('parent')

        current_method.marker = MARKER_CALL_PARENT_FIRST

        method = TaskFactory(BufferedSystemIO())._create_proxy_method(current_method, parent_method)
        method(self)

        self.assertEqual(['parent', 'child'], invoked)

    def test_create_proxy_method_calls_parent_after_child(self):
        """
        Checks that execution order is: child -> parent
        Marker: @after_parent

        :return:
        """

        invoked = []

        def current_method(f_self):
            invoked.append('child')

        def parent_method(f_self):
            invoked.append('parent')

        current_method.marker = MARKER_CALL_PARENT_LAST

        method = TaskFactory(BufferedSystemIO())._create_proxy_method(current_method, parent_method)
        method(self)

        self.assertEqual(['child', 'parent'], invoked)

    def test_find_method_including_bases_finds_method_from_base_of_base_class(self):
        """
        Given we have a chain of First -> Second -> Third
        And First has "looking_for" method
        When we start looking for "looking_for" method in Third
        Then we should find a match

        :return:
        """

        class First(object):
            def looking_for(self):
                pass

        class Second(First):
            pass

        class Third(Second):
            pass

        result = TaskFactory(BufferedSystemIO())._find_method_including_bases(Third, 'looking_for')

        self.assertIn('<locals>.First.looking_for', str(result))

    @staticmethod
    def _prepare(io: BufferedSystemIO, input_tasks: dict) -> Tuple[ExtendableTaskInterface, TaskDeclaration]:
        # we will use TaskFactory that uses result provided by the StaticFileSyntaxInterpreter
        factory = TaskFactory(io)
        parser = StaticFileSyntaxInterpreter(io, YamlFileLoader([]))

        # first parse "input_tasks"
        parsed = parser.parse_tasks(input_tasks, '', 'makefile.yaml')
        raw_parsed_task = parsed[0]  # we pick a first task from the list - :song
        parsing_context = StaticFileContextParsingResult(
            imports=[],
            parsed=parsed,
            subprojects=[],
            global_environment={}
        )

        # then create a normal TaskDeclaration(TaskInterface())
        declaration = factory.create_task_with_declaration_after_parsing(
            raw_parsed_task,
            parsing_context
        )

        declaration.get_task_to_execute()._io = IO()
        task = declaration.get_task_to_execute()
        task._io = io

        return task, declaration
