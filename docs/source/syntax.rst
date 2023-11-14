.. _syntax:

Syntax
======

RKD is elastic. Different syntax allows to choose between ease of usage and extended possibilities.


YAML
~~~~

- Best choice to start with RKD, perfect for simpler usage
- Gives clear view on what is defined, has obvious structure
- Created tasks are not possible to be shared as part of Python package


.. literalinclude:: syntax/simplified/.rkd/makefile.yaml


Simplified Python
~~~~~~~~~~~~~~~~~

- Practical replacement for YAML syntax, good choice for more advanced tasks
- Has more flexibility on the structure, tasks and other code can be placed in different files and packages
- Created tasks are not possible to be shared as part of Python package, or at least difficult and should not be


.. literalinclude:: syntax/simplified/.rkd/makefile.py


Classic Python
~~~~~~~~~~~~~~

- Provides a full control without any limits on tasks extending
- Has more flexibility on the structure, tasks and other code can be placed in different files and packages
- Best fits for creating shareable tasks using local and remote Python packages


.. literalinclude:: syntax/classic/.rkd/makefile.py


.. include:: syntax-reference.rst
