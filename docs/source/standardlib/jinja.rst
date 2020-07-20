JINJA
=====

Renders JINJA2 files, and whole directories of files. Allows to render by pattern.

All includes and extends are by default looking in current working directory path.

:j2:render
~~~~~~~~~~
.. jinja:: j2_render
   :file: source/templates/package-usage.rst

Renders a single file from JINJA2.


**Example of usage:**

.. code:: bash

    rkd :j2:render -s SOURCE-FILE.yaml.j2 -o OUTPUT-FILE.yaml


:j2:directory-to-directory
~~~~~~~~~~~~~~~~~~~~~~~~~~
.. jinja:: j2_render
   :file: source/templates/package-usage.rst

Renders all files recursively in given directory to other directory.
Can remove source files after rendering them to the output files.

*Note: Pattern is a regexp pattern that matches whole path, not only file name*

*Note: Exclude pattern is matching on SOURCE files, not on target files*


**Example usage:**

.. code:: bash

    rkd :j2:directory-to-directory \
        --source="/some/path/templates" \
        --target="/some/path/rendered" \
        --delete-source-files \
        --pattern="(.*).j2"
