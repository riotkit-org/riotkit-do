Loading priority
================

Environment variables loading order in YAML syntax
--------------------------------------------------

*Legend: Top - is most important*

1. Operating system environment
2. Per-task "environment" section
3. Per-task "env_file" imports
4. Global "environment" section
5. Global "env_file" imports

Order of loading of makefile files in same .rkd directory
---------------------------------------------------------

*Legend: Lower has higher priority (next is appending changes to previous)*

1. *.py
2. *.yaml
3. *.yml

.. _Path and inheritance:

Paths and inheritance
---------------------

RKD by default search for .rkd directory in current execution directory - `./.rkd`.


**The search order is following (from lower to higher load priority):**

1. RKD's internals (we provide a standard tasks like `:tasks`, `:init`, `:sh`, `:exec` and more)
2. `/usr/lib/rkd`
3. User's home `~/.rkd`
4. Current directory `./.rkd`
5. `RKD_PATH`

**Custom path defined via environment variable**

RKD_PATH allows to define multiple paths that would be considered in priority.

.. code:: bash

    export RKD_PATH="/some/path:/some/other/path:/home/user/riotkit/.rkd-second"


**How the makefiles are loaded?**

Each makefile is loaded in order, next makefile can override tasks of previous.
That's why we at first load internals, then your tasks.


Tasks execution
---------------

Tasks are executed one-by-one as they are specified in commandline or in TaskAlias declaration (commandline arguments).

.. code:: bash

    rkd :task-1 :task-2 :task-3

1. task-1
2. task-2
3. task-3

A --keep-going can be specified after given task eg. :task-2 --keep-going, to ignore a single task failure and in consequence allow to go to the next task regardless of result.
