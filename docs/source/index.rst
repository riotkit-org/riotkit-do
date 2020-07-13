
RiotKit-Do (RKD)
================

*Stop writing hacks in Makefile, use Python snippets for advanced usage, for the rest use simple few lines of Bash, share code between your projects using Python Packages.*


**RKD can be used on PRODUCTION, for development, for testing, to replace some of Bash scripts inside docker containers,
and for many more, where Makefile was used.**

Example use cases
~~~~~~~~~~~~~~~~~

- Docker based production environment with multiple configuration files, procedures (see: `Harbor project <https://github.com/riotkit-org/riotkit-harbor>`_)
- Database administrator workspace (importing dumps, creating new user accounts, plugging/unplugging databases)
- Development environment (executing migrations, importing test database, splitting tests and running parallel)
- On CI (prepare project to run on eg. Jenkins or Gitlab CI) - RKD is reproducible on local computer which makes inspection easier
- Kubernetes/OKD deployment workspace (create shared YAML parts with JINJA2 between multiple environments and deploy from RKD)
- Automate things like certificate regeneration on production server, RKD can generate any application configs using JINJA2
- Installers (RKD has built-in commands for replacing lines in files, modifying .env files)

Quick start
~~~~~~~~~~~

.. code:: bash

    # 1) via PIP
    pip install rkd

    # 2) Create project (will create a virtual env and commit files to GIT)
    rkd :rkd:create-structure --commit


Getting started with RKD
~~~~~~~~~~~~~~~~~~~~~~~~

The "Quick start" section will end up with a **.rkd** directory, a requirements.txt and setup-venv.sh

1. Use **eval $(setup-venv.sh)** to enter shell of your project, where RKD is installed with all dependencies
2. Each time you install anything from **pip** in your project - add it to requirements.txt, you can install additional RKD tasks from pip
3. In **.rkd/makefile.yaml** you can start adding your first tasks and imports


Read more
~~~~~~~~~

- YAML syntax is described in :ref:`Tasks development` section
- Writing Python code in makefile.yaml requires to lookup :ref:`Tasks API`
- Learn how to import installed tasks via pip - :ref:`Importing tasks`


.. image:: ../tasks.png

.. image:: ../python.png


.. toctree::
   :maxdepth: 5
   :caption: Contents:

   quickstart
   standardlib/index
   usage/index

