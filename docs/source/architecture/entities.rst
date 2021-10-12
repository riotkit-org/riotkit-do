Lifecycle entities
==================

Internally RKD has three types of objects that are used across the application - Task creation, Task usage declaration, Task execution scheduling.

1) Task Creation
----------------

:code:`TaskInterface` implementations are considered to provide **importable Tasks** to be used in any automation project.

Example: I have :code:`PostgreSQLRunTask` and I import it as :code:`:pgsql:start`


.. code:: python

    # ...

    class RenderDirectoryTask(TaskInterface):
        """Renders *.j2 files recursively in a directory to other directory"""

        def get_name(self) -> str:
            return ':directory-to-directory'

        def get_group_name(self) -> str:
            return ':j2'

        def execute(self, context: ExecutionContext) -> bool:
            # ...


Tasks should be defined mainly as part of installable libraries via PyPI, but could be also defined in local repository.


2) Task usage declaration - importing & preconfiguring Tasks in project code
----------------------------------------------------------------------------

:code:`TaskDeclaration` declares that imported :code:`TaskInterface` implementation would be used in our automation project
under some name, with some environment variables, custom workspace and other little customizations that does not involve changing the code of imported Task.


:code:`Pipeline`, :code:`PipelineTask` and :code:`PipelineBlock` defines complete Pipelines, with error handling, notifications, list of Tasks to execute.

**That's called static declaration of reproducible usage. Tasks are imported into a project defined in code, each Task is preconfigured and ready to be used in reproducible way.**


.. code:: python

    from rkd.core.api.syntax import Pipeline, PipelineTask as Task, PipelineBlock as Block, TaskDeclaration
    from rkd.core.standardlib.core import DummyTask
    from rkd.core.standardlib.shell import ShellCommandTask

    IMPORTS = [
        TaskDeclaration(ShellCommandTask(), internal=True)
    ]

    PIPELINES = [
        Pipeline(
            name=':example',
            to_execute=[
                Block(rescue='...', tasks=[
                    Task('...'),
                ]),
                Task('...'),
            ]
        )
    ]


3) Runtime Task scheduling
--------------------------

Imported Tasks and declared for usage in a project are processed, when executed.
This later stage is invisible to end-user and is performed internally on runtime, the entities are not known to the user.

Internally RKD must wrap any :code:`TaskDeclaration` and process :code:`Pipeline` into lower-level entities on first stage - resolving & compilation stage.

:code:`TaskDeclaration` is wrapped by :code:`DeclarationScheduledToRun` that **mixes** environment, arguments and other options **declared in code with everything that
exists during execution that takes place now.**

:code:`Pipeline` is translated into :code:`GroupDeclaration` and associated :code:`ArgumentBlock` objects which are no longer strings like :code:`:db:start --listen=5432`, but are separate :code:`TaskDeclaration` objects.
There are all :code:`@rescue` and :code:`@error` modifiers resolved into objects, so everything is calculated on very early stage and therefore can be validated without disrupting later execution by any simple errors.

Each :code:`TaskDeclaration` in Pipeline is wrapped into :code:`DeclarationBelongingToPipeline` which acts very similar to :code:`DeclarationScheduledToRun`, but it was named differently
to distinct between something that was declared in the code (:code:`DeclarationBelongingToPipeline`) from something that contains a set of information how the user invoked the command from shell (:code:`DeclarationScheduledToRun`)
