
Basics
======

Tasks are prefixed always with ":".
Each task can handle it's own arguments.

Tasks arguments usage
~~~~~~~~~~~~~~~~~~~~~

*makefile.py*

.. code:: python


    from rkd.syntax import TaskDeclaration, TaskAliasDeclaration
    from rkd.standardlib.python import PublishTask

    IMPORTS = [
        TaskDeclaration(PublishTask())
    ]

    TASKS = [
        TaskAliasDeclaration(':my:test', [':py:publish', '--username=...', '--password=...'])
    ]

**Example of calling same task twice, but with different input**

Notes for this example: The "username" parameter is a default defined in
``makefile.py`` in this case.

.. code:: bash

    $ rkd :my:test --password=first :my:test --password=second
     >> Executing :py:publish
    Publishing
    {'username': '...', 'password': 'first'}

     >> Executing :py:publish
    Publishing
    {'username': '...', 'password': 'second'}

**Example of calling same task twice, with no extra arguments**

In this example the argument values "..." are taken from ``makefile.py``

.. code:: bash

    $ rkd :my:test :my:test
     >> Executing :py:publish
    Publishing
    {'username': '...', 'password': '...'}

     >> Executing :py:publish
    Publishing
    {'username': '...', 'password': '...'}

**Example of --help per command:**

.. code:: bash

    $ rkd :my:test :my:test --help
    usage: :py:publish [-h] [--username USERNAME] [--password PASSWORD]

    optional arguments:
      -h, --help           show this help message and exit
      --username USERNAME  Username
      --password PASSWORD  Password

Simplified - YAML syntax
~~~~~~~~~~~~~~~~~~~~~~~~

YAML syntax has an advantage of simplicity and clean syntax, custom bash tasks can be defined there easier than in Python.
To use YAML you need to define **makefile.yaml** file in .rkd directory.

**NOTICE: makefile.py and makefile.yaml can exist together. Python version will be loaded first, the YAML version will append changes in priority.**

.. literalinclude:: ../examples/yaml/.rkd/makefile.yaml


What's loaded first? See :ref:`Path and inheritance`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
