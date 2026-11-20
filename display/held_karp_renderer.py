import pygame

from algorithms.held_karp import HeldKarp
from display.algorithm_renderer import AlgorithmRenderer
from display import theme


class HeldKarpRenderer(AlgorithmRenderer):
    name = "Held-Karp (DP)"
    accent = theme.HELD_KARP_ACCENT

    def draw(self, screen: pygame.Surface, algorithm: HeldKarp):
        theme.draw_tour(screen, algorithm.best_tour)
        if algorithm.is_finished():
            return
        nodes = algorithm.graph.get_nodes()
        path = [nodes[i] for i in algorithm.current_best_path()]
        for a, b in zip(path, path[1:]):
            theme.draw_dashed_line(screen, self.accent, (a.x, a.y), (b.x, b.y))

    def draw_agents(self, screen: pygame.Surface, algorithm: HeldKarp):
        if algorithm.is_finished():
            return
        nodes = algorithm.graph.get_nodes()
        for node_id in algorithm.current_subset_ids():
            node = nodes[node_id]
            pygame.draw.circle(screen, self.accent, (node.x, node.y), theme.AGENT_RADIUS + 3, 2)

    def info_lines(self, algorithm: HeldKarp) -> list[str]:
        size = algorithm.subset_size(algorithm.current_subset)
        return [
            f"Subset size: {size}/{algorithm.m}",
            f"Subsets: {algorithm.next_subset}/{len(algorithm.subsets)}",
        ]

    def legend_items(self):
        return [
            ("ring", self.accent, "Current subset"),
            ("dashed", self.accent, "Best path for subset"),
            ("line", theme.BEST_TOUR_COLOR, "Optimal tour"),
        ]
