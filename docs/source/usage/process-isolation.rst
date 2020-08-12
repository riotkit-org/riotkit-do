Process isolation and permissions changing with sudo
====================================================

Alternatively called "forking" is a feature of RKD similar to Gradle's JVM forking - the task can be run in a separate
Python's process. This gives a possibility to run specific task as a specific user (eg. upgrade permissions to ROOT or downgrade to regular user)


Mechanism
~~~~~~~~~

RKD uses serialization to transfer data between processes - a standard :code:`pickle` library is used.
Pickle has limitations on what can be serialized - any inner-methods and lambdas cannot be returned by task.

To test if your task is compatible with running as a separate process simply add :code:`--become=USER-NAME` to the commandline of your task.
If it will fail due to serialization issue, then you will be notified with a nice stacktrace.

Technically the mechanism works on the task executor level, it means that process isolation is independent of the programming language as
whole task's execute() is ran in a separate process, even if task is declared in YAML and has Bash steps.

Permissions changing with sudo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

YAML syntax allows to define additional attribute :code:`become`, that if defined then makes whole task to execute inside a separate
Python process ran with sudo.

Additionally the RKD commandline supports a per-task parameter :code:`--become`

Future usage
~~~~~~~~~~~~

The mechanism is universal, it can be possibly used to sandbox, or even to execute tasks remotely.
Currently we do not support such features but we do not say its impossible in the future.
