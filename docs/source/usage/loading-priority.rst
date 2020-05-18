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

Tasks execution
---------------

Tasks are executed one-by-one as they are specified in commandline or in TaskAlias declaration (commandline arguments).

.. code:: bash

    rkd :task-1 :task-2 :task-3

1. task-1
2. task-2
3. task-3

A --keep-going can be specified after given task eg. :task-2 --keep-going, to ignore a single task failure and in consequence allow to go to the next task regardless of result.
