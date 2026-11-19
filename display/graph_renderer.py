import pygame

from graph.graph import Graph


class GraphRenderer:
    def __init__(self):
        self.font = pygame.font.SysFont(None, 20)

    def draw(self, screen: pygame.Surface, graph: Graph):
        nodes = graph.get_nodes()

        for node in nodes:
            pygame.draw.circle(
                screen,
                (240, 240, 240),
                (node.x, node.y),
                6
            )

            label = self.font.render(
                str(node.node_id),
                True,
                (255, 255, 255)
            )

            screen.blit(label, (node.x + 10, node.y - 10))