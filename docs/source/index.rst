
Riotkit Do (RKD)
================

Quick start
-----------

RKD is delivered as a Python Package. All externally provided tasks should be also installable via Python's PIP.

.. code:: bash

    virtualenv .venv
    source .venv/bin/activate

    echo "rkd" > requirements.txt
    #echo "rkd==0.1" > requirements.txt  # better choose a stable tag and use fixed version for stability

    pip install -r requirements.txt
    rkd :rkd:create-structure

Conception
----------

Simple task executor with clear rules and early validation of input parameters.
Each task specified to be run is treated like a separate application - has it's own parameters, by default inherits global settings but those could be overridden.
The RKD version and version of any installed tasks are managed by Python Packaging.

**Basic examples:**

.. code:: bash

    rkd :tasks

    # runs two tasks ":sh" with different arguments
    rkd :sh -c 'echo hello' :sh -c 'ps aux'

    # runs different tasks in order
    rkd :py:clean :py:build :py:publish --user=__token__ --password=123456

    # allows to fail one of tasks in our pipeline (does not interrupt the pipeline when first task fails)
    rkd :sh -c 'exit 1' --keep-going :sh -c 'echo hello'

    # silent output, only tasks stdout and stderr is visible (for parsing outputs in scripts)
    rkd --silent :sh -c "ps aux"


.. image:: ../tasks.png

.. image:: ../python.png


Usage in shell
--------------

Tasks are prefixed always with ":".
Each task can handle it's own arguments.

Tasks arguments usage
~~~~~~~~~~~~~~~~~~~~~

*makefile.py*

.. code:: python


    from rkd.syntax import TaskDeclaration, TaskAliasDeclaration
    from rkd.standardlib.python import PublishTask

    IMPORTS = [
        TaskDeclaration(PublishTask())
    ]

    TASKS = [
        TaskAliasDeclaration(':my:test', [':py:publish', '--username=...', '--password=...'])
    ]

**Example of calling same task twice, but with different input**

Notes for this example: The "username" parameter is a default defined in
``makefile.py`` in this case.

.. code:: bash

    $ rkd :my:test --password=first :my:test --password=second
     >> Executing :py:publish
    Publishing
    {'username': '...', 'password': 'first'}

     >> Executing :py:publish
    Publishing
    {'username': '...', 'password': 'second'}

**Example of calling same task twice, with no extra arguments**

In this example the argument values "..." are taken from ``makefile.py``

.. code:: bash

    $ rkd :my:test :my:test
     >> Executing :py:publish
    Publishing
    {'username': '...', 'password': '...'}

     >> Executing :py:publish
    Publishing
    {'username': '...', 'password': '...'}

**Example of --help per command:**

.. code:: bash

    $ rkd :my:test :my:test --help
    usage: :py:publish [-h] [--username USERNAME] [--password PASSWORD]

    optional arguments:
      -h, --help           show this help message and exit
      --username USERNAME  Username
      --password PASSWORD  Password

Paths and inheritance
~~~~~~~~~~~~~~~~~~~~~

RKD by default search for .rkd directory in current execution directory - `./.rkd`.


**The search order is following (from lower to higher load priority):**

1. RKD's internals (we provide a standard tasks like `:tasks`, `:init`, `:sh`, `:exec` and more)
2. `/usr/lib/rkd`
3. User's home `~/.rkd`
4. Current directory `./.rkd`
5. `RKD_PATH`

**Custom path defined via environment variable**

RKD_PATH allows to define multiple paths that would be considered in priority.

`RKD_PATH="/some/path:/some/other/path:/home/user/riotkit/.rkd-second"`

**How the makefile.py are loaded?**

Each makefile.py is loaded in order, next makefile.py can override tasks of previous.
That's why we at first load internals, then your tasks.



.. toctree::
   :maxdepth: 5
   :caption: Contents:

   standardlib/index

