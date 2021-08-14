.. _Extending tasks:
Extending tasks
===============

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
