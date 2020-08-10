"""
Forked executor takes a Python code and executes as a separate process.

Schema:
   1. RKD spawns PYTHON process that executes THIS SCRIPT
   2. RKD creates a temporary file for communication
   3. Context and task code is passed to communication file, so the 'forked' subprocess can read it
   4. Process is unpacking the serialized data, executing the task
   5. Possible errors are catch and passed via temporary file to RKD (to re-raise in main process)
   6. Return result is passed via temporary file to RKD

This method gives us a possibility to change user on-the-fly (in Docker containers it is very helpful) and possibly
a chance in the future to implement eg. remote executor or at least partially isolated executor
"""

FORKED_EXECUTOR_TEMPLATE = """
import pickle
import base64
import sys

#
# Load serialized context
#
communication_file = sys.stdin.read().strip()

with open(communication_file, 'rb') as f:
    unserialized = pickle.loads(f.read())

task = unserialized['task']
ctx = unserialized['ctx']


def _communicate_return(val):
    with open(communication_file, 'wb') as f:
        f.write(pickle.dumps(val))


try:
    if not task.execute(ctx):
        _communicate_return(False)
        sys.exit(0)

except Exception as exc:
    _communicate_return(exc)

    sys.exit(0)

_communicate_return(True)
"""
