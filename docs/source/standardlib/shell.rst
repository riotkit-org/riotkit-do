Shell
=====

:sh
~~~

Executes a Bash script. Can be multi-line.

**Example of plain usage:**

.. code:: bash

    rkd :sh -c "ps aux"
    rkd :sh --background -c "some-heavy-task"


**Example of task alias usage:**

.. literalinclude:: ../../examples/makefile-like/.rkd/makefile.py


:exec
~~~~~

Works identically as **:sh**, but for spawns a single process. Does not allow a multi-line script syntax.