from abc import ABC, abstractmethod
import pygame

from algorithms.algorithm import Algorithm


class AlgorithmRenderer(ABC):

    @abstractmethod
    def draw(self, screen: pygame.Surface, algorithm: Algorithm) -> None:
        pass