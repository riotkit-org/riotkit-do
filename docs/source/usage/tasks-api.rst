.. _Tasks API:

Tasks API
=========

Each task must implement a TaskInterface
----------------------------------------

.. autoclass:: rkd.contract.TaskInterface
   :members:

To include a task, wrap it in a declaration
-------------------------------------------

.. autoclass:: rkd.syntax.TaskDeclaration

To create an alias for task or multiple tasks
---------------------------------------------

.. autoclass:: rkd.syntax.TaskAliasDeclaration

Execution context provides parsed shell arguments and environment variables
---------------------------------------------------------------------------

.. autoclass:: rkd.contract.ExecutionContext
   :members:

Interaction with input and output
---------------------------------
.. autoclass:: rkd.inputoutput.IO
   :members:

Storing temporary files
-----------------------
.. autoclass:: rkd.temp.TempManager
   :members:
