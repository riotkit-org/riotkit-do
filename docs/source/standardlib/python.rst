Python
======

Set of Python-related tasks for building, testing and publishing Python packages.

.. image:: ../../python.png

:py:publish
~~~~~~~~~~~

Publish a package to the PyPI.

**Example of usage:**

.. code:: bash

    rkd :py:publish --username=__token__ --password=.... --skip-existing --test


:py:build
~~~~~~~~~

Runs a build through setuptools.

:py:install
~~~~~~~~~~~

Installs the project as Python package using setuptools. Calls ./setup.py install.

:py:clean
~~~~~~~~~

Removes all files related to building the application.

:py:unittest
~~~~~~~~~~~~

Runs Python's built'in unittest module to execute unit tests.

**Examples:**

.. code:: bash

    rkd :py:unittest
    rkd :py:unittest -p some_test
    rkd :py:unittest --tests-dir=../test

