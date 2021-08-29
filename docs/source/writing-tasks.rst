Writing reusable tasks
======================

There are different ways to achieve similar goal, to define the Task. In chapter about :ref:`syntax` you can learn differences
between those multiple ways.

Now we will focus on **Classic Python** syntax which allows to define Tasks as classes, those classes can be packaged
into Python packages and reused across projects and event organizations.


Importing packages
------------------

Everytime a new project is created there is no need to duplicate same solutions over and over again.
Even in simplest makefiles there are ready-to-use tasks from :code:`rkd.core.standardlib` imported and used.

.. code:: yaml

    version: org.riotkit.rkd/yaml/v2
    imports:
        - my_org.my_package1


Package index
-------------

A makefile can import a class or whole package. There is no any automatic class discovery, every package exports what was intended to export.

Below is explained how does it work that Makefile can import multiple tasks from :code:`my_org.my_package1` without specifying classes one-by-one.

**Example package structure**

.. code:: bash

    my_package1/
    my_package1/__init__.py
    my_package1/script.py
    my_package1/composer.py


**Example __init__.py inside Python package e.g. my_org.my_package1**

.. code:: python

    from rkd.core.api.syntax import TaskDeclaration
    from .composer import ComposerIntegrationTask                 # (1)
    from .script import PhpScriptTask, imports as script_imports  # (2)


    # (3)
    def imports():
        return [
            TaskDeclaration(ComposerIntegrationTask()) # (5)
        ] + script_imports()  # (4)


- (1): **ComposerIntegrationTask** was imported from **composer.py** file
- (2): **imports as script_imports** other **def imports()** from **script.py** was loaded and used in **(4)**
- (3): **def imports()** defines which tasks will appear automatically in your build, when you import whole module, not a single class
- (5): **TaskDeclaration** can decide about custom task name, custom working directory, if the task is **internal** which means - if should be listed on :tasks


Task construction
-----------------

Basic example of how the Task looks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../src/core/rkd/core/standardlib/env.py
   :start-after: <sphinx:getenv>
   :end-before: # <sphinx:/getenv>

Basic configuration methods to implement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **get_name():** Define a name e.g. :code:`:my-task`
- **get_group_name():** Optionally a group name e.g. :code:`:app1`
- **get_declared_envs():** List of allowed environment variables to be used inside of this Task
- **configure_argparse():** Commandline switches configuration, uses Python's native ArgParse
- **get_configuration_attributes()**: Optionally. If our Task is designed to be used as Base Task of other Task, then there we can limit which methods and class attributes can be called from **configure()** method

.. autoclass:: rkd.core.api.contract.TaskInterface
   :members: get_name, get_group_name, get_declared_envs, configure_argparse, get_configuration_attributes


Basic action methods
~~~~~~~~~~~~~~~~~~~~

- **execute():** Contains the Task logic, there is access to environment variables, commandline switches and class attributes
- **inner_execute():** If you want to create a Base Task, then implement a call to this method inside **execute()**, so the Task that extends your Base Task can inject code inside **execute()** you defined
- **configure():** If our Task extends other Task, then there is a possibility to configure Base Task in this method
- **compile():** Code that will execute on compilation stage. There is an access to **CompilationLifecycleEvent** which allows several operations such as **task expansion** (converting current task into a Pipeline with dynamically created Tasks)

.. autoclass:: rkd.core.api.contract.ExtendableTaskInterface
   :members: execute, configure, compile, inner_execute


Additional methods that can be called inside execute() and inner_execute()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **io():** Provides logging inside **execute()** and **configure()**
- **rkd() and sh():** Executes commands in subshells
- **py():** Executes Python code isolated in a subshell

.. autoclass:: rkd.core.api.contract.ExtendableTaskInterface
   :members: io, rkd, sh, py

