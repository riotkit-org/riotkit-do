.. _Importing tasks:

Importing tasks
===============

Tasks can be defined as installable Python's packages that you can import in your Makefile

**Please note:**

- To import a group, the package you try to import need to hvve a defined **imports()** method inside of the package.
- The imported group does not need to import automatically dependend tasks (but it can, it is recommended), you need to read into the docs of specific package if it does so

1) Install a package
--------------------

RKD defines dependencies using Python standards.

Example: Given we want to import tasks from package "rkt_armutils".

.. code:: bash

    echo "rkt_armutils==3.0" >> requirements.txt
    pip install -r requirements.txt


**Good practices:**

- Use fixed versions eg. 3.0 or even 3.0.0 and upgrade only intentionally to reduce your work. Automatic updates, especially of major versions
could be unpredictable and possibly can break something time-to-time

**How do I check latest version?:**

- Simply install a package eg. :code:`pip install rkt_armutils`, then do a :code:`pip show rkt_armutils` and write the version
to the requirements.txt, or lookup a package first at https://pypi.org/project/rkt_armutils/ (where rkt_armutils is an example package)


2) In YAML syntax
-----------------

Example: Given we want to import task "InjectQEMUBinaryIntoContainerTask", or we want to import whole "rkt_armutils.docker" group

.. code:: yaml

    imports:
        # Import whole package, if the package defines a group import (method imports())
        - rkt_armutils.docker

        # Or import single task
        - rkt_armutils.docker.InjectQEMUBinaryIntoContainerTask


2) In Python syntax
-------------------

Example: Given we want to import task "InjectQEMUBinaryIntoContainerTask", or we want to import whole "rkt_armutils.docker" group

.. code:: python

    from rkd.api.syntax import TaskDeclaration
    from rkt_armutils.docker import InjectQEMUBinaryIntoContainerTask

    # ... (use "+" operator to append, remove "+" if you didn't define any import yet)
    IMPORTS += [TaskDeclaration(InjectQEMUBinaryIntoContainerTask)]


3) Inline syntax
----------------

Tasks could be imported also in shell, for quick check, handy scripts, or for embedding inside other applications.

.. code:: bash

    # note: Those examples requires "rkt_utils" package from PyPI
    RKD_IMPORTS="rkt_utils.docker" rkd :docker:tag
    RKD_IMPORTS="rkt_utils.docker:rkt_ciutils.boatci:rkd_python" rkd :tasks

    # via commandline switch "--imports"
    rkd --imports "rkt_utils.docker:rkt_ciutils.boatci:rkd_python" :tasks


*Note: The significant difference between environment variable and commandline switch is that the environment variable
will be inherited into subshells of RKD, commandline argument not.*


For more information about this environment variable check it's documentation page: :ref:`RKD_IMPORTS`

Ready to go? Check :ref:`Built-in tasks` that you can import in your Makefile
-----------------------------------------------------------------------------
