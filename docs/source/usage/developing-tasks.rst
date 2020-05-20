Tasks development
=================

RKD has two approaches to define a task. The first one is simpler - in makefile in YAML or in Python.
The second one is a set of tasks as a Python package.

Developing a Python package
---------------------------

Each task should implement methods of **rkd.contract.TaskInterface** interface, that's the basic rule.

Following example task could be imported with path **rkd.standardlib.ShellCommandTask**, in your own task you would have a different package name instead of **rkd.standardlib**.

**Example task from RKD standardlib:**

.. literalinclude:: ../../../src/rkd/standardlib/shell.py
   :start-after: <sphinx=shell-command>
   :end-before: </sphinx=shell-command>


**Explanation of example:**

1. The docstring in Python class is what will be shown in **:tasks as description**. You can also define your description by implementing **def get_description() -> str**
2. Name and group name defines a full name eg. :your-project:build
3. **def configure_argparse()** allows to inject arguments, and --help description for a task - it's a standard Python's argparse object to use
4. **def execute()** provides a context of execution, please read :ref:`Tasks API` chapter about it. In short words you can get commandline arguments, environment variables there.
5. **self.io()** is providing input-output interaction, please use it instead of print, please read :ref:`Tasks API` chapter about it.

Please check :ref:`Tasks API` for interfaces description
--------------------------------------------------------
