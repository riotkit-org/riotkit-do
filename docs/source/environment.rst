Working with environment variables
==================================

In a project-focused conception RKD is allowing to define environment variables in three places.

1) Dotenv
---------

:code:`.env` file is loaded on each RKD startup from directory, where :code:`./rkdw` is launched.

2) Document scope
-----------------

When operating on YAML there is a possibility to define a makefile-scoped environment variables, inline and loaded from dotenv file.

.. code:: yaml

    version: org.riotkit.rkd/yaml/v1
    environment:
        STOP: "Police brutality"
    env_files:
        - .env-prod
    tasks: {}


3) Task scope
-------------

.. code:: yaml

    version: org.riotkit.rkd/yaml/v1
    tasks:
        :task1:
            environment:
                STOP: "Police brutality"
            env_files:
                - .env-prod
            steps: |
                echo "STOP: ${STOP}"


4) Operating system scope
-------------------------

Traditional, expected way how to pass the environment variables.

.. code:: bash

    STOP="Police brutality" ./rkdw :task1


Priority
--------

Later has higher priority.

1. Dotenv loaded at startup
2. Document scope
3. Task scope
4. Operating system
