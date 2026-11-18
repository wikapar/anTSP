import pygame

from display.algorithm_renderer import AlgorithmRenderer
from display.graph_renderer import GraphRenderer


class Display:
    def __init__(self, width: int, height: int, algorithm_renderer: AlgorithmRenderer):
        self.width = width
        self.height = height

        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("TSP Visualizer")

        self.font = pygame.font.SysFont(None, 20)

        self.graph_renderer = GraphRenderer()
        self.algorithm_renderer = algorithm_renderer

    def draw(self, simulation):
        self.screen.fill((25, 25, 25))

        self.graph_renderer.draw(
            self.screen,
            simulation.graph
        )

        self.algorithm_renderer.draw(
            self.screen,
            simulation.algorithm
        )
        pygame.display.flip()


    def clear(self):
        self.screen.fill((25, 25, 25))

    def update(self):
        pygame.display.flip()


    def close(self):
        pygame.quit()