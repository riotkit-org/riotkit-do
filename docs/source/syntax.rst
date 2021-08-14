Syntax
======

RKD is elastic. Different syntax allows to choose between ease of usage and extended possibilities.


YAML
~~~~

- Best choice to start with RKD, perfect for simpler usage
- Gives clear view on what is defined, has obvious structure
- Created tasks are not possible to be shared as part of Python package


.. literalinclude:: syntax/simplified/.rkd/makefile.yaml


Simplified Python
~~~~~~~~~~~~~~~~~

- Practical replacement for YAML syntax, good choice for more advanced tasks
- Has more flexibility on the structure, tasks and other code can be placed in different files and packages
- Created tasks are not possible to be shared as part of Python package, or at least difficult and should not be


.. literalinclude:: syntax/simplified/.rkd/makefile.py


Classic Python
~~~~~~~~~~~~~~

- Provides a full control without any limits on tasks extending
- Has more flexibility on the structure, tasks and other code can be placed in different files and packages
- Best fits for creating shareable tasks using local and remote Python packages


.. literalinclude:: syntax/classic/.rkd/makefile.py


Syntax reference
~~~~~~~~~~~~~~~~

+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| Simplified Python                                                       | Python Class                                         | YAML                            | Description                                 |
+=========================================================================+======================================================+=================================+=============================================+
| get_steps(task: MultiStepLanguageAgnosticTask) -> List[str]:            | get_steps                                            | steps: [""]                     | List of steps in any language (only if      |
|                                                                         |                                                      |                                 | extending MultiStep LanguageAgnosticTask)   |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| stdin()                                                                 | N/A                                                  | input: ""                       | Standard input text                         |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| @extends(ClassName) decorator on a main method                          | ClassName(BaseClass)                                 | extends: package.name.ClassName | Which Base Task should be extended          |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| execute(task: BaseClassNameTask, ctx: ExecutionContext):                | execute(self, ctx: ExecutionContext)                 | execute: ""                     | Python code to execute                      |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| inner_execute(task: BaseClassNameTask, ctx: ExecutionContext):          | inner_execute(self, ctx: ExecutionContext)           | inner_execute: ""               | Python code to execute inside               |
|                                                                         |                                                      |                                 | inner_execute (if implemented by Base Task) |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| compile(task: BaseClassNameTask, event: CompilationLifecycleEvent):     | compile(self, event: CompilationLifecycleEvent):     | N/A                             | Python code to execute during               |
|                                                                         |                                                      |                                 | Context compilation process                 |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| configure(task: BaseClassNameTask, event: ConfigurationLifecycleEvent): | configure(self, event: ConfigurationLifecycleEvent): | configure: ""                   | Python code to execute during Task          |
|                                                                         |                                                      |                                 | configuration process                       |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| get_description()                                                       | get_description(self)                                | description: ""                 | Task description                            |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| get_group_name()                                                        | get_group_name()                                     | N/A                             | Group name                                  |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| internal=True in TaskDeclaration                                        | internal=True in TaskDeclaration                     | internal: False                 | Is task considered                          |
|                                                                         |                                                      |                                 | internal? (hidden on                        |
|                                                                         |                                                      |                                 | :tasks list)                                |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| become in TaskDeclaration (or commandline switch)                       | become in TaskDeclaration                            | become: root                    | Change user for task execution time         |
|                                                                         | (or commandline switch)                              |                                 |                                             |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| workdir in TaskDeclaration                                              | workdir in TaskDeclaration                           | workdir: /some/path             | Change working directory for task           |
|                                                                         |                                                      |                                 | execution time                              |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
| configure_argparse(task: BaseClassNameTask, parser: ArgumentParser)     | configure_argparse(self, parser: ArgumentParser)     | arguments: {}                   | Configure argparse.ArgumentParser object    |
+-------------------------------------------------------------------------+------------------------------------------------------+---------------------------------+---------------------------------------------+
