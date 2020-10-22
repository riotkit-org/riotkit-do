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

import pickle


FORKED_EXECUTOR_TEMPLATE = """
import pickle
import base64
import sys

def _communicate_return(val):
    with open(communication_file, 'wb') as f:
        f.write(pickle.dumps(val))


communication_file = sys.argv[1]

try:
    #
    # Load serialized context
    #
    
    with open(communication_file, 'rb') as f:
        unserialized = pickle.loads(f.read())
    
    task = unserialized['task']
    ctx = unserialized['ctx']

    if not task.execute(ctx):
        _communicate_return(False)
        sys.exit(0)

except Exception as exc:
    _communicate_return(exc)

    sys.exit(0)

_communicate_return(True)
"""


def get_unpicklable(instance, exception=None, string='', first_only=True):
    """
    Recursively go through all attributes of instance and return a list of whatever
    can't be pickled.

    Set first_only to only print the first problematic element in a list, tuple or
    dict (otherwise there could be lots of duplication).

    See: https://stackoverflow.com/a/55224405/6782994 (author)
    """
    problems = []
    if isinstance(instance, tuple) or isinstance(instance, list):
        for k, v in enumerate(instance):
            try:
                pickle.dumps(v)
            except BaseException as e:
                problems.extend(get_unpicklable(v, e, string + f'[{k}]'))
                if first_only:
                    break
    elif isinstance(instance, dict):
        for k in instance:
            try:
                pickle.dumps(k)
            except BaseException as e:
                problems.extend(get_unpicklable(
                    k, e, string + f'[key type={type(k).__name__}]'
                ))
                if first_only:
                    break
        for v in instance.values():
            try:
                pickle.dumps(v)
            except BaseException as e:
                problems.extend(get_unpicklable(
                    v, e, string + f'[val type={type(v).__name__}]'
                ))
                if first_only:
                    break
    else:
        for k, v in instance.__dict__.items():
            try:
                pickle.dumps(v)
            except BaseException as e:
                problems.extend(get_unpicklable(v, e, string + '.' + k))

    # if we get here, it means pickling instance caused an exception (string is not
    # empty), yet no member was a problem (problems is empty), thus instance itself
    # is the problem.
    if string != '' and not problems:
        problems.append(
            string + f" (Type '{type(instance).__name__}' caused: {exception})"
        )

    return problems
