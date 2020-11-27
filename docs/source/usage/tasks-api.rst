.. _Tasks API:

Tasks API
=========

Each task must implement a TaskInterface
----------------------------------------

.. autoclass:: rkd.api.contract.TaskInterface
   :members:

To include a task, wrap it in a declaration
-------------------------------------------

.. autoclass:: rkd.api.syntax.TaskDeclaration

To create an alias for task or multiple tasks
---------------------------------------------

.. autoclass:: rkd.api.syntax.TaskAliasDeclaration

Execution context provides parsed shell arguments and environment variables
---------------------------------------------------------------------------

.. autoclass:: rkd.api.contract.ExecutionContext
   :members:

Interaction with input and output
---------------------------------
.. autoclass:: rkd.api.inputoutput.IO
   :members:

Storing temporary files
-----------------------
.. autoclass:: rkd.api.temp.TempManager
   :members:

Parsing RKD syntax
------------------
.. autoclass:: rkd.api.parsing.SyntaxParsing
   :members:

Testing
-------

.. autoclass:: rkd.api.testing.BasicTestingCase
   :members:

.. autoclass:: rkd.api.testing.FunctionalTestingCase
   :members:

.. autoclass:: rkd.api.testing.OutputCapturingSafeTestCase
   :members:
