#!/usr/bin/env python3

import unittest
import os
from rkd.standardlib import InitTask

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class TestTaskInterface(unittest.TestCase):
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
