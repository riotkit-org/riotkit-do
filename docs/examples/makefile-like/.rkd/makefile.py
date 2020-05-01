
from rkd.syntax import TaskAliasDeclaration as Task

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
    '''])
]
