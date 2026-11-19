import pygame

from application.algorithm_run import AlgorithmRun
from display import theme
from display.chart_renderer import ChartRenderer
from display.graph_renderer import GraphRenderer

MARGIN = 12
GAP = 12
HEADER_HEIGHT = 104
CHART_HEIGHT = 230


class Layout:
    """Splits the window into one panel per algorithm (side by side) and a chart at the bottom.
    Every panel = header (text) + graph area. All graph areas have the same size,
    so the same graph can be shown in every panel."""

    def __init__(self, width: int, height: int, num_panels: int, show_chart: bool = True):
        self.width = width
        self.height = height

        if show_chart:
            self.chart = pygame.Rect(MARGIN, height - MARGIN - CHART_HEIGHT, width - 2 * MARGIN, CHART_HEIGHT)
            panels_bottom = self.chart.top - GAP
        else:
            self.chart = None
            panels_bottom = height - MARGIN

        panel_width = (width - 2 * MARGIN - GAP * (num_panels - 1)) // num_panels
        panel_height = panels_bottom - MARGIN

        self.panels = []
        self.headers = []
        self.graph_areas = []
        for i in range(num_panels):
            panel = pygame.Rect(MARGIN + i * (panel_width + GAP), MARGIN, panel_width, panel_height)
            self.panels.append(panel)
            self.headers.append(pygame.Rect(panel.left, panel.top, panel.width, HEADER_HEIGHT))
            self.graph_areas.append(pygame.Rect(panel.left, panel.top + HEADER_HEIGHT,
                                                panel.width, panel.height - HEADER_HEIGHT))

        if panel_width < 200 or self.graph_areas[0].height < 150:
            raise ValueError(f"Window {width}x{height} is too small for {num_panels} panel(s).")

    @property
    def graph_size(self) -> tuple[int, int]:
        """Size of the area where the graph is drawn - use it to generate the graph."""
        return self.graph_areas[0].size


class Display:
    def __init__(self, layout: Layout):
        self.layout = layout

        pygame.init()
        self.screen = pygame.display.set_mode((layout.width, layout.height))
        pygame.display.set_caption("TSP Visualizer")

        # subsurfaces share pixels with the screen, so renderers can use graph coordinates directly
        self.graph_surfaces = [self.screen.subsurface(rect) for rect in layout.graph_areas]
        self.header_surfaces = [self.screen.subsurface(rect) for rect in layout.headers]
        self.chart_surface = self.screen.subsurface(layout.chart) if layout.chart else None

        self.graph_renderer = GraphRenderer()
        self.chart_renderer = ChartRenderer()

    def draw(self, runs: list[AlgorithmRun], paused: bool = False):
        self.screen.fill(theme.BACKGROUND)

        for run, header, graph_surface, panel in zip(runs, self.header_surfaces,
                                                     self.graph_surfaces, self.layout.panels):
            pygame.draw.rect(self.screen, theme.PANEL_BACKGROUND, panel)
            self.draw_header(header, run)

            run.renderer.draw(graph_surface, run.algorithm)
            self.graph_renderer.draw(graph_surface, run.algorithm.graph)
            run.renderer.draw_agents(graph_surface, run.algorithm)

            pygame.draw.rect(self.screen, theme.PANEL_BORDER, panel, 1)

        if self.chart_surface is not None:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            local_mouse = (mouse_x - self.layout.chart.left, mouse_y - self.layout.chart.top)
            self.chart_renderer.draw(self.chart_surface, runs, local_mouse, paused)

        pygame.display.flip()

    def draw_header(self, surface: pygame.Surface, run: AlgorithmRun):
        """Same header for every algorithm: title + status, shared stats, own stats, legend."""
        width = surface.get_width()
        accent = run.renderer.accent

        pygame.draw.rect(surface, accent, (14, 14, 4, 18))
        theme.draw_text(surface, run.name, (26, 14), theme.TEXT_PRIMARY, theme.FONT_TITLE)

        status = "finished" if run.algorithm.is_finished() else "running"
        status_color = theme.BEST_TOUR_COLOR if run.algorithm.is_finished() else theme.TEXT_SECONDARY
        theme.draw_text(surface, status, (width - 14, 16), status_color, theme.FONT_TEXT, anchor="topright")

        if run.history:
            best = f"{run.best_distance:.1f} (at step {run.best_found_at_step})"
        else:
            best = "-"
        theme.draw_text(surface, f"Steps: {run.steps}     Best tour: {best}", (14, 40), theme.TEXT_PRIMARY)
        theme.draw_text(surface, "     ".join(run.renderer.info_lines(run.algorithm)), (14, 60),
                        theme.TEXT_SECONDARY)

        x = 14
        legend_y = 88
        for kind, color, label in run.renderer.legend_items():
            x = theme.draw_legend_symbol(surface, kind, color, x, legend_y)
            rect = theme.draw_text(surface, label, (x + 6, legend_y), theme.TEXT_SECONDARY,
                                   theme.FONT_SMALL, anchor="midleft")
            x = rect.right + 18

        pygame.draw.line(surface, theme.PANEL_BORDER, (0, surface.get_height() - 1),
                         (width, surface.get_height() - 1), 1)

    def close(self):
        pygame.quit()
