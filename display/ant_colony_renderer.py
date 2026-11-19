import pygame

from algorithms.ant_colony import AntColony
from display.algorithm_renderer import AlgorithmRenderer
from display import theme

MIN_TRAIL_ALPHA = 18
MAX_TRAIL_ALPHA = 220
MAX_TRAIL_WIDTH = 5


class AntColonyRenderer(AlgorithmRenderer):
    name = "Ant Colony Optimization"
    accent = theme.ACO_ACCENT

    def __init__(self):
        self._trail_surface = None

    def draw(self, screen: pygame.Surface, algorithm: AntColony):
        self.draw_pheromones(screen, algorithm)
        theme.draw_tour(screen, algorithm.best_tour)

    def draw_agents(self, screen: pygame.Surface, algorithm: AntColony):
        for ant in algorithm.ants:
            theme.draw_agent(screen, self.accent, (ant.current_node.x, ant.current_node.y))

    def draw_pheromones(self, screen: pygame.Surface, ant_colony: AntColony):
        """Trail strength is shown relative to the weakest/strongest trail, so it stays
        readable for any number of ants or evaporation rate."""
        if self._trail_surface is None or self._trail_surface.get_size() != screen.get_size():
            self._trail_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self._trail_surface.fill((0, 0, 0, 0))

        nodes = {node.node_id: node for node in ant_colony.graph.get_nodes()}
        values = ant_colony.pheromones.values()
        low, high = min(values), max(values)
        span = high - low

        # weak trails first so strong ones are on top
        for (node_a_id, node_b_id), pheromone in sorted(ant_colony.pheromones.items(), key=lambda item: item[1]):
            ratio = (pheromone - low) / span if span > 0 else 0
            alpha = int(MIN_TRAIL_ALPHA + (MAX_TRAIL_ALPHA - MIN_TRAIL_ALPHA) * ratio)
            width = 1 + round((MAX_TRAIL_WIDTH - 1) * ratio)
            node_a, node_b = nodes[node_a_id], nodes[node_b_id]
            pygame.draw.line(
                self._trail_surface,
                (*self.accent, alpha),
                (node_a.x, node_a.y),
                (node_b.x, node_b.y),
                width
            )

        screen.blit(self._trail_surface, (0, 0))

    def info_lines(self, algorithm: AntColony) -> list[str]:
        iteration = min(algorithm.current_iteration + 1, algorithm.max_iterations)
        return [
            f"Iteration: {iteration}/{algorithm.max_iterations}",
            f"Ants: {algorithm.number_of_ants}",
            f"alpha={algorithm.alpha:g}  beta={algorithm.beta:g}  rho={algorithm.evaporation_rate:g}",
        ]

    def legend_items(self):
        return [
            ("fade", self.accent, "Pheromone trails"),
            ("line", theme.BEST_TOUR_COLOR, "Best tour"),
            ("dot", self.accent, "Ants"),
        ]
