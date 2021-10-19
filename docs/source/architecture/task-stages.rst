Task lifetime stages
====================


1) Construction
---------------

Tasks are created and imported into the :code:`ApplicationContext`. Every :code:`.rkd` directory context is parsed into
:code:`ApplicationContext`, then all contexts are merged into an unified :code:`ApplicationContext`.

2) Compilation
--------------

Unified :code:`ApplicationContext` is compiled, compilation does two things:

1. Resolving all Pipelines into Groups of resolved Tasks
2. Executing :code:`compile()` on all defined Tasks in :code:`ApplicationContext`, regardless if they are called

3) Configuration
----------------

:code:`configure()` method is triggered on each Task that is scheduled to be executed.

4) Execution
------------

:code:`execute()` method is triggered on each Task that is scheduled to be executed.

5) Teardown
-----------

To be done. Not implemented yet.
