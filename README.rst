RKD - RiotKit DO
================

Task executor - balance between Makefile and Gradle.

THIS PROJECT IS A WORK IN PROGRESS.

**Goals:** - Define tasks as simple as in Makefile - Reuse code as
simple as in Gradle (using extensions that provides tasks. Extensions
are installable from PIP) - Simple configuration in Python

Rules
-----

-  No hooks eg. task.executeAfter(otherTask), no complex dependencies
-  No dynamic tasks names eg. by turning on Publish component it should
   not create tasks eg. :publishIWAToDockerRegistry (where IWA is the
   project name)

Usage in shell
--------------

Tasks are prefixed always with ":". Each task can handle it's own
arguments.

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

