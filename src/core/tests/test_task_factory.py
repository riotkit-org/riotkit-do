from typing import Tuple

from rkd.core.api.contract import ExecutionContext, ExtendableTaskInterface
from rkd.core.api.inputoutput import BufferedSystemIO, IO
from rkd.core.api.syntax import TaskDeclaration
from rkd.core.api.testing import FunctionalTestingCase
from rkd.core.dto import StaticFileContextParsingResult
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
