#!/usr/bin/env python3

import unittest
import unittest.mock
import os
from tempfile import NamedTemporaryFile
from rkd.context import ContextFactory
from rkd.context import ApplicationContext
from rkd.context import distinct_imports
from rkd.api.inputoutput import NullSystemIO
from rkd.exception import ContextException
from rkd.api.syntax import TaskDeclaration
from rkd.api.syntax import TaskAliasDeclaration
from rkd.api.syntax import GroupDeclaration
from rkd.test import TestTask
from rkd.standardlib import InitTask

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

    def test_context_remembers_directories_from_which_it_was_loaded(self):
        """Verify that whenever we merge contexts, the 'directories' attribute is also merged"""

        ctx1 = ApplicationContext([], [], '/home/iwa-ait')
        ctx2 = ApplicationContext([], [], '/home/black-lives-matters')

        ctx_merged = ApplicationContext.merge(ctx1, ctx2)

        self.assertEqual(['/home/iwa-ait'], ctx1.directories)
        self.assertEqual(['/home/iwa-ait', '/home/black-lives-matters'], ctx_merged.directories)

    def test_context_empty_path_is_not_applied_to_directories(self):
        """Test that '' path will not be added to directories list"""

        ctx = ApplicationContext([], [], '')

        self.assertEqual([], ctx.directories)
        self.assertEqual(0, len(ctx.directories))

    def test_distint_imports_on_py_file(self):
        """Case: PY file can define a variable IMPORTS that can contain both TaskDeclaration and TaskAliasDeclaration
        """

        with NamedTemporaryFile() as tmp_file:
            tmp_file.write(b'''
            from rkd.syntax import TaskAliasDeclaration as Task
            
            IMPORTS = [
                TaskAliasDeclaration(':hello', [':test'])
            ]
            ''')

            with unittest.mock.patch('rkd.context.os.path.isfile', return_value=True):
                with unittest.mock.patch('rkd.context.SourceFileLoader.load_module') as src_loader_method:
                    class TestImported:
                        IMPORTS = []
                        TASKS = []

                    src_loader_method.return_value = TestImported()
                    src_loader_method.return_value.IMPORTS = [TaskAliasDeclaration(':hello', [':test'])]
                    src_loader_method.return_value.TASKS = []

                    ctx_factory = ContextFactory(NullSystemIO())
                    ctx = ctx_factory._load_from_py(tmp_file.name)

                    self.assertIn(':hello', ctx._task_aliases)

    def test_distinct_imports_on_yaml_file(self):
        """Case: YAML file can import a module that contains imports() method
        And that method returns list of Union[TaskDeclaration, TaskAliasDeclaration]
        """

        with NamedTemporaryFile() as tmp_file:
            tmp_file.write(b'''
            version: org.riotkit.rkd/yaml/v1
            imports:
                - fictional
            ''')

            with unittest.mock.patch('rkd.context.YamlSyntaxInterpreter.parse') as parse_method:
                parse_method.return_value = ([TaskAliasDeclaration(':hello', [':test'])], [])

                ctx_factory = ContextFactory(NullSystemIO())
                ctx = ctx_factory._load_from_yaml(os.path.dirname(tmp_file.name), os.path.basename(tmp_file.name))

                self.assertIn(':hello', ctx._task_aliases)

    def test_distinct_imports_raises_exception_when_unknown_type_object_added_to_list(self):
        self.assertRaises(ContextException,
                          lambda: distinct_imports('hello', ['string-should-not-be-there-even-IDE-knows-that']))

    def test_distinct_imports_does_not_raise_any_exception_when_no_data(self):
        self.assertEqual(([], []), distinct_imports('hello', []))

    def test_distinct_imports_separtes_lists(self):
        """A successful case for distinct_imports()"""

        imports, aliases = distinct_imports('hello', [
            TaskDeclaration(TestTask()),
            TaskAliasDeclaration(':hello', [':test'])
        ])

        self.assertTrue(isinstance(imports[0], TaskDeclaration))
        self.assertTrue(isinstance(aliases[0], TaskAliasDeclaration))

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

    def test_context_resolves_recursively_task_aliases(self):
        ctx = ApplicationContext([
            TaskDeclaration(InitTask())
        ], [
            TaskAliasDeclaration(':deeper', [':init', ':init']),
            TaskAliasDeclaration(':deep', [':init', ':deeper'])
        ], directory='')

        ctx.compile()
        task = ctx.find_task_by_name(':deep')
        task: GroupDeclaration

        # :deeper = :init
        # :deep = :init :deeper = :init :init :init
        self.assertEqual(':init', task.get_declarations()[0].to_full_name())
        self.assertEqual(':init', task.get_declarations()[1].to_full_name())
        self.assertEqual(':init', task.get_declarations()[2].to_full_name())
