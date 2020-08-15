#!/usr/bin/env python3

import unittest
from tempfile import NamedTemporaryFile
from rkd.standardlib import LineInFileTask
from rkd.test import mock_task, mock_execution_context
from rkd.api.inputoutput import BufferedSystemIO


class LineInFileTaskTest(unittest.TestCase):
    @staticmethod
    def _execute_mocked_task(params: dict, envs: dict = {}) -> BufferedSystemIO:
        io = BufferedSystemIO()

        task: LineInFileTask = LineInFileTask()
        mock_task(task, io=io)
        task.execute(mock_execution_context(task, params, envs))

        return io

    def test_simply_appends_line_if_it_does_not_exists(self):
        with NamedTemporaryFile() as tmp_file:
            self._execute_mocked_task({
                'file': tmp_file.name,
                '--output': '',
                '--regexp': 'Linux ([0-9.]+)',
                '--insert': 'Linux 4.16.1',
                '--fail-on-no-occurrence': False,
                '--only-first-occurrence': False,
                '--new-after-line': ''
            })

            self.assertEqual("Linux 4.16.1\n", tmp_file.read().decode('utf-8'))

    def test_simply_replaces_found_one_matched_line(self):
        with NamedTemporaryFile() as tmp_file:
            # at first add initial file content
            with open(tmp_file.name, 'w') as fw:
                fw.write('Text: Hello')

            # then modify it
            self._execute_mocked_task({
                'file': tmp_file.name,
                '--output': '',
                '--regexp': 'Text: (.*)',
                '--insert': 'Text: 14 June 1872 unions were legalised in Canada through the Trade Unions Act after a' +
                            ' wave of illegal strikes and protests. Still the law didn\'t compel employers to' +
                            ' recognise or bargain with unions, and picketing remained illegal.',
                '--fail-on-no-occurrence': False,
                '--only-first-occurrence': False,
                '--new-after-line': ''
            })

            self.assertIn("14 June 1872 unions were legalised in Canada", tmp_file.read().decode('utf-8'))

    def test_advanced_replaces_using_regexp_pattern(self):
        """Tests usage of regexp groups eg. $match[0], $match[1] etc."""

        with NamedTemporaryFile() as tmp_file:
            # at first add initial file content
            with open(tmp_file.name, 'w') as fw:
                fw.write('Symbol: 1')

            # then modify it
            self._execute_mocked_task({
                'file': tmp_file.name,
                '--output': '',
                '--regexp': 'Symbol: ([0-9]+)',
                '--insert': 'Symbol: $match[0] + 161',
                '--fail-on-no-occurrence': False,
                '--only-first-occurrence': False,
                '--new-after-line': ''
            })

            self.assertIn("Symbol: 1 + 161", tmp_file.read().decode('utf-8'))

    def test_fails_when_no_occurrence_and_flag_is_set(self):
        """Test flag --fail-on-no-occurrence"""

        with NamedTemporaryFile() as tmp_file:
            io = self._execute_mocked_task({
                'file': tmp_file.name,
                '--output': '',
                '--regexp': 'Knock knock',
                '--insert': 'Who\'s there?',
                '--fail-on-no-occurrence': True,
                '--only-first-occurrence': False,
                '--new-after-line': ''
            })

            self.assertIn('No matching line for selected regexp found', io.get_value())

    def test_replaces_only_first_occurrence(self):
        """Test that only one occurrence will be replaced"""

        with NamedTemporaryFile() as tmp_file:
            # at first add initial file content
            with open(tmp_file.name, 'w') as fw:
                fw.write("Symbol: 1\n")
                fw.write("Color: Red\n")
                fw.write("Symbol: 2\n")
                fw.write("\n\n")
                fw.write("Dog or cat: Dog\n")

            # then modify it
            self._execute_mocked_task({
                'file': tmp_file.name,
                '--output': '',
                '--regexp': 'Symbol: ([0-9]+)',
                '--insert': 'Symbol: 161',
                '--fail-on-no-occurrence': True,
                '--only-first-occurrence': True,
                '--new-after-line': ''
            })

            processed_file_content = tmp_file.read().decode('utf-8')

            self.assertIn("Symbol: 161", processed_file_content)
            self.assertNotIn("Symbol: 1\n", processed_file_content)
            self.assertIn("Symbol: 2", processed_file_content)

    def test_adds_multiple_lines_after_selected_marker(self):
        self.maxDiff = None

        task = LineInFileTask()
        task._io = BufferedSystemIO()

        result = task._insert_new_lines_if_necessary(
            False,
            '''
            Hijo del pueblo, te oprimen cadenas,
            y esa injusticia no puede seguir;
            si tu existencia es un mundo de penas
            antes que esclavo prefiere morir.
            En la batalla, la hiena fascista.
            por nuestro esfuerzo sucumbirá;
            y el pueblo entero, con los anarquistas,
            hará que triunfe la libertad.
            
            --- Read more --
            
            --- EOF
            ''',
            lines_to_insert='''            Trabajador, no más sufrir,
            el opresor ha de sucumbir.
            Levántate, pueblo leal,
            al grito de revolución social.
            Fuerte unidad de fe y de acción
            producirá la revolución.
            Nuestro pendón uno ha de ser:
            sólo en la unión está el vencer.'''.split("\n"),
            after_line_regexp='(.*)Read\ more(.*)',
            only_first_occurrence=True,
            regexp='.*Trabajador.*'
        )

        self.assertEqual(
            '''
            Hijo del pueblo, te oprimen cadenas,
            y esa injusticia no puede seguir;
            si tu existencia es un mundo de penas
            antes que esclavo prefiere morir.
            En la batalla, la hiena fascista.
            por nuestro esfuerzo sucumbirá;
            y el pueblo entero, con los anarquistas,
            hará que triunfe la libertad.
            
            --- Read more --
            Trabajador, no más sufrir,
            el opresor ha de sucumbir.
            Levántate, pueblo leal,
            al grito de revolución social.
            Fuerte unidad de fe y de acción
            producirá la revolución.
            Nuestro pendón uno ha de ser:
            sólo en la unión está el vencer.
            
            --- EOF
            ''',
            result,
        )

    def test_adds_missing_lines_after_specified_markers(self):
        task = LineInFileTask()
        task._io = BufferedSystemIO()

        result = task._insert_new_lines_if_necessary(
            False,
            '''
            Press list
            
            [@CNT]
            Other press
            Solidaridad Obrera
            
            [@FAI]
            Tierra y Libertad
            ''',
            lines_to_insert=['            Other press'],
            after_line_regexp='.*(CNT|FAI).*',
            only_first_occurrence=False,
            regexp='.*Other press'
        )

        self.assertEqual(
            '''
            Press list
            
            [@CNT]
            Other press
            Solidaridad Obrera
            
            [@FAI]
            Other press
            Tierra y Libertad
            ''',
            result
        )

    def test_lines_are_added_only_once_even_when_command_called_multiple_times(self):
        """Check that multiple invocations wont duplicate the line"""

        with NamedTemporaryFile() as tmp_file:
            for i in range(0, 10):
                self._execute_mocked_task({
                    'file': tmp_file.name,
                    '--output': '',
                    '--regexp': 'Bakunin ([0-9.]+)',
                    '--insert': 'Bakunin 5.16.%i' % i,
                    '--fail-on-no-occurrence': False,
                    '--only-first-occurrence': False,
                    '--new-after-line': ''
                })

            # "9" is because we have 9 iterations in range
            self.assertEqual("Bakunin 5.16.9\n", tmp_file.read().decode('utf-8'))