#!/usr/bin/env python3

from rkd.core.api.syntax import TaskAliasDeclaration as TaskAlias

# SUBPROJECTS = ['terraform']

IMPORTS = []

PIPELINES = [
    TaskAlias(':list', [':sh', '-c', 'pwd', ':sh', '-c', 'ls -la'],
              description='Should be in testsubproject1->infrastructure')
]

TASKS = []
