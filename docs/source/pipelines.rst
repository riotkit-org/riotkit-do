Pipelines
=========

    Pipeline is a set of Tasks executing in selected order, with optional addition of error handling.


@error
------

Executes a Task or set of Tasks when error happens. Does not affect the final result. After error task is finished the whole execution is stopped, no any more task will execute.

**Syntax:**

.. tabs::

   .. tab:: YAML

      .. code:: yaml

            version: org.riotkit.rkd/yaml/v2
            pipelines:
                :upgrade:
                    - task: ":db:backup"
                    - task: ":db:stop"
                    - block:
                          error: [':notify', '--msg="Failed"']
                          tasks:
                              - task: [':db:migrate']
                    - task: [":db:start"]
                    - task: [":notify", '--msg', 'Finished']

   .. tab:: Python

      .. code:: python

            from rkd.core.api.syntax import Pipeline, PipelineTask as Task, PipelineBlock as Block, TaskDeclaration
            from rkd.core.standardlib.core import DummyTask
            from rkd.core.standardlib.shell import ShellCommandTask

            # ...

            PIPELINES = [
                Pipeline(
                    name=':upgrade',
                    description='Example',
                    to_execute=[
                        Task(':db:backup'),
                        Task(':db:stop'),
                        Block(error=':notify --msg="Failed"', tasks=[
                            Task(':db:migrate')
                        ]),
                        Task(':db:start'),
                        Task(':notify', '--msg', 'Finished')
                    ]
                )
            ]

**Example workflow:**

.. image:: rkd-pipeline-error.png

