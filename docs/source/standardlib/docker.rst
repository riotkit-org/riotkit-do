Docker
======

.. _RunInContainerBaseTask:
RunInContainerBaseTask
~~~~~~~~~~~~~~~~~~~~~~~~

- inner_execute() should be used to execute a code while the container is running
- execute() should not be overridden

.. jinja:: RunInContainerBaseTask
   :file: source/templates/package-usage.rst

.. CAUTION::
    This is a Base Task. It is not a Task to run, but to create a **own, runnable Task** basing on it.

.. HINT::
    This is an extendable task. Read more in :ref:`Extending tasks` chapter.


.. autoclass:: rkd.core.standardlib.docker.RunInContainerBaseTask
   :exclude-members: get_name, get_group_name
   :members:
