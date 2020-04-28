#!/usr/bin/env python3

import unittest
import os
from rkd.context import ContextFactory
from rkd.context import Context

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class ContextTest(unittest.TestCase):
    def test_loads_internal_context(self) -> None:
        discovery = ContextFactory()
        ctx = discovery._load_context_from_directory(CURRENT_SCRIPT_PATH + '/../src/rkd/internal')

        self.assertTrue(isinstance(ctx, Context))

    def test_loads_internal_context_in_unified_context(self) -> None:
        discovery = ContextFactory()
        ctx = discovery.create_unified_context()

        print(ctx._imported_tasks)

        print(ctx)
