
import pygame

from algorithms.backtracking import Backtracking
from display.algorithm_renderer import AlgorithmRenderer


class BacktrackingRenderer(AlgorithmRenderer):
    def __init__(self):
        self.node_radius = 8
        self.font = None  # Created on first draw

        # Colors
        self.best_tour_color = (224, 68, 184)      # Magenta
        self.current_path_color = (0, 217, 232)    # Cyan
        self.current_node_color = (255, 70, 70)    # Red
        self.outline_color = (255, 255, 255)       # White

    def draw(self, screen: pygame.Surface, algorithm: Backtracking):
        self.draw_best_tour(screen, algorithm)
        self.draw_current_path(screen, algorithm)
        self.draw_current_node(screen, algorithm)
        self.draw_info(screen, algorithm)
        self.draw_legend(screen)

    def draw_best_tour(self, screen: pygame.Surface, backtracking: Backtracking):
        if backtracking.best_tour is None:
            return

        points = [
            (node.x, node.y)
            for node in backtracking.best_tour
        ]

        # Thick, solid magenta line
        pygame.draw.lines(
            screen,
            self.best_tour_color,
            False,
            points,
            6
        )

    def draw_dashed_line(
        self,
        screen: pygame.Surface,
        color,
        start,
        end,
        width=3,
        dash_length=7,
        gap_length=5,
        offset=5
    ):
        start_vec = pygame.math.Vector2(start)
        end_vec = pygame.math.Vector2(end)

        direction = end_vec - start_vec
        distance = direction.length()

        if distance == 0:
            return

        direction = direction.normalize()

        # Calculate perpendicular offset
        perpendicular = pygame.math.Vector2(
            -direction.y,
            direction.x
        )

        shift = perpendicular * offset

        start_vec += shift
        end_vec += shift

        position = 0

        while position < distance:
            dash_end = min(position + dash_length, distance)

            p1 = start_vec + direction * position
            p2 = start_vec + direction * dash_end

            pygame.draw.line(
                screen,
                color,
                p1,
                p2,
                width
            )

            position += dash_length + gap_length

    def draw_current_path(self, screen: pygame.Surface, backtracking: Backtracking):
        if len(backtracking.path) < 2:
            return

        for i in range(len(backtracking.path) - 1):
            start = (
                backtracking.path[i].x,
                backtracking.path[i].y
            )

            end = (
                backtracking.path[i + 1].x,
                backtracking.path[i + 1].y
            )

            # Dashed cyan line, slightly offset
            self.draw_dashed_line(
                screen,
                self.current_path_color,
                start,
                end,
                width=3,
                dash_length=7,
                gap_length=5,
                offset=5
            )

    def draw_current_node(self, screen: pygame.Surface, backtracking: Backtracking):
        if not backtracking.path:
            return

        node = backtracking.path[-1]
        position = (node.x, node.y)

        # White outline
        pygame.draw.circle(
            screen,
            self.outline_color,
            position,
            self.node_radius + 3
        )

        # Red center
        pygame.draw.circle(
            screen,
            self.current_node_color,
            position,
            self.node_radius
        )

    def draw_info(self, screen: pygame.Surface, backtracking: Backtracking):
        if self.font is None:
            self.font = pygame.font.SysFont(None, 20)

        if backtracking.best_tour is None:
            best = "-"
            found_at = "-"
        else:
            best = f"{backtracking.best_distance:.2f}"
            found_at = str(backtracking.best_found_at_step)

        status = "finished" if backtracking.is_finished() else "running"

        lines = [
            f"Backtracking ({status})",
            f"Steps: {backtracking.steps}",
            f"Current path: {backtracking.current_distance:.2f}",
            f"Best distance: {best} (found at step {found_at})",
        ]

        for i, line in enumerate(lines):
            label = self.font.render(
                line,
                True,
                (255, 255, 255)
            )
            screen.blit(label, (10, 10 + i * 18))

    def draw_legend(self, screen: pygame.Surface):
        if self.font is None:
            self.font = pygame.font.SysFont(None, 20)

        entries = [
            (self.best_tour_color, "Best complete tour (solid)"),
            (self.current_path_color, "Current path (dashed)"),
            (self.current_node_color, "Current node"),
        ]

        x = 10
        y = screen.get_height() - 20 * len(entries) - 10

        for i, (color, text) in enumerate(entries):
            row_y = y + i * 20

            if i == 0:
                # Thick solid line
                pygame.draw.line(
                    screen,
                    color,
                    (x, row_y + 8),
                    (x + 16, row_y + 8),
                    6
                )

            elif i == 1:
                # Dashed line
                pygame.draw.line(
                    screen,
                    color,
                    (x, row_y + 8),
                    (x + 5, row_y + 8),
                    3
                )
                pygame.draw.line(
                    screen,
                    color,
                    (x + 10, row_y + 8),
                    (x + 15, row_y + 8),
                    3
                )

            else:
                # Red circle
                pygame.draw.circle(
                    screen,
                    color,
                    (x + 7, row_y + 8),
                    6
                )

            label = self.font.render(
                text,
                True,
                (255, 255, 255)
            )
            screen.blit(label, (x + 22, row_y))
