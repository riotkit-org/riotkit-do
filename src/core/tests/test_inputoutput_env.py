#!/usr/bin/env python3

import os
from rkd.core.api.testing import BasicTestingCase
from rkd.core.api.inputoutput import get_environment_copy


class TestIOEnv(BasicTestingCase):
    def test_get_environment_copy(self):
        # prepare test data
        os.environ['FIRST'] = '$SECOND'

        # get result
        copy = get_environment_copy()

        self.assertEqual("\\$SECOND", copy['FIRST'])
