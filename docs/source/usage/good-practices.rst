Good practices
==============

Do not use os.getenv()
----------------------

*Note: Only in Python code*

The ExecutionContext is providing processed environment variables. Variables could be overridden on some levels
eg. in makefile.py - :code:`rkd.api.syntax.TaskAliasDeclaration` can take a dict of environment variables to force override.

Use :code:`context.get_env()` instead.

Define your environment variables
---------------------------------

*Note: Only in Python code*

By using :code:`context.get_env()` you are enforced to implement a :code:`TaskInterface.get_declared_envs()` returning
a list of all environment variables used in your task code.

All defined environment variables will land in --help, which is considered as a task self-documentation.

Use sh(), exec(), rkd() and silent_sh()
---------------------------------------

Using raw :code:`subprocess` will make your commands output invisible in logs, as the subprocess is writting directly to stdout/stderr skipping sys.stdout and sys.stderr.
The methods provided by RKD are buffering the output and making it possible to save to both file and to console.

Do not print if you do not must, use io()
-----------------------------------------

:code:`rkd.api.inputoutput.IO` provides a standardized way of printing messages. The class itself distinct importance of messages, writing them
to proper stdout/stderr and to log files.

:code:`print` is also captured by IO, but should be used only eventually.

