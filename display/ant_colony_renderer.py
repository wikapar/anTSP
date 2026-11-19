import pygame

from algorithms.ant_colony import AntColony
from display.algorithm_renderer import AlgorithmRenderer


class AntColonyRenderer(AlgorithmRenderer):
    def __init__(self):
        self.ant_radius = 5
        self.max_pheromone_width = 6

    def draw(self, screen: pygame.Surface, algorithm: AntColony):
        self.draw_pheromones(screen, algorithm)
        self.draw_best_tour(screen, algorithm)
        self.draw_ants(screen, algorithm)

    def draw_pheromones(self, screen: pygame.Surface, ant_colony: AntColony):
        nodes = {
            node.node_id: node
            for node in ant_colony.graph.get_nodes()
        }

        max_pheromone = max(
            ant_colony.pheromones.values(),
            default=1
        )

        for (node_a_id, node_b_id), pheromone in ant_colony.pheromones.items():
            node_a = nodes[node_a_id]
            node_b = nodes[node_b_id]

            intensity = pheromone / max_pheromone
            width = max(1, int(intensity * self.max_pheromone_width))

            pygame.draw.line(
                screen,
                (255, 150, 0),
                (node_a.x, node_a.y),
                (node_b.x, node_b.y),
                width
            )

    def draw_ants(self, screen: pygame.Surface, ant_colony: AntColony):
        for ant in ant_colony.ants:
            pygame.draw.circle(
                screen,
                (220, 30, 30),
                (ant.current_node.x, ant.current_node.y),
                self.ant_radius
            )

    def draw_best_tour(self, screen: pygame.Surface, ant_colony: AntColony):
        if ant_colony.best_tour is None:
            return

        points = [
            (node.x, node.y)
            for node in ant_colony.best_tour
        ]

        pygame.draw.lines(
            screen,
            (30, 200, 30),
            False,
            points,
            3
        )