import pygame

from graph.graph import Graph
from display import theme


class GraphRenderer:
    def draw(self, screen: pygame.Surface, graph: Graph):
        for node in graph.get_nodes():
            pygame.draw.circle(screen, theme.NODE_COLOR, (node.x, node.y), theme.NODE_RADIUS)
            theme.draw_text(
                screen,
                str(node.node_id),
                (node.x + 9, node.y - 9),
                theme.TEXT_MUTED,
                theme.FONT_SMALL,
                anchor="bottomleft"
            )
