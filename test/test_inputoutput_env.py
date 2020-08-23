#!/usr/bin/env python3

import unittest
import os
from rkd.api.inputoutput import get_environment_copy


class TestIOEnv(unittest.TestCase):
    def test_get_environment_copy(self):
        # prepare test data
        os.environ['FIRST'] = '$SECOND'

        # get result
        copy = get_environment_copy()

        self.assertEqual('\$SECOND', copy['FIRST'])
