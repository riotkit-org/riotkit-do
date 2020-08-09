"""
Forked executor takes a Python code and executes as a separate process.

Schema:
   1. RKD spawns PYTHON process that executes THIS SCRIPT
   2. RKD passes context and task code via stdin
   3. Process is unpacking the data, executing the task
   4. Possible errors are catched and passed via temporary file to RKD
   5. Return result is passed via temporary file to RKD

This method gives us a possibility to change user on-the-fly (in Docker containers it is very helpful)
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
