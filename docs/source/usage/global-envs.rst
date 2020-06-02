.. _global environment variables:

Global environment variables
============================

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
