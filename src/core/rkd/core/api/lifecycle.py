"""
Lifecycle contract
==================
"""
from typing import List


class CompilationLifecycleEventAware(object):
    def compile(self, event: 'CompilationLifecycleEvent') -> None:
        """
        Execute code after all tasks were collected into a single context
        """
        pass


class ConfigurationLifecycleEventAware(object):
    def get_configuration_attributes(self) -> List[str]:
        return []

    def configure(self, event: 'ConfigurationLifecycleEvent') -> None:
        """
        Executes before all tasks are executed. ORDER DOES NOT MATTER, can be executed in parallel.
        """
        pass
