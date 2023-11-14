from textwrap import dedent
from traceback import format_exc
from typing import Dict, Type
from typing import List
from argparse import ArgumentParser
from typing import Callable
from typing import Optional
from copy import deepcopy, copy

from rkd.core.api.parsing import SyntaxParsing
from ..api.contract import TaskInterface, ExtendableTaskInterface, MultiStepLanguageExtensionInterface
from ..api.contract import ExecutionContext
from ..api.contract import ArgparseArgument
from ..api.syntax import TaskDeclaration
from ..execution.lifecycle import CompilationLifecycleEvent
from .shell import ShellCommandTask
from ..taskutil import evaluate_code


class CallableTask(TaskInterface):
    """
    Executes a custom callback - allows to quickly define a short, primitive task
    """

    _callable: Callable[[ExecutionContext, TaskInterface], bool]
    _args_callable: Callable[[ArgumentParser], None]
    _argparse_options: Optional[List[ArgparseArgument]]
    _name: str
    _group: str
    _description: str
    _envs: dict
    _become: str

    def __init__(self, name: str, callback: Callable[[ExecutionContext, TaskInterface], bool],
                 args_callback: Callable[[ArgumentParser], None] = None,
                 description: str = '',
                 group: str = '',
                 become: str = '',
                 argparse_options: List[ArgparseArgument] = None):
        self._name = name
        self._callable = callback
        self._args_callable = args_callback
        self._description = description
        self._group = group
        self._envs = {}
        self._become = become
        self._argparse_options = argparse_options

    def get_name(self) -> str:
        return self._name

    def get_become_as(self) -> str:
        return self._become

    def get_description(self) -> str:
        return self._description

    def get_group_name(self) -> str:
        return self._group

    def configure_argparse(self, parser: ArgumentParser):
        if self._argparse_options:
            for opts in self._argparse_options:
                parser.add_argument(*opts.args, **opts.kwargs)

        if self._args_callable:
            self._args_callable(parser)

    def execute(self, context: ExecutionContext) -> bool:
        return self._callable(context, self)

    def push_env_variables(self, envs: dict):
        self._envs = deepcopy(envs)

    def get_declared_envs(self) -> Dict[str, str]:
        return self._envs


class PythonSyntaxTask(ExtendableTaskInterface, MultiStepLanguageExtensionInterface):
    code: str
    name: Optional[str]
    step_num: int

    def __init__(self):
        self.code = ''
        self.name = None
        self.step_num = 0
        self._envs = {}

    def get_name(self) -> str:
        return self.name

    def get_group_name(self) -> str:
        return ''

    def execute(self, context: ExecutionContext) -> bool:
        full_task_name = self.get_name() + '@step ' + str(self.step_num)

        try:
            # compile code
            to_return = evaluate_code(
                code=self.code,
                io=self.io(),
                full_task_name=full_task_name,
                returns_boolean=True,
                ctx=context,
                self=self
            )

        except Exception as e:
            self.io().error_msg('Error while executing step %i in task "%s". Exception: %s' % (
                self.step_num, full_task_name, str(e)
            ))
            self.io().error_msg(format_exc())

            to_return = False

        return to_return

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def with_predefined_details(self, code: str, name: str, step_num: int) -> 'PythonSyntaxTask':
        clone = copy(self)
        clone.code = dedent(code)
        clone.name = name
        clone.step_num = step_num

        return clone


class MultiStepLanguageAgnosticTask(ExtendableTaskInterface):
    """
    Allows to define multiple shell/other language steps
    In YAML syntax it is a default task type (notice: there is no need to specify extends attribute)

    **Bash example**

    .. code:: yaml

        version: org.riotkit.rkd/yaml/v2
        tasks:
            :example:
                steps: |
                    echo "Hello from the Bash"


    **Python example**

    .. code:: yaml

        version: org.riotkit.rkd/yaml/v2
        tasks:
            :example:
                steps: |
                    #!python
                    print('Hello')


    **Multiple languages and steps example**

    .. code:: yaml

        version: org.riotkit.rkd/yaml/v2
        tasks:
            :example:
                steps:
                    - |
                        #!python
                        print('Hello from Python')
                    - ps aux
                    - echo "Hello from Bash"


    **Non-standard languages support**

    .. code:: yaml

        version: org.riotkit.rkd/yaml/v2
        imports:
            - rkd.php.script.PhpLanguage
        environment:
            PHP: '8.0'
            IMAGE: 'php'
        tasks:
            :example:
                steps:
                    - |
                        #!rkd.php.script.PhpLanguage
                        phpinfo();

                    - |
                        #!rkd.core.standardlib.jinja.Jinja2Language
                        The used shell is {{ SHELL }}
    """

    PREDEFINED_STEP_TYPES = {
        'bash': ShellCommandTask,
        'python': PythonSyntaxTask
    }

    def get_name(self) -> str:
        return ':multistep'

    def get_group_name(self) -> str:
        return ''

    def execute(self, context: ExecutionContext) -> bool:
        pass

    def compile(self, event: CompilationLifecycleEvent) -> None:
        """
        Expand self to a group of tasks - each step will be a separate task

        :param event:
        :return:
        """

        steps = self.get_steps()
        tasks = []
        step_num = 0

        event.io.internal(f'MultiStepLanguageAgnosticTask: {self.get_name()} - expanding {len(steps)} steps into tasks')

        if not steps:
            # todo: Better exception class
            raise Exception(f'No tasks to expand for task {self.get_name()} ({self}), possibly missing steps')

        for step in steps:
            step_num += 1
            step_type_name = self._parse_type(step)

            if step_type_name in self.PREDEFINED_STEP_TYPES.keys():
                step_type = self.PREDEFINED_STEP_TYPES[step_type_name]
            else:
                step_type = self._try_to_import_type(step_type_name)

            tasks.append(
                TaskDeclaration(
                    task=self._create_task(step_type, step, step_num, self.get_group_name() + self.get_name()),
                    workdir=event.get_current_declaration().workdir,
                    internal=event.get_current_declaration().is_internal,
                    env=event.get_current_declaration().get_user_overridden_env()
                )
            )

        event.expand_into_group(
            tasks=tasks,
            pipeline=True,
            source_first=False,
            source_last=False,
            hide_children=True
        )

    def _try_to_import_type(self, type_name: str) -> Type:
        as_type = SyntaxParsing.parse_import_as_type(type_name)

        if as_type:
            return as_type

        raise Exception(f'Language {type_name} not supported in task {self.get_name()}')

    def _create_task(self, step_type: Type, code: str, step_num: int, name_prefix: str) -> ExtendableTaskInterface:
        as_lines = code.split("\n")

        # cut off first line
        if as_lines[0][0:2] == '#!':
            code = "\n".join(as_lines[1:])

        step: ExtendableTaskInterface = step_type().with_predefined_details(
            code=code,
            name=name_prefix + f':step_{step_num}',
            step_num=step_num
        )
        step.get_declared_envs = self.get_declared_envs
        step.get_description = self.get_description

        if "get_full_description" in dir(self):
            step.get_full_description = self.__getattribute__('get_full_description')

        return step

    @staticmethod
    def _parse_type(code: str) -> str:
        # code that begin with a hashbang will have hashbang cut off
        # #!bash
        # #!python
        # #!rkd.php.script.PhpScriptTask
        as_lines = code.lstrip().split("\n")
        first_line = as_lines[0]

        if first_line[0:2] == '#!':
            return first_line[2:]

        return "bash"

    def get_steps(self) -> List[str]:
        return []

    def configure_argparse(self, parser: ArgumentParser):
        """
        To be extended
        :param parser:
        :return:
        """
        pass
