.. _Best practices:

Best practices
==============


Do not use os.getenv()
----------------------

The ExecutionContext is providing processed environment variables. Variables could be overridden on some levels
eg. in makefile.py - :code:`rkd.core.api.syntax.TaskAliasDeclaration` can take a dict of environment variables to force override.

Use :code:`context.get_env()` instead.


Define your environment variables
---------------------------------

*Note: Only in Python code*

By using :code:`context.get_env()` you are enforced to implement a :code:`TaskInterface.get_declared_envs()` returning
a list of all environment variables used in your task code.

All defined environment variables will land in --help, which is considered as a task self-documentation.


Use sh() and exec() to invoke commands
--------------------------------------

Using raw :code:`subprocess` will make your commands output invisible in logs, as the subprocess is writting directly to stdout/stderr skipping sys.stdout and sys.stderr.
The methods provided by RKD are buffering the output and making it possible to save to both file and to console.


Do not print if you do not must, use io()
-----------------------------------------

:code:`rkd.core.api.inputoutput.IO` provides a standardized way of printing messages. The class itself distinct importance of messages, writing them
to proper stdout/stderr and to log files.

:code:`print` is also captured by IO, but should be used only eventually.


Use tasks expansion or pipelines instead of dynamic tasks creation in Makefile
------------------------------------------------------------------------------

Makefiles are not designed to execute logic outside tasks execution. As long as it is possible use :code:`compilation stage` to expand task into a group of tasks, see
:ref:`Task expansion pattern` chapter of the documentation.

Standard way of tasks creation helps other people to understand your construction due to a common usage of a defined pattern in our documentation.
Second argument is that things defined using :ref:`Task expansion pattern` are possible to package into a Python package.


Invoke RKD subtasks as a pipeline or tasks expansion
----------------------------------------------------

Invoking tasks in the middle of one of tasks code signals an architecture fault. Your tasks probably are having too many responsibilities.
To be SOLID split tasks into smaller pieces and create a pipeline or task expansion.


Don't mix dependencies between subprojects - rethink project structure
----------------------------------------------------------------------

RKD contexts are built at compilation stage, therefore it is possible that in :code:`subproject` A you can use tasks from :code:`subproject B`

**Solutions to avoid complex dependencies:**

- Extract common things into base tasks accessible in the PYTHONPATH, or best in a separate package
- Create aggregated pipelines on top level, before the subprojects, e.g. on project level. This requires to cut subprojects into smaller pieces to pilot the behavior from project level

Having complex dependencies in subprojects is again a signal of a invalid design.


Keep compilation and configuration stage fast
---------------------------------------------

Compilation and configuration stages of every task are not intended to query databases, HTTP servers, to search recursively for files or directories.
All other tasks in project will be affected if at least one task compilation would be slow.


Use configuration stage for validation
--------------------------------------

Configuration stage should be used for validation stage as it is executed for all tasks before first task is executed.
Error messages at early stage, not in the middle of execution are very helpful in practice, increases quality of the automation.
