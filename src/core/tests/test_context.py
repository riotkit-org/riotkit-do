#!/usr/bin/env python3

import unittest
import unittest.mock
import os
from tempfile import NamedTemporaryFile
from unittest import mock
from rkd.core.context import ContextFactory
from rkd.core.context import ApplicationContext
from rkd.core.context import distinct_imports
from rkd.core.api.inputoutput import NullSystemIO, IO, SystemIO
from rkd.core.dto import StaticFileContextParsingResult
from rkd.core.exception import ContextException
from rkd.core.api.syntax import TaskDeclaration, Pipeline
from rkd.core.api.syntax import TaskAliasDeclaration
from rkd.core.api.syntax import GroupDeclaration
from rkd.core.api.testing import BasicTestingCase
from rkd.core.test import TaskForTesting

TESTS_DIR = os.path.dirname(os.path.realpath(__file__))


class ContextTest(BasicTestingCase):
    def test_loads_internal_context(self) -> None:
        """Test if internal context (RKD by default has internal context) is loaded properly
        """
        discovery = ContextFactory(NullSystemIO())
        ctx = discovery._load_context_from_directory(TESTS_DIR + '/../rkd/core/misc/internal')

        self.assertEqual(1, len(ctx))
        self.assertTrue(isinstance(ctx[0], ApplicationContext))

    def test_loads_internal_context_in_unified_context(self) -> None:
        """Check if application loads context including paths from RKD_PATH
        """

        os.environ['RKD_PATH'] = TESTS_DIR + '/../../../docs/examples/makefile-like/.rkd'
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
            path=TESTS_DIR + '/../../../docs/examples/yaml-only/.rkd',
            task=':hello',
            filename='makefile.yaml'
        )

    def test_loads_when_only_py_file_is_in_directory(self):
        """Check if tasks will be loaded when in .rkd there is only a YAML file
        """

        self._common_test_loads_task_from_file(
            path=TESTS_DIR + '/../../../docs/examples/python-only/.rkd',
            task=':hello-python',
            filename='makefile.py'
        )

    def test_context_remembers_directories_from_which_it_was_loaded(self):
        """Verify that whenever we merge contexts, the 'directories' attribute is also merged"""

        ctx1 = ApplicationContext([], [], '/home/iwa-ait',
                                  subprojects=[],
                                  workdir='',
                                  project_prefix='')
        ctx2 = ApplicationContext([], [], '/home/black-lives-matters',
                                  subprojects=[],
                                  workdir='',
                                  project_prefix='')

        ctx_merged = ApplicationContext.merge(ctx1, ctx2)

        self.assertEqual(['/home/iwa-ait'], ctx1.directories)
        self.assertEqual(['/home/iwa-ait', '/home/black-lives-matters'], ctx_merged.directories)

    def test_context_empty_path_is_not_applied_to_directories(self):
        """Test that '' path will not be added to directories list"""

        ctx = ApplicationContext([], [], '', workdir='', project_prefix='', subprojects=[])

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

            with unittest.mock.patch('rkd.core.context.os.path.isfile', return_value=True):
                with unittest.mock.patch('rkd.core.context.SourceFileLoader.load_module') as src_loader_method:
                    class TestImported:
                        IMPORTS = []
                        TASKS = []

                    src_loader_method.return_value = TestImported()
                    src_loader_method.return_value.IMPORTS = [TaskAliasDeclaration(':hello', [':test'])]
                    src_loader_method.return_value.TASKS = []

                    ctx_factory = ContextFactory(NullSystemIO())
                    ctx = ctx_factory._load_from_py(tmp_file.name, prefix='', workdir='')

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

            with unittest.mock.patch('rkd.core.yaml_context.StaticFileSyntaxInterpreter.parse') as parse_method:

                parse_method.return_value = StaticFileContextParsingResult(
                    imports=[TaskAliasDeclaration(':hello', [':test'])],
                    parsed=[],
                    subprojects=[],
                    global_environment={}
                )

                ctx_factory = ContextFactory(NullSystemIO())
                ctx = ctx_factory._load_from_static_file(os.path.dirname(tmp_file.name), os.path.basename(tmp_file.name),
                                                         workdir='', prefix='')

                self.assertIn(':hello', ctx._task_aliases)

    def test_distinct_imports_raises_exception_when_unknown_type_object_added_to_list(self):
        # noinspection PyTypeChecker
        self.assertRaises(ContextException,
                          lambda: distinct_imports('hello', ['string-should-not-be-there-even-IDE-knows-that']))

    def test_distinct_imports_does_not_raise_any_exception_when_no_data(self):
        self.assertEqual(([], []), distinct_imports('hello', []))

    def test_distinct_imports_separtes_lists(self):
        """A successful case for distinct_imports()"""

        imports, aliases = distinct_imports('hello', [
            TaskDeclaration(TaskForTesting()),
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
            TaskDeclaration(TaskForTesting(), name=':test')
        ], [
            Pipeline(':deeper', [':test', ':test']),
            Pipeline(':deep', [':test', ':deeper'])
        ], directory='',
            subprojects=[],
            workdir='',
            project_prefix='')

        ctx.io = IO()
        ctx.compile()
        task = ctx.find_task_by_name(':deep')
        task: GroupDeclaration

        # :deeper = :init
        # :deep = :init :deeper = :init :init :init
        self.assertEqual(':test', task.get_declarations()[0].repr_as_invoked_task)
        self.assertEqual(':test', task.get_declarations()[1].repr_as_invoked_task)
        self.assertEqual(':test', task.get_declarations()[2].repr_as_invoked_task)

    def test_expand_contexts_expands_one_context(self) -> None:
        # MAIN PROJECT context
        ctx = ApplicationContext(
            tasks=[
                TaskDeclaration(TaskForTesting())
            ],
            aliases=[
                TaskAliasDeclaration(':kropotkin', [':init', ':init']),
            ],
            directory='',
            subprojects=['testsubproject1'],
            workdir=f'{TESTS_DIR}/internal-samples/subprojects',
            project_prefix=''
        )

        # SUBPROJECT context
        subproject_1_ctx = ApplicationContext(
            tasks=[
                TaskDeclaration(TaskForTesting())
            ],
            aliases=[
                TaskAliasDeclaration(':book', [':init', ':init']),
            ],
            directory='',
            subprojects=[],  # no deeper subprojects, we do not test deeper as we mock recursion
            workdir='testsubproject1',
            project_prefix=':testsubproject1'
        )

        with mock.patch('rkd.core.context.ContextFactory._load_context_from_directory') as _load_context_from_directory:
            factory = ContextFactory(io=SystemIO())
            _load_context_from_directory.return_value = [subproject_1_ctx]

            # ACTION
            factory._expand_contexts(ctx)

            # assertions
            args, kwargs = _load_context_from_directory.call_args_list[0]

            self.assertIn('tests/internal-samples/subprojects/testsubproject1/.rkd', kwargs['path'])
            self.assertIn('internal-samples/subprojects/testsubproject1', kwargs['workdir'])
            self.assertEqual(':testsubproject1', kwargs['subproject'])

    def test_expand_contexts_ignores_subprojects_if_no_any(self):
        ctx = ApplicationContext(
            tasks=[
                TaskDeclaration(TaskForTesting())
            ],
            aliases=[
                TaskAliasDeclaration(':malatesta', [':init', ':init']),
            ],
            directory='',
            subprojects=[],  # there are no any subprojects
            workdir=f'{TESTS_DIR}/internal-samples/subprojects',
            project_prefix=''
        )
        factory = ContextFactory(io=SystemIO())

        self.assertEqual([ctx], factory._expand_contexts(ctx))
