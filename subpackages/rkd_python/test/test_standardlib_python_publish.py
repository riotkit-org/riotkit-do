#!/usr/bin/env python3

import unittest
import subprocess


class PublishTaskTest(unittest.TestCase):
    def _call_publish_via_shell(self, arguments: str):
        try:
            out = subprocess.check_output('''
                export RKD_PATH=$(pwd)/../example/.rkd
                
                cd ../
                python3 -m rkd --silent :sh -c "python3 -m rkd --silent :py:publish ''' + arguments + '''"
            ''', shell=True)
        except subprocess.CalledProcessError as e:
            return e.output

        return out

    def test_integration_is_output_properly_catch_by_sh(self):
        """Case: In the past there were problems with output displaying by RKD-in-RKD - sh('rkd :py:publish ...')

        Integration test with TaskUtilities.sh()
        """

        out = self._call_publish_via_shell('--username=wrong --password=wrong --test').decode('utf-8')
        self.assertIn('403 Invalid or non-existent authentication information.', out)
        self.assertIn('Uploading distributions to https://test.pypi.org', out)
