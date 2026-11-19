import pygame

from graph.graph import Graph


class GraphRenderer:
    def __init__(self):
        self.font = pygame.font.SysFont(None, 20)

    def draw(self, screen: pygame.Surface, graph: Graph):
        nodes = graph.get_nodes()

        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                a = nodes[i]
                b = nodes[j]

                pygame.draw.line(
                    screen,
                    (70, 70, 70),
                    (a.x, a.y),
                    (b.x, b.y),
                    1
                )

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