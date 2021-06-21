#!/usr/bin/env python3

from rkd.core.api.syntax import TaskAliasDeclaration as TaskAlias

SUBPROJECTS = []
IMPORTS = []
PIPELINES = [
    TaskAlias(':apply', [':sh', '-c', 'pwd', ':sh', '-c', 'ls -la'], description='terraform apply'),
    TaskAlias(':pwd', [':sh', '-c', 'pwd; echo "from terraform"'], description='Shows current working directory')
]
TASKS = []
