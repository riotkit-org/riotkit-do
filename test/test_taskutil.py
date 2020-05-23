#!/usr/bin/env python3

import unittest
import os
import subprocess
from collections import OrderedDict
from io import StringIO
from rkd.standardlib import InitTask
from rkd.inputoutput import IO

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class TestTaskUtil(unittest.TestCase):
    def test_sh_accepts_script_syntax(self):
        task = InitTask()
        self.assertIn('__init__.py', task.sh("ls -la\npwd", capture=True))

    def test_exec_spawns_process(self):
        task = InitTask()
        self.assertIn('__init__.py', task.exec('ls', capture=True))

    def test_sh_executes_in_background(self):
        task = InitTask()
        task.exec('ls', background=True)

    def test_exec_background_capture_validation_raises_error(self):
        def test():
            task = InitTask()
            task.exec('ls', background=True, capture=True)

        self.assertRaises(Exception, test)

    def test_sh_captures_output_in_correct_order_with_various_timing(self):
        """Test if output is containing stdout and stderr lines mixed in proper order (as it is defined in shell script)

        Notice: Test is interacting with shell, to reduce possibility of weird behavior it is retried multiple times
        """
        for i in range(1, 50):
            self.maxDiff = None  # unittest setting
            task = InitTask()

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
                ''')

            self.assertEqual("FIRST\nSECOND\nTHIRD\nFOURTH\nFIFTH\n", out.getvalue())

    def test_sh_captures_output_in_correct_order_with_fixed_timing(self):
        """Test if output contains stdout and stderr lines printed out in proper order,
        while there is a sleep between prints

        Notice: Test is interacting with shell, to reduce possibility of weird behavior it is retried multiple times
        """

        for i in range(1, 30):
            self.maxDiff = None  # unittest setting
            task = InitTask()

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

            self.assertEqual("FIRST\nSECOND\nTHIRD\n", out.getvalue())

    def test_sh_rkd_in_rkd_shows_first_lines_on_error(self):
        """Bugfix: sh() was loosing first line(s) of output, when exception was raised

        Notice: Test is interacting with shell, to reduce possibility of weird behavior it is retried multiple times
        """

        for i in range(1, 5):
            for std_redirect in ['', '>&2']:
                task = InitTask()
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

    def test_sh_3rd_depth_rkd_calls(self):
        """Bugfix: sh() of 3-depth calls -> test -> rkd -> rkd returns first line of output
        """

        for std_redirect in ['', '>&2']:
            task = InitTask()
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

        envs = OrderedDict()
        envs['ENV_NAME'] = 'riotkit'
        envs['COMPOSE_CMD'] = 'docker-compose -p ${ENV_NAME}'

        out = task.sh('''
            echo "${COMPOSE_CMD} up -d"
        ''', env=envs, capture=True)

        self.assertEqual('docker-compose -p riotkit up -d', out.strip())
