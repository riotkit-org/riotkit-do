ENV
===

Manipulates the environment variables stored in a .env file

RKD is always loading an .env file on startup, those tasks in this package allows to manage variables stored in .env file in the scope of a project.

:env:get
~~~~~~~~~~
.. jinja:: env_get
   :file: source/templates/package-usage.rst


**Example of usage:**

.. code:: bash

    rkd :env:get --name COMPOSE_PROJECT_NAME

:env:set
~~~~~~~~~~
.. jinja:: env_set
   :file: source/templates/package-usage.rst


**Example of usage:**

.. code:: bash

    rkd :env:set --name COMPOSE_PROJECT_NAME --value hello
    rkd :env:set --name COMPOSE_PROJECT_NAME --ask
    rkd :env:set --name COMPOSE_PROJECT_NAME --ask --ask-text="Please enter your name:"
