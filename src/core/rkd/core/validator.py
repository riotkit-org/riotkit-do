
from typing import Union

from .api.inputoutput import IO
from .api.syntax import DeclarationScheduledToRun
from .argparsing.parser import CommandlineParsingHelper
from .exception import NotSupportedEnvVariableError
from .iterator import TaskIterator


class TaskDeclarationValidator(TaskIterator):
    io: IO

    def __init__(self, io: IO):
        self.io = io

    def iterate_blocks(self) -> bool:
        return True

    def process_task(self, scheduled: DeclarationScheduledToRun, task_num: int):
        self.assert_declaration_is_valid(scheduled)

    def assert_declaration_is_valid(self, scheduled: DeclarationScheduledToRun):
        self.io.internal(f'Validating {scheduled.debug()}')

        # check if arguments are satisfied
        CommandlineParsingHelper.parse(scheduled.declaration, scheduled.args)

        # validate environment variables
        allowed_envs = scheduled.declaration.get_task_to_execute().internal_normalized_get_declared_envs()

        for env_name in scheduled.declaration.get_list_of_user_overridden_envs():
            if env_name not in allowed_envs:
                raise NotSupportedEnvVariableError('"%s" is not a supported environment variable by "%s" task' % (
                    env_name, scheduled.declaration.to_full_name()
                ))
