from typing import List, Optional, Union
from .api.syntax import TaskDeclaration, DeclarationScheduledToRun, GroupDeclaration, DeclarationBelongingToPipeline
from .argparsing.model import ArgumentBlock


class ResolvedTaskBag(object):
    """
    Stores resolved TaskDeclaration objects into Declarations that are scheduled to be executed
    """

    __declarations: List[DeclarationScheduledToRun]

    def __init__(self):
        self.__declarations = []

    @property
    def scheduled_declarations_to_run(self) -> List[DeclarationScheduledToRun]:
        return self.__declarations

    def add(self, declaration: Union[TaskDeclaration, DeclarationBelongingToPipeline],
            args: List[str],
            block: ArgumentBlock,
            parent: Optional[GroupDeclaration] = None):

        if isinstance(declaration, DeclarationBelongingToPipeline):
            scheduled_to_run = declaration
            scheduled_to_run.append(
                runtime_arguments=args,
                env={},
                user_overridden_env=[]
            )
            scheduled_to_run.parent = parent
        else:
            scheduled_to_run = DeclarationScheduledToRun(
                declaration=declaration,
                runtime_arguments=args,
                parent=parent
            )

        # relation to blocks - multiple to one
        scheduled_to_run.connect_block(block)

        self.__declarations.append(scheduled_to_run)

        return scheduled_to_run
