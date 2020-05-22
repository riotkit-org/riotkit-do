JINJA
=====

Renders JINJA2 files, and whole directories of files. Allows to render by pattern.

:j2:render
~~~~~~~~~~
**Class name:** rkd.standardlib.jinja.FileRendererTask

**Package:** rkd.standardlib.jinja

Renders a single file from JINJA2.


**Example of usage:**

.. code:: bash

    rkd :j2:render -s SOURCE-FILE.yaml.j2 -o OUTPUT-FILE.yaml


:j2:directory-to-directory
~~~~~~~~~~~~~~~~~~~~~~~~~~
**Class name:** rkd.standardlib.jinja.RenderDirectoryTask

**Package:** rkd.standardlib.jinja

Renders all files recursively in given directory to other directory.
Can remove source files after rendering them to the output files.

*Pattern is a regexp pattern that matches whole path, not only file name*


**Example usage:**

.. code:: bash

    rkd :j2:directory-to-directory \
        --source="/some/path/templates" \
        --target="/some/path/rendered" \
        --delete-source-files \
        --pattern="(.*).j2"
