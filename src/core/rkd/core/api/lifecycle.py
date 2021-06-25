"""
Lifecycle contract
==================
"""


class CompilationLifecycleEventAware(object):
    def compile(self, event: 'CompilationLifecycleEvent') -> None:
        """
        Execute code after all tasks were collected into a single context
        """
        pass
