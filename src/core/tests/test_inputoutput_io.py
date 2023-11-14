#!/usr/bin/env python3

import sys
from rkd.core.api.testing import BasicTestingCase, OutputCapturingSafeTestCase
from rkd.core.api.inputoutput import IO
from rkd.core.api.inputoutput import SystemIO
from rkd.core.api.inputoutput import BufferedSystemIO
from rkd.core.api.inputoutput import clear_formatting


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
            io.h1, io.h2, io.h3, io.h4, io.success_msg, io.info_msg, io.print_separator, io.print_group
        ]

        for method in methods:
            self.__setattr__('is_text_optional', False)

            def opt_outln(text: str):
                self.__setattr__('is_text_optional', True)

            io.opt_outln = opt_outln
            io.opt_errln = opt_outln

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

    def test_io_output_processing_changes_output(self):
        """
        Tests adding "[stdout]" and "[stderr]" prefixes to the output
        """

        mocked_output = []

        io = IO()
        io.set_log_level('info')
        io._stderr = io._stdout = lambda txt: mocked_output.append(txt)

        # add a processor that will append origin - "stdout" or "stderr"
        io.add_output_processor(lambda txt, origin: '[{}]: {}'.format(origin, txt))

        io.info('Hello from stdout')
        io.error('Hello from stderr')

        mocked_output_as_str = " ".join(mocked_output)

        self.assertIn('[stdout]: \x1b', mocked_output_as_str)
        self.assertIn('[stderr]: \x1b', mocked_output_as_str)

    def test_io_output_processing_does_not_break_on_exception_in_processing_method_when_error_level_is_not_debug(self):
        """
        Verify error handling - when level is not "debug", then no any error should be present from processors
        because we cannot mess with the I/O that is written to the console
        """

        mocked_output = []

        io = IO()
        io.set_log_level('info')
        io._stderr = io._stdout = lambda txt: mocked_output.append(txt)

        def processor_that_raises_exceptions(txt, origin):
            raise Exception('Hello')

        io.add_output_processor(processor_that_raises_exceptions)

        io.info('26 Jan 1932 4000 mainly Jewish tenants in New York attacked police reserve forces who were trying ' +
                'to evict 17 tenants. The mob was led by women on rooftops who directed the action with megaphones ' +
                'and hurled missiles at police.')

        self.assertIn('were trying to evict 17 tenants', str(mocked_output))

    def test_io_output_processing_is_raising_exception_in_debug_mode(self):
        """
        Error handling - when level is "debug", then we should be raising exceptions
        """

        mocked_output = []

        io = IO()
        io.set_log_level('debug')
        io._stderr = io._stdout = lambda txt: mocked_output.append(txt)

        def processor_that_raises_exceptions(txt, origin):
            raise Exception('Hello')

        io.add_output_processor(processor_that_raises_exceptions)

        with self.assertRaises(Exception):
            io.info('There will be no shelter here')

    def test_io_output_processing_is_raising_exception_when_invalid_type_returned_in_debug_mode(self):
        """
        Error handling - when level is "debug", then we should be raising exceptions
        Variant: returned invalid type (not a STR - returned INT)
        """

        mocked_output = []

        io = IO()
        io.set_log_level('debug')
        io._stderr = io._stdout = lambda txt: mocked_output.append(txt)

        def processor_that_raises_exceptions(txt, origin):
            return 123456

        # noinspection PyTypeChecker
        io.add_output_processor(processor_that_raises_exceptions)

        with self.assertRaises(Exception):
            io.info('Face the facts, no thanks, "Your passport lacks stamps Please go back for war, ' +
                    'torture and the death camps" Join the ranks, labeled as illegal people, Cursed by those who ' +
                    'suck blood from golden calf’s nipple')

    def test_table(self):
        """Simply test format_table() - the table is expected to use an external library, it is expected that external library
        will be tested already, but we need to check there if the interface matches
        """

        io = IO()
        out = io.format_table(
            header=['Activist', 'Born date'],
            body=[
                ['Mikhail Alexandrovich Bakunin', '1814'],
                ['Errico Malatesta', '1853'],
                ['José Buenaventura Durruti Dumange', '1896'],
                ['Johann Rudolf Rocker', '1873']
            ]
        )

        self.assertIn('---------------------------------', out)
        self.assertIn('Mikhail Alexandrovich Bakunin', out)
        self.assertIn('Johann Rudolf Rocker', out)
        self.assertIn('Activist', out)
        self.assertIn('Born date', out)