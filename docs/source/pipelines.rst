Pipelines
=========

    Pipeline is a set of Tasks executing in selected order, with optional addition of error handling.
    Modifiers are changing behavior of Task execution, by implementing fallbacks, retries and error notifications.


.. TIP::

    Modifiers can be used together e.g. **@retry** + **@rescue**, **@retry** + **@error**

    Exceptions are: **@retry** + **@retry-block** and **@error** + **@rescue**


Basic pipeline
--------------

Basically the pipeline is a set of Tasks, it does not need to define any error handling.

.. TIP::

    Treat Pipeline as a shell command invocation - in practice a Pipeline is an alias, it is similar to a command executed in command line but a little bit more advanced.

    The comparison isn't abstract, that's how Pipelines works and why there are shell examples of Pipelines.


.. tabs::

   .. tab:: YAML

      .. code:: yaml

            version: org.riotkit.rkd/yaml/v2

            # ...

            pipelines:
                :perform:
                    tasks:
                        - task: :start
                        - task: :do-something
                        - task: :stop

   .. tab:: Python

      .. code:: python

            from rkd.core.api.syntax import Pipeline, PipelineTask as Task, PipelineBlock as Block, TaskDeclaration

            # ...

            PIPELINES = [
                Pipeline(
                    name=':perform',
                    description='Example',
                    to_execute=[
                        Task(':start'),
                        Task(':do-something'),
                        Task(':stop')
                    ]
                )
            ]

   .. tab:: Shell

      .. code:: bash

            # :perform
            ./rkdw :start :do-something :stop


@retry
------

Simplest modifier that retries each failed task in a block up to maximum of N times.

The example actually combines **@retry** + **@rescue**. But **@retry** can be used alone.

**Syntax:**

.. tabs::

   .. tab:: YAML

      .. code:: yaml

            version: org.riotkit.rkd/yaml/v2

            # ...

            pipelines:
                :start:
                    tasks:
                        - block:
                              retry: 1  # retry max. 1 time
                              rescue: [':app:clear-cache', ':app:start']
                              tasks:
                                  - task: [':db:start']
                                  - task: [':app:start']
                        - task: [':logs:collect', '--app', '--db', '--watch']

   .. tab:: Python

      .. code:: python

            from rkd.core.api.syntax import Pipeline, PipelineTask as Task, PipelineBlock as Block, TaskDeclaration

            # ...

            PIPELINES = [
                Pipeline(
                    name=':start',
                    description='Example',
                    to_execute=[
                        Block(rescue=':app:clear-cache :app:start', retry=1, tasks=[
                            Task(':db:start'),
                            Task(':app:start')
                        ]),
                        Task(':logs:collect', '--app', '--db', '--watch')
                    ]
                )
            ]

   .. tab:: Shell

      .. code:: bash

            # :start
            ./rkdw '{@rescue :app:clear-cache :app:start @retry 1}' :db:start :app:start '{/@}' :logs:collect --app --db --watch


**Example workflow:**

.. image:: rkd-pipeline-retry.png


@retry-block
------------

Works in similar way as **@retry**, the difference is that if at least one task fails in a block, then all tasks from that blocks are repeated N times.

**Example workflow:**

.. image:: rkd-pipeline-retry-block.png


@error
------

Executes a Task or set of Tasks when error happens. Does not affect the final result. After error task is finished the whole execution is stopped, no any more task will execute.

**Syntax:**

.. tabs::

   .. tab:: YAML

      .. code:: yaml

            version: org.riotkit.rkd/yaml/v2

            # ...

            pipelines:
                :upgrade:
                    tasks:
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

   .. tab:: Shell

      .. code:: bash

            # :upgrade
            ./rkdw :db:backup :db:stop '{@error :notify --msg="Failed"}' :db:migrate '{/@}' :db:start :notify --msg "Finished"

**Example workflow:**

.. image:: rkd-pipeline-error.png


@rescue
-------

Defines a Task that should be ran, when any of Task from given block will fail.
Works similar as **@error**, but with difference that **@rescue** changes the result of pipeline execution.

.. TIP::

    When **@rescue** succeeds, then we assume that original Task that failed is now ok.


**Example workflow:**

.. image:: rkd-pipeline-rescue.png
