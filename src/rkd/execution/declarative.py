
"""
Declarative allows to collect a list of steps with BASH and/or Python code, then later execute it

Especially helpful, when parsing what is to execute - used in MAKEFILE YAML syntax

"""

import os
import ast
from collections import OrderedDict
from collections import namedtuple
from copy import deepcopy
from traceback import format_exc
from typing import List
from ..api.contract import TaskInterface
from ..api.contract import ExecutionContext


Step = namedtuple('Step', ['language', 'code', 'task_name', 'rkd_path', 'envs', 'task_num'])


class DeclarativeExecutor(object):
    """Executes declared Bash and/or Python code in form of steps

    Avoids using lambdas and inner-methods, so the code is simple, 100% statically typed and serializable
    """

    steps: List[Step]

    def __init__(self):
        self.steps = []

    def add_step(self, language: str, code: str, task_name: str, rkd_path: str, envs: dict):
        self.steps.append(Step(
            language=language,
            code=code, task_name=task_name,
            rkd_path=rkd_path,
            envs=envs,
            task_num=len(self.steps) + 1
        ))

    def execute_steps_one_by_one(self, ctx: ExecutionContext, this: TaskInterface) -> bool:
        """Proxy that executes all steps one-by-one as part of TaskInterface.execute()"""

        this.io().debug('Executing declared steps one-by-one')

        for step in self.steps:
            step: Step

            if step.language == 'python':
                execute = self.execute_python_step
            elif step.language == 'bash':
                execute = self.execute_bash_step
            else:
                raise Exception('Invalid language type')

            this.io().debug('Executing step %i' % step.task_num)
            result = execute(ctx, this, step)

            # if one of step failed, then interrupt and mark task as failure
            if not result:
                this.io().debug('Step failed, interrupting task execution')
                return False

        return True

    @staticmethod
    def execute_python_step(ctx: ExecutionContext, this: TaskInterface, step: Step) -> bool:
        """Executes a Python code through eval()

        The "ctx" and "this" variables are available internally as a context for executed code
        """

        env_backup = deepcopy(os.environ)

        # "ctx" and "this" will be available as a local context
        try:
            # prepare environment
            os.environ.update(step.envs)
            os.environ['RKD_PATH'] = step.rkd_path
            this.push_env_variables(os.environ)
            filename = step.task_name + '@step ' + str(step.task_num)

            # compile code
            this.io().debug('Compiling code')
            tree = ast.parse(step.code)

            if not isinstance(tree.body[-1], ast.Return):
                this.io().debug('Python code at step %s@%i does not have return' % (step.task_name, step.task_num))
                tree = ast.parse(step.code + "\nreturn False")

            eval_expr = ast.Expression(tree.body[-1].value)
            exec_expr = ast.Module(tree.body[:-1], type_ignores=[])

            # run compiled code
            exec(compile(exec_expr, filename, 'exec'))

            to_return = eval(compile(eval_expr, filename, 'eval'))

        except Exception as e:
            this.io().error_msg('Error while executing step %i in task "%s". Exception: %s' % (
                step.task_num, step.task_name, str(e)
            ))
            this.io().error_msg(format_exc())

            to_return = False

        finally:
            os.environ = env_backup

        return to_return

    @staticmethod
    def execute_bash_step(ctx: ExecutionContext, this: TaskInterface, step: Step) -> bool:
        try:
            # assign arguments from ArgumentParser (argparse) to env variables
            args = OrderedDict()
            for name, value in ctx.args.items():
                args['ARG_' + name.upper()] = value

            # glue all environment variables
            process_env = OrderedDict()
            process_env.update(step.envs)
            process_env.update(args)
            process_env.update({'RKD_PATH': step.rkd_path, 'RKD_DEPTH': int(os.getenv('RKD_DEPTH', 0))})

            this.sh(step.code, strict=True, env=process_env)
            return True

        except Exception as e:
            this.io().error_msg('Error while executing step %i in task "%s". Exception: %s' % (
                step.task_num, step.task_name, str(e)
            ))
            return False
