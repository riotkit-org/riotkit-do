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


YAML syntax reference
---------------------

Let's at the beginning start from analyzing an example.

.. code:: yaml

    version: org.riotkit.rkd/yaml/v1

    # optional: Import tasks from Python packages
    # This gives a possibility to publish tasks and share across projects, teams, organizations
    imports:
        - rkt_utils.db.WaitForDatabaseTask

    # optional environment section would append those variables to all tasks
    # of course the tasks can overwrite those values in per-task syntax
    environment:
        PYTHONPATH: "/project/src"

    # optional env files loaded there would append loaded variables to all tasks
    # of course the tasks can overwrite those values in per-task syntax
    #env_files:
    #    - .some-dotenv-file

    tasks:
        :check-is-using-linux:
            description: Are you using Linux?
            # use sudo to become a other user, optional
            become: root
            steps:
                # steps can be defined as single step, or multiple steps
                # each step can be in a different language
                # each step can be a multiline string
                - "[[ $(uname -s) == \"Linux\" ]] && echo \"You are using Linux, cool\""
                - echo "step 2"
                - |
                    #!python
                    print('Step 3')

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

**Example projects using Makefile YAML syntax:**

- `Taiga docker image <https://github.com/riotkit-org/docker-taiga/blob/master/.rkd/makefile.yaml>`_
- `Taiga Events docker image <https://github.com/riotkit-org/docker-taiga-events/blob/master/.rkd/makefile.yaml>`_
- `K8S Workspace <https://github.com/riotkit-org/riotkit-do-example-kubernetes-workspace/blob/master/.rkd/makefile.yaml>`_

.. _Read more about Python Makefile syntax:

Extended usage - Makefile in Python syntax
==========================================

Not only tasks can be written in Python code, but Makefile too - such makefile is called :code:`makefile.py`, and placed in :code:`.rkd` directory.

**Example:**

.. literalinclude:: ../../.rkd/makefile.py


- The Python syntax is very flexible
- You can create your own local packages and import them here, create own advanced structure
- Possibility to declare aliases and adjust TaskDeclarations for advanced usage (YAML syntax does not offer this)

**Example projects using Makefile.py syntax:**

- `TunMan <https://github.com/riotkit-org/tunman/blob/master/.rkd/makefile.py>`_
- `RiotKit Harbor building scripts <https://github.com/riotkit-org/riotkit-harbor/blob/master/.rkd/makefile.py>`_
- `RiotKit CI Utils <https://github.com/riotkit-org/ci-utils/blob/master/.rkd/makefile.yaml>`_


Check :ref:`Detailed usage manual` page for description of all environment variables, mechanisms, good practices and more
-------------------------------------------------------------------------------------------------------------------------
