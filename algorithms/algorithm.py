from abc import ABC, abstractmethod

class Algorithm(ABC):

    @abstractmethod
    def step(self):
        pass

    @abstractmethod
    def is_finished(self):
        pass