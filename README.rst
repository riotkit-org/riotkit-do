RKD - RiotKit DO
================

Task executor - balance between Makefile and Gradle [see documentation_]

THIS PROJECT IS A WORK IN PROGRESS.

**Goals:**

- Define tasks as simple as in Makefile
- Reuse code as simple as in Gradle (using extensions that provides tasks. Extensions are installable from PIP)
- Simple configuration in Python
- Write tasks code in Python as simple as possible

Rules
-----

-  No hooks eg. task.executeAfter(otherTask), no complex dependencies
-  No dynamic tasks names eg. by turning on Publish component it should
   not create tasks eg. :publishIWAToDockerRegistry (where IWA is the
   project name)
-  Don't pack too many features into the core, do this in external modules. Keep the RKD core clean!
-  Full static analysis, you can work on makefile.py and on task's code in PyCharm with full code completion!
-  Do early validation. Runtime validation for long running builds is a pain-in-the-ass for the user.

Documentation
-------------

Please read the documentation_ here_.

.. _documentation: https://riotkit-do.readthedocs.io/en/latest/
.. _here: https://riotkit-do.readthedocs.io/en/latest/
