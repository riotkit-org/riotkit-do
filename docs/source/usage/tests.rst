Testing with unittest
=====================

:code:`rkd.api.testing` provides methods for running tasks with output capturing, a well as mocking RKD classes for unit testing of your task methods.
To use our API just extend one of base classes.

Example: Running a task on a fully featured RKD executor
--------------------------------------------------------

.. code:: python

    #!/usr/bin/env python3

    import os
    from rkd.api.testing import FunctionalTestingCase

    SCRIPT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))


    class TestFunctional(FunctionalTestingCase):
        """
        Functional tests case of the whole application.
        Runs application like from the shell, captures output and performs assertions on the results.
        """

        def test_tasks_listing(self):
            """ :tasks """

            full_output, exit_code = self.run_and_capture_output([':tasks'])

            self.assertIn(' >> Executing :tasks', full_output)
            self.assertIn('[global]', full_output)
            self.assertIn(':version', full_output)
            self.assertIn('succeed.', full_output)
            self.assertEqual(0, exit_code)


Example: Mocking RKD-specific dependencies in TaskInterface
-----------------------------------------------------------

.. code:: python

    from rkd.api.inputoutput import BufferedSystemIO
    from rkd.api.testing import FunctionalTestingCase

    # ...

    class SomeTestCase(FunctionalTestingCase):

        # ...

        def test_something_important(self):
            task = LineInFileTask()  # put your task class there
            io = BufferedSystemIO()

            BasicTestingCase.satisfy_task_dependencies(task, io=io)

            self.assertEqual('something', task.some_method())

Documentation
-------------

.. autoclass:: rkd.api.testing.BasicTestingCase
   :members:

.. autoclass:: rkd.api.testing.FunctionalTestingCase
   :members:

.. autoclass:: rkd.api.testing.OutputCapturingSafeTestCase
   :members:
