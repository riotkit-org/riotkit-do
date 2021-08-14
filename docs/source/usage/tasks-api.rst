.. _Tasks API:

Tasks API
=========

Each task must implement a TaskInterface (directly, or through a Base Task)
---------------------------------------------------------------------------

.. ATTENTION::
   Methods marked as :code:`abstract` must be implemented by your task that extends directly from TaskInterface.

.. TIP::
   During configuration and execution stage every task is having it's own ExecutionContext instance.
   ExecutionContext (called ctx) gives access to parameters, environment variables, user input (e.g. stdin)
   Do not try to manually read from stdin, or os.environment - read more about this topic in :ref:`Best practices` chapter.


.. autoclass:: rkd.core.api.contract.TaskInterface
   :members:

To include a task, wrap it in a declaration
-------------------------------------------

.. NOTE::
   Task declaration declares a Task (TaskInterface implementation) to be a runnable task imported into a given Makefile.

.. TIP::
   With TaskDeclaration there is a possibility to customize things like task name, environment, working directory and other attributes.


.. autoclass:: rkd.core.api.syntax.TaskDeclaration

To create an alias for task or multiple tasks
---------------------------------------------

.. NOTE::
   TaskAlias is a simplified pipeline form, it is a chain of tasks written in a string form.

.. autoclass:: rkd.core.api.syntax.TaskAliasDeclaration

Execution context provides parsed shell arguments and environment variables
---------------------------------------------------------------------------

.. autoclass:: rkd.core.api.contract.ExecutionContext
   :members:

Interaction with input and output
---------------------------------

.. TIP::
   From inside a Task the IO can be accessed with :code:`self.io()`

.. CAUTION::
   Every task has it's own instance of IO, with customized per-task log level.

.. autoclass:: rkd.core.api.inputoutput.IO
   :members:

Storing temporary files
-----------------------

.. TIP::
   From inside a Task the TempManager can be accessed with :code:`self.temp`

.. autoclass:: rkd.core.api.temp.TempManager
   :members:

Parsing RKD syntax
------------------
.. autoclass:: rkd.core.api.parsing.SyntaxParsing
   :members:

Testing
-------

.. TIP::
   BasicTestingCase is best for unit testing

.. autoclass:: rkd.core.api.testing.BasicTestingCase
   :members:

.. TIP::
   FunctionalTestingCase should be using for tests that are running single task and asserting output contents.

.. autoclass:: rkd.core.api.testing.FunctionalTestingCase
   :members:

.. autoclass:: rkd.core.api.testing.OutputCapturingSafeTestCase
   :members:
