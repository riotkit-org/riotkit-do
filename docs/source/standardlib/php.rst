PHP
===

.. _PhpScriptTask:
PhpScriptTask
~~~~~~~~~~~~~

- configure: Should be overridden only with @before_parent decorator
- inner_execute: Should be overridden preserving original parent after or before
- input: A string of PHP code, optionally

.. jinja:: PhpScriptTask
   :file: source/templates/package-usage.rst

.. CAUTION::
    This is a Base Task. It is not a Task to run, but to create a **own, runnable Task** basing on it.

.. HINT::
    This is an extendable task. Read more in :ref:`Extending tasks` chapter.


.. autoclass:: rkd.php.script.PhpScriptTask
   :exclude-members: get_name, get_group_name
   :members:


PhpLanguage
~~~~~~~~~~~

.. autoclass:: rkd.php.script.PhpLanguage
