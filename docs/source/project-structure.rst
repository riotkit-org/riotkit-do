Project structure
=================

Root level of the project should contain a hidden directory :code:`.rkd`, there could be also defined
subprojects as subdirectories of any depth.

**Example structure**

::

    # project-level RKD files
    .rkd/makefile.yaml
    .rkd/makefile.py
    rkdw

    # some domain-specific files (e.g. web application)
    src/Application/index.php
    composer.json

    # example subproject - documentation
    docs/index.rst
    docs/.rkd/makefile.yaml

    # example second subproject - deployment to production
    infrastructure/main.tf
    infrastructure/variables.tf
    infrastructure/outputs.tf
    infrastructure/.rkd/makefile.py


**Example of usage of above project**

.. code:: bash

    # build project, docs
    ./rkdw :docs:build :build
    ./rkdw :infrastructure:deploy


.. TIP::
    Divide Tasks in subprojects into smaller pieces to create an aggregated flow on project level, or on parent subproject level.

.. TIP::
    Design subprojects to be independent of Tasks in other subprojects to gain an easy way of testing smaller pieces of your automation.


Enabling subprojects
--------------------

Subproject can be enabled only manually, there is no automatic discovery for performance and clarity reasons.
A subproject can be included by it's parent Makefile. There can be an infinite depth of subprojects.

All tasks from subprojects are prefixed with the directory name (a subproject name).


.. tabs::

   .. tab:: makefile.yaml

      .. code:: yaml

        subprojects: ['docs', 'infrastructure']

   .. tab:: makefile.py

      .. code:: python

        SUBPROJECTS = ['docs', 'infrastructure']


.. WARNING::
    Subproject name should not contain "/" or any other special characters

.. WARNING::
    Subprojects are loaded recursively step-by-step. Subproject cannot load sub-sub-subproject, it must go through step-by-step and include its closest children.
