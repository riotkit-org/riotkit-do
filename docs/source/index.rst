
RiotKit-Do (RKD) usage and development manual
=============================================

RKD is a stable, open-source, multi-purpose automation tool which balance flexibility with simplicity. The primary language is Python
and YAML syntax.

RiotKit-Do can be compared to **Gradle** and to **GNU Make**, by allowing both Python and Makefile-like YAML syntax.

**What can be achieved with RKD?**

- Simplify the scripts
- Put your Python and Bash scripts inside a YAML file (like in GNU Makefile)
- Do not reinvent the wheel (argument parsing, logs, error handling for example)
- Share the code across projects and organizations, use native Python Packaging to share tasks (like in Gradle)
- Natively integrate scripts with .env files
- Automatically generate documentation for your scripts
- Maintain your scripts in a good standard

**RKD can be used on PRODUCTION, for development, for testing, to replace some of Bash scripts inside docker containers,
and for many more, where Makefile was used.**

.. tabs::

   .. tab:: YAML

      .. literalinclude:: syntax/simplified/.rkd/makefile.yaml

   .. tab:: Simplified Python

      .. literalinclude:: syntax/simplified/.rkd/makefile.py

   .. tab:: Classic Python

      .. literalinclude:: syntax/classic/.rkd/makefile.py

Example use cases
~~~~~~~~~~~~~~~~~

- Docker based production environment with multiple configuration files, procedures (see: `Harbor project <https://github.com/riotkit-org/riotkit-harbor>`_)
- Database administrator workspace (importing dumps, creating new user accounts, plugging/unplugging databases)
- Development environment (executing migrations, importing test database, splitting tests and running parallel)
- On CI (prepare project to run on eg. Jenkins or Gitlab CI) - RKD is reproducible on local computer which makes inspection easier
- Application cluster management, deploying applications, adding users, setting permissons
- Automate things like certificate regeneration on production server, RKD can generate any application configs using JINJA2
- Installers (RKD has built-in commands for replacing lines in files, modifying .env files, asking user questions and validating answers)

Install RKD
~~~~~~~~~~~

RiotKit-Do is delivered as a Python package that can be installed system-wide or in a virtual environment.
The virtual environment installation is similar in concept to the Gradle wrapper (gradlew)

.. code:: bash

    # download a wrapper that will automatically setup virtual environment and install RKD
    # do not forget to commit wrapper to the GIT repository
    wget https://github.com/riotkit-org/riotkit-do/blob/master/src/core/rkd/core/misc/initial-structure/rkdw.py -O rkdw
    chmod +x rkdw
    ./rkdw


Getting started in freshly created structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The "Quick start" section ends up with a **.rkd** directory, a requirements.txt and ./rkdw

1. Call RKD using a wrapper in project directory **./rkdw**
2. Each time you install anything from **pip** in your project - add it to requirements.txt (or use :code:`pipenv install`), additional RKD tasks can be installed from PIP
3. In **.rkd/makefile.yaml** add your tasks, pipelines and imports

Create your first task with :ref:`READ MORE ABOUT YAML SYNTAX IN THE BEGINNERS GUIDE`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check how to use commandline to run tasks in RKD with :ref:`Commandline basics`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See how to import existing tasks to your Makefile with :ref:`Importing tasks` page
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Keep learning
~~~~~~~~~~~~~

- YAML syntax is described also in :ref:`Tasks development` section
- Writing Python code in makefile.yaml requires to lookup :ref:`Tasks API`
- Learn how to import installed tasks via pip - :ref:`Importing tasks`
- You can also write tasks code in pure Python and redistribute those tasks via Python's PIP - see :ref:`Tasks development`
- With RKD you can create interactive installers - check the :ref:`Wizard` section


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   makefile-guide
   quickstart
   syntax
   usage/importing-tasks
   extending-tasks
   pipelines
   project-structure
   standardlib/index
   environment
   writing-tasks
   usage/index
   rts/index
   architecture/index

