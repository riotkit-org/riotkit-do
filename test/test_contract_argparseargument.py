#!/usr/bin/env python3

import unittest.mock
from rkd.contract import ArgparseArgument


class TestArgparseArgument(unittest.TestCase):
    def test_arguments_are_registered(self):
        arg = ArgparseArgument(['--name', '-n'], {'default': 'Michail Bakunin'})

        self.assertEqual(['--name', '-n'], arg.args)
        self.assertEqual({'default': 'Michail Bakunin'}, arg.kwargs)
