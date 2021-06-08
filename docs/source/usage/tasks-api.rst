.. _Tasks API:

Tasks API
=========

Each task must implement a TaskInterface
----------------------------------------

.. autoclass:: rkd.core.api.contract.TaskInterface
   :members:

To include a task, wrap it in a declaration
-------------------------------------------

.. autoclass:: rkd.core.api.syntax.TaskDeclaration

To create an alias for task or multiple tasks
---------------------------------------------

.. autoclass:: rkd.core.api.syntax.TaskAliasDeclaration

Execution context provides parsed shell arguments and environment variables
---------------------------------------------------------------------------

.. autoclass:: rkd.core.api.contract.ExecutionContext
   :members:

Interaction with input and output
---------------------------------
.. autoclass:: rkd.core.api.inputoutput.IO
   :members:

Storing temporary files
-----------------------
.. autoclass:: rkd.core.api.temp.TempManager
   :members:

Parsing RKD syntax
------------------
.. autoclass:: rkd.core.api.parsing.SyntaxParsing
   :members:

Testing
-------

.. autoclass:: rkd.core.api.testing.BasicTestingCase
   :members:

.. autoclass:: rkd.core.api.testing.FunctionalTestingCase
   :members:

.. autoclass:: rkd.core.api.testing.OutputCapturingSafeTestCase
   :members:
