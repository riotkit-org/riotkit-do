Technical/Core
==============

:init
~~~~~

.. jinja:: init
   :file: source/templates/package-usage.rst

This task runs ALWAYS. :init implements a possibility to inherit global settings to other tasks

:tasks
~~~~~~

.. jinja:: tasks
   :file: source/templates/package-usage.rst

Lists all tasks that are loaded by all chained makefile.py configurations.

Environment variables:

- RKD_WHITELIST_GROUPS: (Optional) Comma separated list of groups to only show on the list
- RKD_ALIAS_GROUPS: (Optional) Comma separated list of groups aliases eg. ":international-workers-association->:iwa,:anarchist-federation->:fa"

:version
~~~~~~~~

.. jinja:: version
   :file: source/templates/package-usage.rst

Shows version of RKD and lists versions of all loaded tasks, even those that are provided not by RiotKit.
The version strings are taken from Python modules as RKD strongly rely on Python Packaging.


CallableTask
~~~~~~~~~~~~

.. jinja:: callable_task
   :file: source/templates/package-usage.rst

This is actually not a task to use directly, it is a template of a task to implement yourself. It's kind of a shortcut
to create a task by defining a simple method as a callback.

.. literalinclude:: ../../examples/callback/.rkd/makefile.py


:rkd:create-structure
~~~~~~~~~~~~~~~~~~~~~

.. jinja:: rkd_create_structure
   :file: source/templates/package-usage.rst

Creates a template structure used by RKD in current directory.


:file:line-in-file
~~~~~~~~~~~~~~~~~~

.. jinja:: line_in_file
   :file: source/templates/package-usage.rst

Similar to the Ansible's lineinfile, replaces/creates/deletes a line in file.

**Example usage:**

.. code:: bash

    echo "Number: 10" > test.txt

    rkd -rl debug :file:line-in-file test.txt --regexp="Number: ([0-9]+)?(.*)" --insert='Number: $match[0] / new: 10'
    cat test.txt

    rkd -rl debug :file:line-in-file test.txt --regexp="Number: ([0-9]+)?(.*)" --insert='Number: $match[0] / new: 6'
    cat test.txt

    rkd -rl debug :file:line-in-file test.txt --regexp="Number: ([0-9]+)?(.*)" --insert='Number: 50'
    cat test.txt

    rkd -rl debug :file:line-in-file test.txt --regexp="Number: ([0-9]+)?(.*)" --insert='Number: $match[0] / new: 90'
    cat test.txt


