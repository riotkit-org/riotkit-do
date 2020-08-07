
RiotKit-Do (RKD)
================

*Stop writing hacks in Makefile, use Python snippets for advanced usage, for the rest use simple few lines of Bash, share code between your projects using Python Packages.*


**What I can do with RKD?**

- Simplify the scripts
- Do not reinvent the wheel (argument parsing, logs, error handling for example)
- Share the code across projects and organizations, use native Python Packaging
- Natively integrate scripts with .env files


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

The "Quick start" section ends up with a **.rkd** directory, a requirements.txt and setup-venv.sh

1. Use **eval $(setup-venv.sh)** to enter shell of your project, where RKD is installed with all dependencies
2. Each time you install anything from **pip** in your project - add it to requirements.txt, you can install additional RKD tasks from pip
3. In **.rkd/makefile.yaml** you can start adding your first tasks and imports

Tutorial - makefile.yaml (YAML syntax)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's at the beginning start from analyzing an example.

.. code:: yaml

    version: org.riotkit.rkd/yaml/v1

    # optional
    imports:
        - rkt_utils.db.WaitForDatabaseTask

    # optional
    environment:
        PYTHONPATH: "/project/src"

    # optional
    #env_files:
    #    - .some-dotenv-file

    tasks:
        :check-is-using-linux:
            description: Are you using Linux?
            steps:
                - "[[ $(uname -s) == \"Linux\" ]] && echo \"You are using Linux, cool\""

        :hello:
            description: Say hello
            arguments:
                "--name":
                    help: "Your name"
                    required: true
                    #default: "Peter"
                    #option: "store_true" # for booleans
            steps: |
                echo "Hello ${ARG_NAME}"

                if [[ $(uname -s) == "Linux" ]]; then
                    echo "You are a Linux user"
                fi


**imports** - Imports external tasks installed via Python' PIP. That's the way to easily share code across projects

**environment** - Can define default values for environment variables. Environment section can be defined for all tasks, or per task

**env_files** - Includes .env files, can be used also per task

**tasks** - List of available tasks, each task has a name, descripton, list of steps (or a single step), arguments


**Running the example:**

1. Create a .rkd directory
2. Create .rkd/makefile.yaml file
3. Paste/rewrite the example into the .rkd/makefile.yaml
4. Run :code:`rkd :tasks` from the directory where the .rkd directory is placed
5. Run defined tasks :code:`rkd :hello :check-is-using-linux`

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

