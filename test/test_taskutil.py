#!/usr/bin/env python3

import unittest.mock
import os
import psutil
import subprocess
from tempfile import NamedTemporaryFile
from collections import OrderedDict
from io import StringIO
from rkd.api.testing import BasicTestingCase, OutputCapturingSafeTestCase
from rkd.standardlib import InitTask
from rkd.api.inputoutput import IO

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class TestTaskUtil(BasicTestingCase, OutputCapturingSafeTestCase):
    def test_sh_accepts_script_syntax(self):
        task = InitTask()
        task._io = IO()
        self.assertIn('__init__.py', task.sh("ls -la\npwd", capture=True))

    def test_exec_spawns_process(self):
        task = InitTask()
        task._io = IO()
        self.assertIn('__init__.py', task.exec('ls', capture=True))

    def test_sh_executes_in_background(self):
        task = InitTask()
        task._io = IO()
        task.exec('ls', background=True)

    def test_exec_background_capture_validation_raises_error(self):
        def test():
            task = InitTask()
            task._io = IO()
            task.exec('ls', background=True, capture=True)

        self.assertRaises(Exception, test)

    def test_sh_captures_output_in_correct_order_with_various_timing(self):
        """Test if output is containing stdout and stderr lines mixed in proper order (as it is defined in shell script)

        Notice: Test is interacting with shell, to reduce possibility of weird behavior it is retried multiple times
        """
        for i in range(1, 100):
            self.maxDiff = None  # unittest setting
            task = InitTask()
            task._io = IO()

            io = IO()
            out = StringIO()

            with io.capture_descriptors(stream=out, enable_standard_out=False):
                task.sh(''' set +e;
                    sleep 0.05;
                    echo "FIRST";
                    sleep 0.05;
                    echo "SECOND" >&2;
                    echo "THIRD";
                    echo "FOURTH" >&2;
                    echo "FIFTH" >&2;
                    echo "SIXTH";
                    echo "SEVENTH" >&2;
                    echo "NINETH";
                    echo "TENTH";
                ''')

            self.assertEqual("FIRST\r\nSECOND\r\nTHIRD\r\nFOURTH\r\nFIFTH\r\nSIXTH\r\nSEVENTH\r\nNINETH\r\nTENTH\r\n", out.getvalue())

    def test_sh_producing_large_outputs(self):
        """Process a few megabytes of output and assert that:

        - It will consume not more than 10 megabytes (assuming also output capturing in tests by io.capture_descriptors())
        - The whole output would be printed correctly
        """

        self.maxDiff = None  # unittest setting
        task = InitTask()
        task._io = IO()

        io = IO()
        out = StringIO()
        text = "History isn't made by kings and politicians, it is made by us."

        memory_before = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

        with io.capture_descriptors(stream=out, enable_standard_out=False):
            task.py('''
for i in range(0, 1024 * 128):
    print("''' + text + '''")
            ''')

        iterations = 1024 * 128
        text_with_newlines_length = len(text) + 2  # \r + \n
        memory_after = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

        self.assertEqual(iterations * text_with_newlines_length, len(out.getvalue()))
        self.assertLessEqual(memory_after - memory_before, 16, msg='Expected less than 16 megabytes of memory usage')

    def test_sh_captures_output_in_correct_order_with_fixed_timing(self):
        """Test if output contains stdout and stderr lines printed out in proper order,
        while there is a sleep between prints

        Notice: Test is interacting with shell, to reduce possibility of weird behavior it is retried multiple times
        """

        for i in range(1, 30):
            self.maxDiff = None  # unittest setting
            task = InitTask()
            task._io = IO()

            io = IO()
            out = StringIO()

            with io.capture_descriptors(stream=out, enable_standard_out=False):
                task.sh(''' set +e;
                    sleep 0.05;
                    echo "FIRST";
                    sleep 0.05;
                    echo "SECOND" >&2;
                    sleep 0.05;
                    echo "THIRD";
                ''')

            self.assertEqual("FIRST\r\nSECOND\r\nTHIRD\r\n", out.getvalue())

    def test_sh_rkd_in_rkd_shows_first_lines_on_error(self):
        """Bugfix: sh() was loosing first line(s) of output, when exception was raised

        Notice: Test is interacting with shell, to reduce possibility of weird behavior it is retried multiple times
        """

        for i in range(1, 5):
            for std_redirect in ['', '>&2']:
                task = InitTask()
                task._io = IO()
                io = IO()
                out = StringIO()

                with io.capture_descriptors(stream=out, enable_standard_out=False):
                    try:
                        task.sh(''' 
                            python3 -m rkd --silent :sh -c 'echo "Bartolomeo Vanzetti" ''' + std_redirect + '''; exit 127'
                        ''')
                    except subprocess.CalledProcessError:
                        pass

                self.assertIn('Bartolomeo Vanzetti', out.getvalue(),
                              msg='Expected that output will be shown for std_redirect=%s' % std_redirect)

    def test_non_interactive_session_returns_output(self):
        """Checks functionally if process.py is implementing a fall-back for non-interactive sessions

        'true |' part enforces the console to be non-interactive, which should cause
        "termios.error: (25, 'Inappropriate ioctl for device')" that should be handled and interactive mode
        should be turned off for stdin
        """

        task = InitTask()
        task._io = IO()
        io = IO()
        out = StringIO()

        with io.capture_descriptors(stream=out, enable_standard_out=False):
            task.sh(''' true | python3 -m rkd --silent :sh -c 'echo "Strajk Kobiet! Jebac PiS!"' ''')

        self.assertIn('Strajk Kobiet! Jebac PiS!', out.getvalue())

    def test_full_command_is_shown_only_in_debug_output_level(self):
        """Test that sh() will show full bash script only in case, when '-rl debug' is used

        :return:
        """

        task = InitTask()
        task._io = IO()
        io = IO()
        out = StringIO()

        with io.capture_descriptors(stream=out, enable_standard_out=False):
            # CASE 1
            with self.subTest('NORMAL output level'):
                try:
                    task.sh('python3 -m rkd :sh -c "exit 5"')

                except subprocess.CalledProcessError as e:
                    self.assertIn("Command 'exit 5' returned non-zero exit status 5.", e.output)

            # CASE 2
            with self.subTest('DEBUG output level'):
                try:
                    task.sh('python3 -m rkd -rl debug :sh -c "exit 5"')

                except subprocess.CalledProcessError as e:
                    self.assertIn("Command '#!/bin/bash -eopipefail \r\nset -euo pipefail; export " +
                                  "PYTHONUNBUFFERED=1; exit 5' returned non-zero exit status 5.", e.output)

    def test_dollar_symbols_are_escaped_in_shell_commands(self):
        """Check that in envrionment variable there can be defined a value that contains dollar symbols"""

        task = InitTask()
        task._io = IO()
        io = IO()
        out = StringIO()

        with io.capture_descriptors(stream=out, enable_standard_out=False):
            task.sh('env | grep TEST_ENV', env={
                'TEST_ENV': 'Mikhail\$1Bakunin\$PATHtest',
                'TEST_ENV_NOT_ESCAPED': 'Hello $TEST_ENV'
            })

        self.assertIn('TEST_ENV=Mikhail$1Bakunin$PATHtest', out.getvalue())
        self.assertIn('TEST_ENV_NOT_ESCAPED=Hello Mikhail$1Bakunin$PATHtest', out.getvalue())

    def test_quotes_are_escaped_in_shell_commands(self):
        task = InitTask()
        task._io = IO()
        io = IO()
        out = StringIO()

        with io.capture_descriptors(stream=out, enable_standard_out=False):
            task.sh('echo ${NAME}', env={
                'NAME': 'Ferdinando "Nicola" Sacco'
            })

        self.assertIn('Ferdinando "Nicola" Sacco', out.getvalue())

    def test_sh_3rd_depth_rkd_calls(self):
        """Bugfix: sh() of 3-depth calls -> test -> rkd -> rkd returns first line of output
        """

        for std_redirect in ['', '>&2']:
            task = InitTask()
            task._io = IO()
            io = IO()
            out = StringIO()

            with io.capture_descriptors(stream=out, enable_standard_out=False):
                try:
                    task.sh(''' 
                        python3 -m rkd --silent :sh -c 'python -m rkd --silent :sh -c \'echo "Nicola Sacco" ''' + std_redirect + '''; exit 1\''
                    ''')
                except subprocess.CalledProcessError:
                    pass

            self.assertIn('Nicola Sacco', out.getvalue(),
                          msg='Expected that output will be shown for std_redirect=%s' % std_redirect)

    @unittest.skip("Github issue #1")
    def test_sh_provides_stdout_and_stderr_in_exception(self):
        task = InitTask()
        task._io = IO()

        try:
            task.sh('''
                echo "Freedom, Equality, Mutual Aid!"
                echo "The state and capitalism is failing" >&2

                exit 161
            ''')
        except subprocess.CalledProcessError as e:
            self.assertEqual("Freedom, Equality, Mutual Aid!\n", e.output)
            self.assertEqual("The state and capitalism is failing\n", e.stderr)

    def test_sh_has_valid_order_of_defining_environment_variables(self):
        """Checks if built-in sh() method is registering variables in proper order
        """

        task = InitTask()
        task._io = IO()

        envs = OrderedDict()
        envs['ENV_NAME'] = 'riotkit'
        envs['COMPOSE_CMD'] = 'docker-compose -p ${ENV_NAME}'

        out = task.sh('''
            echo "${COMPOSE_CMD} up -d"
        ''', env=envs, capture=True)

        self.assertEqual('docker-compose -p riotkit up -d', out.strip())

    def test_py_executes_python_scripts_without_specifying_script_path(self):
        """Simply - check basic successful case - executing a Python code"""

        task = InitTask()
        task._io = IO()
        out = task.py('''
import os
print(os)
        ''', capture=True)

        self.assertIn("<module 'os' from", out)

    def test_py_executes_a_custom_python_script(self):
        """Check that script from specified file in 'script_path' parameter will be executed
        And the code will be passed to that script as stdin.
        """

        task = InitTask()
        task._io = IO()

        with NamedTemporaryFile() as temp_file:
            temp_file.write(b'import sys; print(sys.argv[1])')
            temp_file.flush()

            out = task.py('', capture=True, script_path=temp_file.name, arguments='Hello!')

        self.assertEqual('Hello!\n', out)

    def test_py_inherits_environment_variables(self):
        os.putenv('PY_INHERITS_ENVIRONMENT_VARIABLES', 'should')

        task = InitTask()
        task._io = IO()
        out = task.py(
            code='import os; print("ENV VALUE IS: " + str(os.environ["PY_INHERITS_ENVIRONMENT_VARIABLES"]))',
            capture=True
        )

        self.assertEqual('ENV VALUE IS: should\n', out)

    def test_py_uses_sudo_when_become_specified(self):
        """Expect that sudo with proper parameters is used"""

        task = InitTask()
        task._io = IO()

        with unittest.mock.patch('rkd.taskutil.check_output') as mocked_subprocess:
            mocked_subprocess: unittest.mock.MagicMock
            task.py(code='print("test")', capture=True, become='root')

        self.assertIn('sudo -E -u root python', mocked_subprocess.call_args[0][0])
