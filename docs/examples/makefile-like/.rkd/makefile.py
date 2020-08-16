
from rkd.api.syntax import TaskAliasDeclaration as Task

#
# Example of Makefile-like syntax
#

IMPORTS = []

TASKS = [
    Task(':find-images', [
        ':sh', '-c', 'find ../../ -name \'*.png\''
    ]),

    Task(':build', [':sh', '-c', ''' set -x;
        cd ../../../
    
        chmod +x setup.py
        ./setup.py build
        
        ls -la
    ''']),

    # https://github.com/riotkit-org/riotkit-do/issues/43
    Task(':hello', [':sh', '-c', 'echo "Hello world"']),
    Task(':alias-in-alias-test', [':hello'])
]
