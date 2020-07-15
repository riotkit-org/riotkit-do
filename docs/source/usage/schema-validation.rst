Working with YAML files
=======================

Makefile.yaml has checked syntax before it is parsed by RKD. A **jsonschema** library was used to validate YAML files
against a JSON formatted schema file.

This gives the early validation of typing inside of YAML files, and a clear message to the user about place where the typo is.

YAML parsing API
----------------

Schema validation is a part of YAML parsing, the preferred way of working with YAML files is to not only parse the schema
but also validate. In result of this there is a class that wraps **yaml** library - **rkd.yaml_parser.YamlFileLoader**,
use it instead of plain **yaml** library.


*Notice: The YAML and schema files are automatically searched in .rkd, .rkd/schema directories, including RKD_PATH*


**Example usage:**

.. code:: python

    from rkd.yaml_parser import YamlFileLoader

    parsed = YamlFileLoader([]).load_from_file('deployment.yml', 'org.riotkit.harbor/deployment/v1')


FAQ
---

1. *FileNotFoundError: Schema "my-schema-name.json" cannot be found, looked in: ['.../riotkit-harbor', '/.../riotkit-harbor/schema', '/.../riotkit-harbor/.rkd/schema', '/home/.../.rkd/schema', '/usr/lib/rkd/schema', '/usr/lib/python3.8/site-packages/rkd/internal/schema']*

The schema file cannot be found, the name is invalid or file missing. The schema should be placed somewhere in the .rkd/schema directory - in global, in home directory or in project.


2. *rkd.exception.YAMLFileValidationError: YAML schema validation failed at path "tasks" with error: [] is not of type 'object'*

It means you created a list (starts with "-") instead of dictionary at "tasks" path.

**Example what went wrong:**

.. code:: yaml

    tasks:
        - description: first
        - description: second

**Example how it should be as an 'object':**

.. code:: yaml

    tasks:
        first:
            description: first

        second:
            description: second


API
---

.. autoclass:: rkd.yaml_parser.YamlFileLoader
   :members:
