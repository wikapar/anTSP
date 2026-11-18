import pygame

from graph.graph import Graph


class Display:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("TSP Visualizer")

        self.font = pygame.font.SysFont(None, 20)

    def draw_graph(self, graph: Graph):
        self.screen.fill((25, 25, 25))

        nodes = graph.get_nodes()

        # Draw edges
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                a = nodes[i]
                b = nodes[j]

                pygame.draw.line(
                    self.screen,
                    (70, 70, 70),
                    (a.x, a.y),
                    (b.x, b.y),
                    1
                )

        # Draw nodes
        for node in nodes:
            pygame.draw.circle(
                self.screen,
                (240, 240, 240),
                (node.x, node.y),
                6
            )

            label = self.font.render(str(node.id), True, (255, 255, 255))

            self.screen.blit(
                label,
                (node.x + 10, node.y - 10)
            )

        pygame.display.flip()

    def close(self):
        pygame.quit()