#!/usr/bin/env python3

import unittest
import os
from rkd.context import ContextFactory
from rkd.context import ApplicationContext
from rkd.inputoutput import NullSystemIO

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class ContextTest(unittest.TestCase):
    def test_loads_internal_context(self) -> None:
        """Test if internal context (RKD by default has internal context) is loaded properly
        """
        discovery = ContextFactory(NullSystemIO())
        ctx = discovery._load_context_from_directory(CURRENT_SCRIPT_PATH + '/../src/rkd/internal')

        self.assertTrue(isinstance(ctx, ApplicationContext))

    def test_loads_internal_context_in_unified_context(self) -> None:
        """Check if application loads context including paths from RKD_PATH
        """

        os.environ['RKD_PATH'] = CURRENT_SCRIPT_PATH + '/../docs/examples/makefile-like/.rkd'
        ctx = None

        try:
            discovery = ContextFactory(NullSystemIO())
            ctx = discovery.create_unified_context()
        except:
            raise
        finally:
            self.assertIn(
                ':find-images',
                ctx.find_all_tasks().keys(),
                msg=':find-images is defined in docs/examples/makefile-like/.rkd/makefile.py as an alias type task' +
                    ', expected that it would be loaded from path placed at RKD_PATH'
            )

            os.environ['RKD_PATH'] = ''

    def test_loads_when_only_yaml_file_is_in_directory(self):
        """Check if tasks will be loaded when in .rkd there is only a YAML file
        """

        self._common_test_loads_task_from_file(
            path=CURRENT_SCRIPT_PATH + '/../docs/examples/yaml-only/.rkd',
            task=':hello',
            filename='makefile.yaml'
        )

    def test_loads_when_only_py_file_is_in_directory(self):
        """Check if tasks will be loaded when in .rkd there is only a YAML file
        """

        self._common_test_loads_task_from_file(
            path=CURRENT_SCRIPT_PATH + '/../docs/examples/python-only/.rkd',
            task=':hello-python',
            filename='makefile.py'
        )

    def _common_test_loads_task_from_file(self, path: str, task: str, filename: str):
        os.environ['RKD_PATH'] = path
        ctx = None

        try:
            discovery = ContextFactory(NullSystemIO())
            ctx = discovery.create_unified_context()
        except:
            raise
        finally:
            self.assertIn(task, ctx.find_all_tasks().keys(),
                          msg='Expected that %s task would be loaded from %s' % (task, filename))

            os.environ['RKD_PATH'] = ''
