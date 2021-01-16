
from typing import Union
from .api.syntax import TaskDeclaration, GroupDeclaration
from .argparsing.parser import CommandlineParsingHelper
from .exception import NotSupportedEnvVariableError


class TaskDeclarationValidator(object):

    @staticmethod
    def assert_declaration_is_valid(task: TaskDeclaration, task_num: int,
                                    parent: Union[GroupDeclaration, None] = None,
                                    args: list = None):

        if args is None:
            args = []

        # @todo: Other exception type
        if task.block().has_action_on_error() and task.block().should_rescue():
            raise Exception('Block "{0:s}" cannot define both @rescue and @error'.format(task.block().body))

        # check if arguments are satisfied
        CommandlineParsingHelper.parse(task, args)

        # validate environment variables
        allowed_envs = task.get_task_to_execute().internal_normalized_get_declared_envs()

        for env_name in task.get_user_overridden_envs():
            if env_name not in allowed_envs:
                raise NotSupportedEnvVariableError('"%s" is not a supported environment variable by "%s" task' % (
                    env_name, task.to_full_name()
                ))
