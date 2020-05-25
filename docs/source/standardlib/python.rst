Python
======

*This package was extracted from standardlib to rkd_python, but is maintained together with RKD as part of RKD core.*

Set of Python-related tasks for building, testing and publishing Python packages.

.. image:: ../../python.png

:py:publish
~~~~~~~~~~~

.. jinja:: py_publish
   :file: source/templates/package-usage.rst

Publish a package to the PyPI.

**Example of usage:**

.. code:: bash

    rkd :py:publish --username=__token__ --password=.... --skip-existing --test


:py:build
~~~~~~~~~

.. jinja:: py_build
   :file: source/templates/package-usage.rst

Runs a build through setuptools.

:py:install
~~~~~~~~~~~


.. jinja:: py_install
   :file: source/templates/package-usage.rst

Installs the project as Python package using setuptools. Calls ./setup.py install.

:py:clean
~~~~~~~~~

.. jinja:: py_clean
   :file: source/templates/package-usage.rst

Removes all files related to building the application.

:py:unittest
~~~~~~~~~~~~

.. jinja:: py_unittest
   :file: source/templates/package-usage.rst

Runs Python's built'in unittest module to execute unit tests.

**Examples:**

.. code:: bash

    rkd :py:unittest
    rkd :py:unittest -p some_test
    rkd :py:unittest --tests-dir=../test

