#!/usr/bin/env python3

from unittest.mock import mock_open, patch
from rkd.api.testing import BasicTestingCase
from rkd.api.inputoutput import Wizard
from rkd.api.inputoutput import BufferedSystemIO
from rkd.test import TestTask
from rkd.exception import InterruptExecution


class TestWizard(BasicTestingCase):
    def test_regexp_validation(self):
        wizard = Wizard(TestTask())
        wizard.sleep_time = 0
        wizard.io = BufferedSystemIO()

        with self.subTest('Input is matching regexp'):
            wizard.input = lambda secret: 'Buenaventura'
            wizard.ask('What\'s your name?', 'name', regexp='([A-Za-z]+)')
            self.assertIn('name', wizard.answers)

        with self.subTest('Input is not matching regexp'):
            wizard.input = lambda secret: '...'
            self.assertRaises(InterruptExecution, lambda: wizard.ask('What\'s your name?', 'name', regexp='([A-Za-z]+)'))

    def test_input_is_retried_when_validation_fails(self):
        wizard = Wizard(TestTask())
        wizard.sleep_time = 0
        wizard.io = BufferedSystemIO()
        self.retry_num = 0

        def mocked_input(secret: bool = False):
            self.retry_num = self.retry_num + 1

            return ['...', '...', 'Buenaventura'][self.retry_num]

        wizard.input = mocked_input
        wizard.ask('What\'s your name?', 'name', regexp='([A-Za-z]+)')

        self.assertEqual({'name': 'Buenaventura'}, wizard.answers)

    def test_must_select_between_regexp_and_choice_validation(self):
        """Verify that the 'regexp' and 'choices' cannot be specified at one time in ask()"""

        wizard = Wizard(TestTask())
        wizard.io = BufferedSystemIO()

        self.assertRaises(Exception, lambda:
            wizard.ask('In which year the Spanish social revolution has begun?',
                       attribute='year',
                       regexp='([0-9]+)',
                       choices=['1936', '1910'])
        )

    def test_is_question_pretty_formatted_for_choice_validation(self):
        wizard = Wizard(TestTask())
        wizard.io = BufferedSystemIO()
        wizard.input = lambda secret: '1936'

        wizard.ask('In which year the Spanish social revolution has begun?',
                   attribute='year',
                   choices=['1936', '1910'])

        self.assertIn('In which year the Spanish social revolution has begun? [1936, 1910]:', wizard.io.get_value())

    def test_is_question_pretty_formatted_for_regexp_validation(self):
        wizard = Wizard(TestTask())
        wizard.io = BufferedSystemIO()
        wizard.input = lambda secret: '1936'

        wizard.ask('In which year the Spanish social revolution has begun?',
                   attribute='year',
                   regexp='([0-9]{4})')

        self.assertIn('In which year the Spanish social revolution has begun? [([0-9]{4})]:', wizard.io.get_value())

    def test_is_question_pretty_formatted_for_default_value_and_choice(self):
        wizard = Wizard(TestTask())
        wizard.io = BufferedSystemIO()
        wizard.input = lambda secret: '1936'

        wizard.ask('In which year the Spanish social revolution has begun?',
                   attribute='year',
                   regexp='([0-9]{4})',
                   default='1936')

        self.assertIn('In which year the Spanish social revolution has begun? [([0-9]{4})] [default: 1936]:', wizard.io.get_value())

    def test_finish_is_writing_values(self):
        tmp_wizard_file = mock_open()
        rkd_shell_calls = []

        with patch('rkd.api.inputoutput.open', tmp_wizard_file, create=True):
            task = TestTask()
            task.rkd = lambda *args, **kwargs: rkd_shell_calls.append(args)

            wizard = Wizard(task)
            wizard.io = BufferedSystemIO()

            wizard.input = lambda secret: '1936'
            wizard.ask('In which year the Spanish social revolution has begun?',
                       attribute='year',
                       regexp='([0-9]{4})',
                       default='1936')

            wizard.input = lambda secret: 'ait'
            wizard.ask('Enter new value for COMPOSE_PROJECT_NAME', attribute='COMPOSE_PROJECT_NAME', to_env=True)
            wizard.finish()

            # assertions
            tmp_wizard_file.assert_called_once_with('.rkd/tmp-wizard.json', 'wb')
            self.assertEqual([':env:set', '--name="COMPOSE_PROJECT_NAME"', '--value="ait"'], rkd_shell_calls[0][0])

    def test_getpass_is_used_when_secret_switch_is_used(self):
        """Test a secret=True switch in wizard.input() which is used by ask()"""

        wizard = Wizard(TestTask())
        wizard.io = BufferedSystemIO()

        with patch('rkd.api.inputoutput.getpass') as getpass:
            getpass.return_value = 'organize!'

            self.assertEqual('organize!', wizard.input(secret=True))
