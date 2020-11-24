.. _Tasks development:

Tasks development
=================

RKD has multiple approaches to define a task. The first one is simpler - in makefile in YAML or in Python.
The second one is a set of tasks as a Python package.

Option 1) Simplest - in YAML syntax
-----------------------------------

Definitely the simplest way to define a task is to use YAML syntax, it is recommended for beginning users.

**Example 1:**

.. literalinclude:: ../../examples/yaml/.rkd/makefile.yaml


**Example 2:**

.. literalinclude:: ../../examples/env-in-yaml/.rkd/makefile.yml

**Explanation of examples:**

1. "arguments" is an optional dict of arguments, key is the argument name, subkeys are passed directly to argparse
2. "steps" is a mandatory list or text with step definition in Bash or Python language
3. "description" is an optional text field that puts a description visible in ":tasks" task
4. "environment" is a dict of environment variables that can be defined
5. "env_files" is a list of paths to .env files that should be included
6. "imports" imports a Python package that contains tasks to be used in the makefile and in shell usage

Option 2) For Python developers - task as a class
-------------------------------------------------

This way allows to create tasks in a structure of a Python module. Such task can be packaged, then published to eg. PyPI (or other private repository) and used in multiple projects.

Each task should implement methods of **rkd.api.contract.TaskInterface** interface, that's the basic rule.

Following example task could be imported with path **rkd.standardlib.ShellCommandTask**, in your own task you would have a different package name instead of **rkd.standardlib**.

**Example task from RKD standardlib:**

.. literalinclude:: ../../../rkd/standardlib/shell.py
   :start-after: <sphinx=shell-command>
   :end-before: </sphinx=shell-command>


**Explanation of example:**

1. The docstring in Python class is what will be shown in **:tasks as description**. You can also define your description by implementing **def get_description() -> str**
2. Name and group name defines a full name eg. :your-project:build
3. **def configure_argparse()** allows to inject arguments, and --help description for a task - it's a standard Python's argparse object to use
4. **def execute()** provides a context of execution, please read :ref:`Tasks API` chapter about it. In short words you can get commandline arguments, environment variables there.
5. **self.io()** is providing input-output interaction, please use it instead of print, please read :ref:`Tasks API` chapter about it.

Option 3) Quick and elastic way in Python code of Makefile.py
-------------------------------------------------------------

Multiple Makefile files can be used at one time, you don't have to choose between YAML and Python.
This opens a possibility to define more advanced tasks in pure Python, while you have most of the tasks in YAML.
It's elastic - use YAML, or Python or both.

Let's define then a task in Python in a simplest method.

**Makefile.py**

.. code:: python

    import os
    from rkd.api.syntax import TaskDeclaration
    from rkd.api.contract import ExecutionContext
    from rkd.standardlib import CallableTask

    def union_method(context: ExecutionContext) -> bool:
        os.system('xdg-open https://iwa-ait.org')
        return True

    IMPORTS = [
        # just declare a task with a name + code as function! Yay, simple!
        TaskDeclaration(CallableTask(':create-union', union_method))
    ]

    TASKS = []

:ref:`Read more about Python Makefile syntax`.

Please check :ref:`Tasks API` for interfaces description
--------------------------------------------------------
