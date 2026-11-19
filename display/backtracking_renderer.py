import pygame

from algorithms.backtracking import Backtracking
from display.algorithm_renderer import AlgorithmRenderer
from display import theme


class BacktrackingRenderer(AlgorithmRenderer):
    name = "Backtracking"
    accent = theme.BACKTRACKING_ACCENT

    def draw(self, screen: pygame.Surface, algorithm: Backtracking):
        theme.draw_tour(screen, algorithm.best_tour)
        self.draw_current_path(screen, algorithm)

    def draw_agents(self, screen: pygame.Surface, algorithm: Backtracking):
        if not algorithm.path or algorithm.is_finished():
            return
        node = algorithm.path[-1]
        theme.draw_agent(screen, self.accent, (node.x, node.y))

    def draw_current_path(self, screen: pygame.Surface, backtracking: Backtracking):
        if backtracking.is_finished():
            return
        path = backtracking.path
        for i in range(len(path) - 1):
            theme.draw_dashed_line(
                screen,
                self.accent,
                (path[i].x, path[i].y),
                (path[i + 1].x, path[i + 1].y)
            )

    def info_lines(self, algorithm: Backtracking) -> list[str]:
        return [
            f"Depth: {len(algorithm.path)}/{algorithm.graph.get_size()}",
            f"Current path: {algorithm.current_distance:.1f}",
            f"Pruning: {'on' if algorithm.use_pruning else 'off'}",
        ]

    def legend_items(self):
        return [
            ("dashed", self.accent, "Current path"),
            ("line", theme.BEST_TOUR_COLOR, "Best tour"),
            ("dot", self.accent, "Current node"),
        ]
