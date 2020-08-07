
Basics
======

RKD command-line usage is highly inspired by GNU Make and Gradle, but it has its own extended possibilities to
make your scripts smaller and more readable.

- Tasks are prefixed always with ":".
- Each task can handle it's own arguments (unique in RKD)
- "@" allows to propagate arguments to next tasks (unique in RKD)

Tasks arguments usage in shell and in scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Executing multiple tasks in one command:**

.. code:: bash

    rkd :task1 :task2


**Multiple tasks with different switches:**

.. code:: bash

    rkd :task1 --hello  :task2 --world


**Tasks sharing the same switches**

Both tasks will receive switch "--hello"

.. code:: bash

    # expands to:
    #  :task1 --hello
    #  :task2 --hello
    rkd @ --hello :task1 :task2

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
    rkd @ --hello :task1 :task2 @ :task3 @ --world :task4 :task5


**Written as a pipeline (regular bash syntax)**

It's exactly the same example as above, but written multiline. It's recommended to write multiline commands if they are longer.

.. code:: bash

    rkd @ --hello \
        :task1 \
        :task2 \
        @
        :task3 \
        @ --world \
        :task4 \
        :task5


YAML syntax - makefile.yaml
~~~~~~~~~~~~~~~~~~~~~~~~~~~

YAML syntax has an advantage of simplicity and clean syntax, custom bash tasks can be defined there easier than in Python.
To use YAML you need to define **makefile.yaml** file in .rkd directory.

:ref:`READ MORE ABOUT YAML SYNTAX IN THE BEGINNERS GUIDE`

**NOTICE: makefile.py and makefile.yaml can exist together. Python version will be loaded first, the YAML version will append changes in priority.**

.. literalinclude:: ../examples/yaml/.rkd/makefile.yaml


What's loaded first? See :ref:`Path and inheritance`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
