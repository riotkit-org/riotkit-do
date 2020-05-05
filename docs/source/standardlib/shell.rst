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

Class to import: BaseShellCommandWithArgumentParsingTask
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creates a command that executes bash script and provides argument parsing using Python's argparse.
Parsed arguments are registered as ARG_{{argument_name}} eg. --activity-type would be exported as ARG_ACTIVITY_TYPE.

.. code:: python

    IMPORTS += [
        BaseShellCommandWithArgumentParsingTask(
            name=":protest",
            group=":activism",
            description="Take action!",
            arguments_definition=lambda argparse: (
                argparse.add_argument('--activity-type', '-t', help='Select an activity type')
            ),
            command='''
                echo "Let's act! Let's ${ARG_ACTIVITY_TYPE}!"
            '''
        )
    ]


