#!/usr/bin/env python3

import os
import subprocess
from io import StringIO
from rkd.api.testing import BasicTestingCase
from rkd.process import carefully_decode, check_call, switched_workdir
from rkd.api.inputoutput import IO


class TestProcess(BasicTestingCase):
    def test_carefully_decode(self) -> None:
        self.assertEqual(' world', carefully_decode(u'æ'.encode('cp1252') + b' world', 'utf-8'))

    def test_streaming_callback_exception_does_not_hang_application_but_actually_raise_exception(self) -> None:
        def callback(text: str) -> None:
            if "test" in text:
                raise Exception('Found "test"')

        with self.assertRaises(Exception):
            check_call('/bin/bash -c "sleep 1; echo "test"; sleep 100;"', output_capture_callback=callback)

            # assert that "sleep 100" is not executing (exit code 1)
            with self.assertRaises(subprocess.CalledProcessError):
                check_call('ps aux |grep "sleep 100" | grep -v grep')

    def test_environment_is_passed_and_system_environment_still_available(self) -> None:
        os.environ['COMING_FROM_PARENT_CONTEXT'] = 'Buenaventura Durruti'

        io = IO()
        out = StringIO()

        try:
            with io.capture_descriptors(stream=out, enable_standard_out=False):
                check_call('env', env={'PROTEST_TYPE': 'Sabotage'})

        finally:
            del os.environ['COMING_FROM_PARENT_CONTEXT']

        self.assertIn('PROTEST_TYPE=Sabotage', out.getvalue())
        self.assertIn('COMING_FROM_PARENT_CONTEXT=Buenaventura Durruti', out.getvalue())

    def test_switched_workdir(self) -> None:
        original_cwd = os.getcwd()

        try:
            with switched_workdir('/tmp'):
                self.assertEqual('/tmp', os.getcwd())

        finally:
            self.assertEqual(original_cwd, os.getcwd())
