#!/usr/bin/env python3

import sys
from rkd.api.testing import BasicTestingCase, OutputCapturingSafeTestCase
from rkd.api.inputoutput import IO
from rkd.api.inputoutput import SystemIO
from rkd.api.inputoutput import BufferedSystemIO
from rkd.api.inputoutput import clear_formatting


class TestIO(BasicTestingCase, OutputCapturingSafeTestCase):
    def test_is_log_level_at_least_info(self):
        """Test error level comparison

        Covers: IO.set_log_level() and IO.is_log_level_at_least()
        """

        io = IO()
        io.set_log_level('info')

        self.assertFalse(io.is_log_level_at_least('debug'))
        self.assertTrue(io.is_log_level_at_least('info'))
        self.assertTrue(io.is_log_level_at_least('warning'))
        self.assertTrue(io.is_log_level_at_least('fatal'))

    def test_set_log_level_cannot_set_invalid_log_level(self):
        """Checks validation in IO.set_log_level()"""

        io = IO()
        self.assertRaises(Exception, lambda: io.set_log_level('strikebreaker'))

    def test_inherit_silent(self):
        """Silent mode inheritance from SystemIO"""

        sys_io = SystemIO()
        sys_io.silent = True

        io = IO()
        io.inherit_silent(sys_io)

        self.assertTrue(io.is_silent())

    def test_formatting_methods_are_clearing_formatting_at_the_end(self):
        """Check that formatting methods are clearing the formatting at the end"""

        io = BufferedSystemIO()

        methods = [
            io.h1, io.h2, io.h3, io.h4, io.success_msg, io.error_msg, io.info_msg, io.print_separator, io.print_group
        ]

        for method in methods:
            try:
                method('test')
            except TypeError:
                method()

            self.assertEqual("\x1B[", io.get_value()[0:2], msg='Expected beginning of formatting')
            self.assertEqual('[0m', io.get_value().strip()[-3:], msg='Expected formatting clearing at the end')
            io.clear_buffer()

    def test_formatting_methods_are_printing_output_as_optional(self):
        """Expects that pretty-printed messages will be optional"""

        io = BufferedSystemIO()

        methods = [
            io.h1, io.h2, io.h3, io.h4, io.success_msg, io.error_msg, io.info_msg, io.print_separator, io.print_group
        ]

        for method in methods:
            self.__setattr__('is_text_optional', False)

            def opt_outln(text: str):
                self.__setattr__('is_text_optional', True)

            io.opt_outln = opt_outln

            try:
                method('test')
            except TypeError:
                method()

            self.assertTrue(self.__getattribute__('is_text_optional'),
                            msg='%s: Expected that the text will be printed through opt_outln()' % str(method))

    def test_get_log_level_raises_exception_on_unset_level(self):
        """Check DEFAULT error level and validation of not set error logging"""

        io = IO()

        self.assertEqual('info', io.get_log_level())

        io.log_level = None
        self.assertRaises(Exception, lambda: io.get_log_level())

    def test_clear_formatting_clears_simple_bash_coloring(self):
        """Test that clear_formatting() clears basic Bash coloring"""

        colored = """\x1B[93m10 June 1927 in Italy, the trial of anarchist Gino Lucetti concluded for 
attempting to assassinate Mussolini.
He was sentenced to 30 years in prison; two others received 12 years. 
He was killed by shelling in 1943 before the end of the war\x1B[0m"""

        without_coloring = clear_formatting(colored)

        self.assertFalse(without_coloring.startswith("\x1B[93m"))
        self.assertFalse(without_coloring.endswith("\x1B[0m"))

    def test_io_capturing_is_restoring_both_stdout_and_stderr_to_previous_state(self):
        """Assert that capture_descriptors() restores sys.stdout and sys.stderr to original state after
        mocking them for output capturing"""

        io = IO()

        stdout_backup = sys.stdout
        stderr_backup = sys.stderr

        with io.capture_descriptors(target_files=None):
            pass

        self.assertEqual(stdout_backup, sys.stdout)
        self.assertEqual(stderr_backup, sys.stderr)
