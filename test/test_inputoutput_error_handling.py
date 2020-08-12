#!/usr/bin/env python3

import sys
import unittest
from rkd.api.inputoutput import BufferedSystemIO
from rkd.api.inputoutput import output_formatted_exception
from rkd.api.inputoutput import indent_new_lines


class TestIOErrorHandling(unittest.TestCase):
    def test_is_information_written_through_stderr_methods(self):
        """To check if information is written to the proper methods we will mock stdout methods"""

        io = BufferedSystemIO()
        io._stdout = lambda *args, **kwargs: None

        try:
            raise IndexError('Invalid index 5')
        except Exception as exc:
            output_formatted_exception(exc, ':my-test-task', io)

        self.assertIn('IndexError', io.get_value())
        self.assertIn('Invalid index 5', io.get_value())
        self.assertIn('Retry with "-rl debug" switch before failed task to see stacktrace', io.get_value())

    def test_are_chained_exceptions_printed(self):
        """Check if there are multiple exceptions, then those would be printed as a cause"""

        io = BufferedSystemIO()

        try:
            try:
                raise IndexError('Invalid index 5')
            except IndexError as index_exc:
                raise Exception('There was an error with index') from index_exc

        except Exception as exc:
            output_formatted_exception(exc, ':my-test-task', io)

        self.assertIn('(Caused by) IndexError:', io.get_value())
        self.assertIn('Exception:', io.get_value())
        self.assertIn('There was an error with index', io.get_value())

    def test_fatal_error_would_be_thrown_in_case_of_a_formatting_failure(self):
        """Tests very important functionality - in case of a failure in the error formatting there must be a fallback
        that will work for sure - a simple print() of stacktrace and proper exit code
        """

        def mock_fatal(*args, **kwargs):
            raise Exception('Fatal!')

        io = BufferedSystemIO()
        io.print_line = mock_fatal

        exit_code = 0

        try:
            raise IndexError('Invalid index 5')
        except Exception as exc:
            stdout_bckp = sys.stdout  # needed to silence the output in tests (we do not want this stack trace in tests)

            try:
                with open('/dev/null', 'w') as sys.stdout:
                    output_formatted_exception(exc, ':my-test-task', io)

            except SystemExit as sys_exit:
                exit_code = sys_exit.code
            finally:
                sys.stdout = stdout_bckp  # restore stdout

        self.assertEqual(1, exit_code)

    def test_indent_new_lines(self):
        self.assertIn("\n      ", indent_new_lines("Line1\nLine2", 6))
