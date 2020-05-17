Troubleshooting
===============

1. Output is corrupted or there is no output from a shell command executed inside of a task

The output capturing is under testing. The Python's subprocess module is skipping "sys.stdout" and "sys.stderr" by writing directly to /dev/stdout and /dev/stderr, which makes output capturing difficult.

Run rkd in compat mode to turn off output capturing from shell commands:

.. code:: bash

    RKD_COMPAT_SUBPROCESS=true rkd :some-task-here
