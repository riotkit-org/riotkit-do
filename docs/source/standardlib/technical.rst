Technical/Core
==============

:init
~~~~~

This task runs ALWAYS. :init implements a possibility to inherit global settings to other tasks

:tasks
~~~~~~

Lists all tasks that are loaded by all chained makefile.py configurations.

:version
~~~~~~~~

Shows version of RKD and lists versions of all loaded tasks, even those that are provided not by RiotKit.
The version strings are taken from Python modules as RKD strongly rely on Python Packaging.


CallableTask
~~~~~~~~~~~~

This is actually not a task to use directly, it is a template of a task to implement yourself. It's kind of a shortcut
to create a task by defining a simple method as a callback.

.. literalinclude:: ../../examples/callback/.rkd/makefile.py


:rkd:create-structure
~~~~~~~~~~~~~~~~~~~~~

Creates a template structure used by RKD in current directory.

