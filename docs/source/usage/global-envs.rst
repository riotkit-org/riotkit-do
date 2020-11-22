.. _global environment variables:

Global environment variables
============================

Global switches designed to customize RKD per project. Put environment variables into your **.env** file, so you will no have
to prepend them in the commandline every time.

Read also about :ref:`environment loading priority`

RKD_WHITELIST_GROUPS
~~~~~~~~~~~~~~~~~~~~

Allows to show only selected groups in the ":tasks" list. All tasks from hidden groups are still callable.

**Examples:**

.. code:: bash

    RKD_WHITELIST_GROUPS=:rkd, rkd :tasks
    RKD_WHITELIST_GROUPS=:rkd rkd :tasks

RKD_ALIAS_GROUPS
~~~~~~~~~~~~~~~~

Alias group names, so it can be shorter, or even group names could be not typed at all.

*Notice: :tasks will rename a group with a first defined alias for this group*

**Examples:**

.. code:: bash

    RKD_ALIAS_GROUPS=":rkd->:r" rkd :tasks :r:create-structure
    RKD_ALIAS_GROUPS=":rkd->" rkd :tasks :create-structure


RKD_UI
~~~~~~

Allows to toggle (true/false) the UI - messages like "Executing task X" or "Task finished", leaving only tasks stdout, stderr and logs.


RKD_AUDIT_SESSION_LOG
~~~~~~~~~~~~~~~~~~~~~

Logs output of each executed task, when set to "true".

**Example structure of logs:**

.. code:: bash

    # Note: This example requires "rkd-harbor" package to be installed from PyPI
    RKD_AUDIT_SESSION_LOG=true harbor :service:list   # RiotKit Harbor is another project based on RKD

    # ls .rkd/logs/2020-06-11/11\:06\:02.068556/
    task-1-init.log  task-2-harbor_service_list.log


RKD_BIN
~~~~~~~

Defines a command that invokes RKD eg. :code:`rkd`. When a custom distribution is present, then this value can different.
For example project RiotKit Harbor has it's own command :code:`harbor`, which is based on RKD, so the RKD_BIN=harbor would be defined
in such project.

RKD_BIN is automatically generated, when executing task in a separate process, but it can be also set globally.


RKD_SYS_LOG_LEVEL
~~~~~~~~~~~~~~~~~

Use for debugging. The variable is read in very early stage of RKD initialization, before :code:`:init` task, and before context preparation.

.. code:: bash

    RKD_SYS_LOG_LEVEL=debug rkd :tasks


.. _RKD_IMPORTS:

RKD_IMPORTS
~~~~~~~~~~~

Allows to import a task, or group of tasks (module) inline, without need to create a Makefile.
Useful in daily tasks to create handy shortcuts, also very useful for testing tasks and embedding them inside other applications.

"**:**" character is a separator for multiple imports.


.. code:: bash

    # note: Those examples requires "rkt_utils" package from PyPI
    RKD_IMPORTS="rkt_utils.docker" rkd :docker:tag
    RKD_IMPORTS="rkt_utils.docker:rkt_ciutils.boatci:rkd_python" rkd :tasks

