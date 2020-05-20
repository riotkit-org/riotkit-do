
from typing import Union
from .syntax import TaskDeclaration, GroupDeclaration
from .argparsing import CommandlineParsingHelper
from .exception import NotSupportedEnvVariableError


class TaskDeclarationValidator:

    @staticmethod
    def assert_declaration_is_valid(task: TaskDeclaration, parent: Union[GroupDeclaration, None] = None, args: list = []):
        # check if arguments are satisfied
        CommandlineParsingHelper.parse(task, args)

        # validate environment variables
        allowed_envs = task.get_task_to_execute().get_declared_envs()

        for env_name in task.get_user_overridden_envs():
            if env_name not in allowed_envs:
                raise NotSupportedEnvVariableError('"%s" is not a supported environment variable by "%s" task' % (
                    env_name, task.to_full_name()
                ))
