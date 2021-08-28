.. _Extending tasks:
Extending tasks
===============

Introduction
------------

RKD is designed to provide ready-to-configure automations. In practice you can install almost ready set of tasks using Python's PIP tool, then adjust those tasks to your needs.

Every Base Task implements some mechanism, in this chapter we will use Docker Container as an example.

::

    Given you have a Base Task RunInContainerBaseTask, it lets you do something, while a container is running.
    You can execute commands in container, copy files between host and the container.

    According to the RunInContainerBaseTask's documentation you need to extend the it.
    Which means to make your own task that extends RunInContainerBaseTask as a base,
    then override a method, put your code.

    Voilà! Your own task basing on RunInContainerBaseTask is now ready to be executed!


Practical tips
--------------

In order to successfully extend a Base Task a few steps needs to be marked.
Check Base Task documentation, especially for:

    - The list of methods that are recommended to be extended
    - Which methods could be used in :code:`configure()` and which in :code:`execute()`
    - Does the Base Task implement :code:`inner_execute()`
    - Note which methods to override needs to keep parent call, and if the parent should be called before or after the child (method that overrides parent)


.. CAUTION::
   inner_execute() will not work if it was not implemented by parent task. The sense of existence of inner_execute() is that it should be executed inside execute() at best moment of Base Task.

.. HINT::
   To avoid compatibility issues when upgrading Base Task version use only documented methods

Decorators
----------

There are three decorators that allows to decide if the parent method will be executed:

- @after_parent (from rkd.core.api.decorators): Execute our method after original method
- @before_parent (from rkd.core.api.decorators): Execute our method before original method
- @without_parent (from rkd.core.api.decorators): Do not execute parent method at all


.. IMPORTANT::
   No decorator in most case means that the parent method will not be executed at all

.. CAUTION::
   Not all methods supports decorators. For example argument parsing always inherits argument parsing from parent.
   Decorators can be used for configure, compile, execute, inner_execute.

.. WARNING::
   Using multiple decorators for single method is not allowed and leads to syntax validation error.


.. tabs::

   .. tab:: YAML

      .. code:: yaml

          execute@after_parent: |
              print('I will e executed after parent method will be')

   .. tab:: Simplified Python

      .. code:: python

          @before_parent
          def execute(task: PythonSyntaxTask, ctx: ExecutionContext):
              print('I will e executed before parent method will be')

   .. tab:: Classic Python

      .. code:: python

          def execute(self, ctx: ExecutionContext):
              print('BEFORE PARENT')
              super().execute(ctx)  # make a parent method call
              print('AFTER PARENT')

Example #1: Using inner_execute
-------------------------------

Check :ref:`RunInContainerBaseTask` documentation first. It says that execute() should not be overridden, but inner_execute() should be used instead.

.. include:: ../../src/core/rkd/core/standardlib/docker.py
   :start-after: <sphinx:extending-tasks>
   :end-before: # </sphinx:extending-tasks>


Example #2: Advanced - extending a task that extends other task
---------------------------------------------------------------

In Example #1 there is a *base task that runs something inside a docker container*, going further in Example #2 there is a task that runs any code in a PHP container.

**Architecture:**

- Our example creates a Task from :ref:`PhpScriptTask` (we extend it, and create a "runnable" Task from it)
- :code:`rkd.php.script.PhpScriptTask` extends :code:`rkd.core.standardlib.docker.RunInContainerBaseTask`

Again, to properly prepare your task basing on existing Base Task check the Base Task documentation for tips.
In case of :ref:`PhpScriptTask` the documentation says the parent :code:`inner_execute` method should be executed to still allow providing PHP code via stdin.
To coexist parent and new method in place of :code:`inner_execute` just use one of decorators to control the inheritance behavior.

**Complete example:**

.. include:: ../../src/php/rkd/php/script.py
   :start-after: <sphinx:extending-tasks>
   :end-before: # </sphinx:extending-tasks>


.. include:: syntax-reference.rst
