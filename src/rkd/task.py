
from abc import ABC as AbstractClass, abstractmethod


class TaskInterface(AbstractClass):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_group_name(self) -> str:
        pass

    def get_full_name(self):
        return self.get_group_name() + self.get_name()

