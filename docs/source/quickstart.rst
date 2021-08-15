
.. _Commandline basics:

Commandline basics
==================

RKD command-line usage is highly inspired by GNU Make and Gradle, but it has its own extended possibilities to
make your scripts smaller and more readable.

- Tasks are prefixed always with ":".
- Each task can handle it's own arguments (unique in RKD)
- "@" allows to propagate arguments to next tasks (unique in RKD)

Tasks arguments usage in shell and in scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Executing multiple tasks in one command:**

.. code:: bash

    ./rkdw :task1 :task2


**Multiple tasks with different switches:**

.. code:: bash

    ./rkdw :task1 --hello  :task2 --world --become=root


Second task will run as root user, additionally with :code:`--world` parameter.


**Tasks sharing the same switches**

Both tasks will receive switch "--hello"

.. code:: bash

    # expands to:
    #  :task1 --hello
    #  :task2 --hello
    ./rkdw @ --hello :task1 :task2

    # handy, huh?

**Advanced usage of shared switches**

Operator "@" can set switches anytime, it can also clear or replace switches in **NEXT TASKS**.

.. code:: bash

    # expands to:
    #   :task1 --hello
    #   :task2 --hello
    #   :task3
    #   :task4 --world
    #   :task5 --world
    ./rkdw @ --hello :task1 :task2 @ :task3 @ --world :task4 :task5


**Written as a pipeline (regular bash syntax)**

It's exactly the same example as above, but written multiline. It's recommended to write multiline commands if they are longer.

.. code:: bash

    ./rkdw @ --hello \
        :task1 \
        :task2 \
        @
        :task3 \
        @ --world \
        :task4 \
        :task5


Advanced: Blocks for error handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Blocks allow to retry single failed task, or a group of tasks, execute a failure or rescue task.

.. TIP::
   Blocks cannot be nested.

**Retry a task - @retry**

Retry task until it will return success, up to defined retries.
If there are multiple tasks, then a single task is repeated, not a whole block.

.. code:: bash

    ./rkdw '{@retry 3}' :unstable-task '{/@}'


**Retry a block (set of tasks) - @retry-block**

Works very similar to @retry, but in case, when at least one task fails - all tasks in the block are repeated.


.. code:: bash

    ./rkdw '{@retry-block 3}' :unstable-task :task2 '{/@}'

**Rescue - @rescue**

When a failure happens in any of tasks, then those tasks are interrupted and a rollback task is executed.
Whole block status depends on the rollback task status. After a successful rollback execution next tasks from outside of the blocks are normally executed.

.. code:: bash

    ./rkdw :db:shutdown :db:backup '{@rescue :db:restore}' :db:upgrade '{/@}' :db:start


**Error - @error**

When at least one task fails, then a error task is notified and the execution is stopped.

.. code:: bash

    ./rkdw '{@error :notify "Task failed!"}' :some-task :some-other-task '{/@}'
