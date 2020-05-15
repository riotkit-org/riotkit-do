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

- Use fixed versions eg. 3.0 or even 3.0.0 and upgrade only intentionally to reduce your work on fixing bugs


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

    from rkd.syntax import TaskDeclaration
    from rkt_armutils.docker import InjectQEMUBinaryIntoContainerTask

    # ... (use "+" operator to append, remove "+" if you didn't define any import yet)
    IMPORTS += [TaskDeclaration(InjectQEMUBinaryIntoContainerTask)]
