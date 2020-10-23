#!/usr/bin/env python3

from rkd.api.testing import BasicTestingCase
from rkd.contract import env_to_switch
from rkd.contract import ArgumentEnv
from rkd.exception import EnvironmentVariableNameNotAllowed


class ArgumentEnvTest(BasicTestingCase):
    def test_env_to_switch(self):
        self.assertEqual('--michael-brown', env_to_switch('MICHAEL_BROWN'))

    def test_reserved_vars_are_not_allowed(self):
        reserved_vars = ['PATH', 'PWD', 'LANG', 'DISPLAY', 'SHELL', 'SHLVL', 'HOME', 'EDITOR']

        for var_name in reserved_vars:
            with self.subTest('Environment variable "%s" should be disallowed' % var_name):
                self.assertRaises(EnvironmentVariableNameNotAllowed,
                                  lambda: ArgumentEnv(name=var_name))

    def test_not_reserved_vars_are_allowed(self):
        not_reserved_examples = ['COMMAND', 'RKD_CMD']

        for var_name in not_reserved_examples:
            with self.subTest('Environment variable "%s" should be allowed to declare' % var_name):
                self.assertIsInstance(ArgumentEnv(name=var_name), ArgumentEnv)
