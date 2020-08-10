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

    # ls .rkd/logs/2020-06-11/11\:06\:02.068556/
    task-1-init.log  task-2-harbor_service_list.log


RKD_BIN
~~~~~~~

Defines a command that invokes RKD eg. :code:`rkd`. When a custom distribution is present, then this value can different.
For example project RiotKit Harbor has it's own command :code:`harbor`, which is based on RKD, so the RKD_BIN=harbor would be defined
in such project.

RKD_BIN is automatically generated, when executing task in a separate process, but it can be also set globally.
