.. _READ MORE ABOUT YAML SYNTAX IN THE BEGINNERS GUIDE:

Beginners guide - on YAML syntax example
========================================

Where to place files
--------------------

:code:`.rkd` directory must always exists in your project. Inside :code:`.rkd` directory you should place your makefile.yaml that will contain
all of the required tasks.

Just like in UNIX/Linux, and just like in Python - there is an environment variable :code:`RKD_PATH` that allows to define
multiple paths to :code:`.rkd` directories placed in other places - for example outside of your project. This gives a flexibility and possibility
to build system-wide tools installable via Python's PIP.

Environment variables
---------------------

RKD natively reads .env (called also "dot-env files") at startup. You can define default environment values in .env, or in other .env-some-name files
that can be included in :code:`env_files` section of the YAML.

**Scope of environment variables**

:code:`env_files` and :code:`environment` blocks can be defined globally, which will end in including that fact in each task, second possibility is to
define those blocks per task. Having both global and per-task block merges those values together and makes per-task more important.


**Example**

.. code:: yaml

    version: org.riotkit.rkd/yaml/v1
    environment:
        PYTHONPATH: "/project"
    tasks:
        :hello:
            description: Prints variables
            environment:
                SOME_VAR: "HELLO"
            steps: |
                echo "SOME_VAR is ${SOME_VAR}, PYTHONPATH is ${PYTHONPATH}"


Arguments parsing
-----------------

Arguments parsing is a strong side of RKD. Each task has it's own argument parsing, it's own generated --help command.
Python's argparse library is used, so Python programmers should feel like in home.

**Example**

.. code:: yaml

    version: org.riotkit.rkd/yaml/v1
    environment:
        PYTHONPATH: "/project"
    tasks:
        :hello:
            description: Prints your name
            arguments:
                "--name":
                    required: true
                    #option: store_true # for booleans/flags
                    #default: "Unknown" # for default values
            steps: |
                echo "Hello ${ARG_NAME}"


.. code:: bash

    rkd :hello --name Peter

Defining tasks in Python code
-----------------------------

Defining tasks in Python gives wider possibilities - to access Python's libraries, better handle errors, write less tricky code.
RKD has a similar concept to hashbangs in UNIX/Linux.

There are two supported hashbangs + no hashbang:

- #!python
- #!bash
- (just none there)

What can I do in such Python code? Everything! Import, print messages, execute shell commands, everything.

**Example**

.. code:: yaml

    version: org.riotkit.rkd/yaml/v1
    environment:
        PYTHONPATH: "/project"
    tasks:
        :hello:
            description: Prints your name
            arguments:
                "--name":
                    required: true
                    #option: store_true # for booleans/flags
                    #default: "Unknown" # for default values
            steps: |
                #!python
                print('Hello %s' % ctx.get_arg('--name'))


**Special variables**

- *this* - instance of current TaskInterface implementation
- *ctx* - instance of ExecutionContext

Please check :ref:`Tasks API` for those classes reference.
