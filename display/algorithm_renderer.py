from abc import ABC, abstractmethod
import pygame

from algorithms.algorithm import Algorithm


class AlgorithmRenderer(ABC):
    """Every renderer draws only on the graph area.
    The header (title, status, stats, legend) is drawn by the Display in the same way
    for every algorithm, the renderer just provides the content for it."""

    name: str = "Algorithm"
    accent: tuple = (255, 255, 255)  # color of the algorithm (search state + chart line)

    @abstractmethod
    def draw(self, screen: pygame.Surface, algorithm: Algorithm):
        """Draws below the nodes (edges, tours, trails)."""
        pass

    def draw_agents(self, screen: pygame.Surface, algorithm: Algorithm):
        """Draws on top of the nodes (ants, current node...)."""
        pass

    def info_lines(self, algorithm: Algorithm) -> list[str]:
        """Algorithm specific information shown in the header."""
        return []

    def legend_items(self) -> list[tuple[str, tuple, str]]:
        """List of (symbol kind, color, label). Kinds: 'line', 'dashed', 'dot', 'fade'."""
        return []
