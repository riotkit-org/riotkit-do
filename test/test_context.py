#!/usr/bin/env python3

import unittest
import os
from rkd.context import ContextFactory
from rkd.context import Context
from rkd.inputoutput import NullSystemIO

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class ContextTest(unittest.TestCase):
    def test_loads_internal_context(self) -> None:
        discovery = ContextFactory(NullSystemIO())
        ctx = discovery._load_context_from_directory(CURRENT_SCRIPT_PATH + '/../src/rkd/internal')

        self.assertTrue(isinstance(ctx, Context))

    def test_loads_internal_context_in_unified_context(self) -> None:
        """
        Check if application loads context including paths from RKD_PATH
        :return:
        """

        os.environ['RKD_PATH'] = CURRENT_SCRIPT_PATH + '/../docs/examples/makefile-like/.rkd'

        try:
            discovery = ContextFactory(NullSystemIO())
            ctx = discovery.create_unified_context()

            # :find-images is defined in docs/examples/makefile-like/.rkd/makefile.py as an alias type task
            self.assertIn(':find-images', ctx.find_all_tasks().keys())
        except:
            raise
        finally:
            os.environ['RKD_PATH'] = ''
