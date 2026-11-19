import math

import pygame

from application.algorithm_run import AlgorithmRun
from application.session import Session, ViewState
from display import theme

PAD_LEFT = 62
PAD_RIGHT = 20
PAD_TOP = 40
PAD_BOTTOM = 50  # x tick labels + key hints

X_LABELS = {"step": "step", "evaluations": "edge evaluations", "time": "CPU time (s)"}
KEY_HINTS = "Space pause   N step   +/- speed   X x-axis   L log scale   R new graph   Esc quit"


def nice_ticks(low: float, high: float, count: int = 5) -> list[float]:
    span = high - low
    if span <= 0:
        return [low]
    raw = span / count
    magnitude = 10 ** math.floor(math.log10(raw))
    step = next(m * magnitude for m in (1, 2, 2.5, 5, 10) if m * magnitude >= raw)
    tick = math.ceil(low / step) * step
    ticks = []
    while tick <= high + 1e-9 * max(1, abs(high)):
        ticks.append(tick)
        tick += step
    return ticks


def format_tick(value: float, mode: str) -> str:
    if mode == "time":
        if value == 0:
            return "0"
        return f"{value:.3g}s"
    return theme.format_count(round(value))


class XScale:
    """Linear or logarithmic mapping of x values to [0, 1]."""

    def __init__(self, x_max: float, log: bool):
        self.x_max = x_max
        self.log = log
        self.offset = x_max / 1e4  # so that x = 0 can be shown on a log axis

    def __call__(self, x: float) -> float:
        if not self.log:
            return x / self.x_max
        return (math.log10(x + self.offset) - math.log10(self.offset)) / (
            math.log10(self.x_max + self.offset) - math.log10(self.offset))

    def inverse(self, t: float) -> float:
        if not self.log:
            return t * self.x_max
        low = math.log10(self.offset)
        high = math.log10(self.x_max + self.offset)
        return 10 ** (low + t * (high - low)) - self.offset

    def ticks(self) -> list[float]:
        if not self.log:
            return nice_ticks(0, self.x_max, 8)
        ticks = [0.0]
        power = math.ceil(math.log10(self.offset * 10))
        while 10 ** power <= self.x_max:
            ticks.append(10 ** power)
            power += 1
        return ticks


class ChartRenderer:
    """Line chart: shortest tour length found so far, one line per algorithm.
    x can be steps, edge evaluations or CPU time (linear or log)."""

    def draw(self, surface: pygame.Surface, session: Session, view: ViewState, mouse_pos=None):
        runs = session.runs
        width, height = surface.get_size()
        surface.fill(theme.PANEL_BACKGROUND)
        pygame.draw.rect(surface, theme.PANEL_BORDER, surface.get_rect(), 1)

        mode = view.x_mode
        title = f"Shortest tour length found so far  vs.  {X_LABELS[mode]}"
        if view.log_x:
            title += " (log)"
        theme.draw_text(surface, title, (14, 12), theme.TEXT_PRIMARY, theme.FONT_TEXT + 2)
        self.draw_legend(surface, runs, width - 14, 12)
        self.draw_hints(surface, view, session)

        plot = pygame.Rect(PAD_LEFT, PAD_TOP, width - PAD_LEFT - PAD_RIGHT, height - PAD_TOP - PAD_BOTTOM)
        values = [record.best for run in runs for record in run.history]
        if not values:
            theme.draw_text(surface, "Waiting for the first complete tour...", plot.center,
                            theme.TEXT_MUTED, theme.FONT_TEXT, anchor="center")
            return

        x_max = max(run.current_x(mode) for run in runs)
        if x_max <= 0:
            x_max = 1
        scale = XScale(x_max, view.log_x)

        y_values = values + ([session.optimum] if session.optimum else [])
        y_low, y_high = min(y_values), max(y_values)
        margin = max((y_high - y_low) * 0.08, y_high * 0.02)
        y_low, y_high = y_low - margin, y_high + margin

        def to_screen(x, value):
            sx = plot.left + plot.width * scale(x)
            sy = plot.bottom - plot.height * (value - y_low) / (y_high - y_low)
            return round(sx), round(sy)

        self.draw_axes(surface, plot, scale, mode, y_low, y_high, to_screen)

        if session.optimum:
            _, y = to_screen(0, session.optimum)
            theme.draw_dashed_line(surface, theme.OPTIMUM_COLOR, (plot.left, y), (plot.right, y),
                                   width=1, dash_length=3, gap_length=4)
            theme.draw_text(surface, f"optimum {session.optimum:.1f}", (plot.right - 4, y - 3),
                            theme.TEXT_SECONDARY, theme.FONT_SMALL, anchor="bottomright")

        for run in runs:
            self.draw_series(surface, run, mode, x_max, to_screen)

        if mouse_pos is not None and plot.collidepoint(mouse_pos):
            self.draw_crosshair(surface, runs, plot, scale, mode, mouse_pos, to_screen)

    def draw_legend(self, surface, runs, right, top):
        """Right aligned: [line] Name: best value."""
        x = right
        for run in reversed(runs):
            best = f"{run.best_distance:.1f}" if run.history else "-"
            status = " (done)" if run.is_finished() else ""
            label = theme.get_font(theme.FONT_SMALL).render(f"{run.name}: {best}{status}", True,
                                                            theme.TEXT_SECONDARY)
            x -= label.get_width()
            surface.blit(label, (x, top + 3))
            x -= 24
            pygame.draw.line(surface, run.renderer.accent, (x, top + 9), (x + 18, top + 9), 3)
            x -= 18

    def draw_hints(self, surface, view: ViewState, session: Session):
        height = surface.get_height()
        speed = f"{view.speed:g} steps/frame"
        state = "PAUSED" if view.paused else "running"
        left = f"{state}  |  speed {speed}  |  graph seed {session.graph_seed}  algorithm seed {session.algorithm_seed}"
        theme.draw_text(surface, left, (14, height - 8), theme.TEXT_MUTED, theme.FONT_SMALL, anchor="bottomleft")
        theme.draw_text(surface, KEY_HINTS, (surface.get_width() - 14, height - 8), theme.TEXT_MUTED,
                        theme.FONT_SMALL, anchor="bottomright")

    def draw_axes(self, surface, plot, scale, mode, y_low, y_high, to_screen):
        for value in nice_ticks(y_low, y_high, 4):
            _, y = to_screen(0, value)
            pygame.draw.line(surface, theme.GRID_COLOR, (plot.left, y), (plot.right, y), 1)
            theme.draw_text(surface, theme.format_count(round(value)), (plot.left - 8, y), theme.TEXT_MUTED,
                            theme.FONT_SMALL, anchor="midright")

        for tick in scale.ticks():
            x, _ = to_screen(tick, y_low)
            pygame.draw.line(surface, theme.AXIS_COLOR, (x, plot.bottom), (x, plot.bottom + 4), 1)
            theme.draw_text(surface, format_tick(tick, mode), (x, plot.bottom + 7), theme.TEXT_MUTED,
                            theme.FONT_SMALL, anchor="midtop")

        pygame.draw.line(surface, theme.AXIS_COLOR, plot.bottomleft, plot.bottomright, 1)

    def draw_series(self, surface, run: AlgorithmRun, mode, x_max, to_screen):
        if not run.history:
            return

        # step function: the best value stays until the next improvement
        history = [(run.record_x(record, mode), record.best) for record in run.history]
        points = [to_screen(*history[0])]
        for (x, value), (_, previous) in zip(history[1:], history):
            points.append(to_screen(x, previous))
            points.append(to_screen(x, value))
        last_value = history[-1][1]
        current_x = run.current_x(mode)
        end = to_screen(current_x, last_value)
        points.append(end)

        if len(points) >= 2:
            pygame.draw.lines(surface, run.renderer.accent, False, points, 2)

        if run.is_finished() and current_x < x_max:
            # finished early: show its final result as a dashed line for comparison
            theme.draw_dashed_line(surface, run.renderer.accent, end, to_screen(x_max, last_value),
                                   width=1, dash_length=6, gap_length=5)

        pygame.draw.circle(surface, theme.PANEL_BACKGROUND, end, 6)
        pygame.draw.circle(surface, run.renderer.accent, end, 4)

    def draw_crosshair(self, surface, runs, plot, scale, mode, mouse_pos, to_screen):
        x_value = scale.inverse((mouse_pos[0] - plot.left) / plot.width)
        x, _ = to_screen(x_value, 0)
        pygame.draw.line(surface, theme.TEXT_MUTED, (x, plot.top), (x, plot.bottom), 1)

        lines = [(None, f"{X_LABELS[mode]}: {format_tick(x_value, mode)}")]
        for run in runs:
            reached = x_value <= run.current_x(mode) or run.is_finished()
            value = run.best_at(x_value, mode) if reached else None
            if value is not None:
                pygame.draw.circle(surface, run.renderer.accent, to_screen(x_value, value), 4)
            text = f"{run.name}: {value:.1f}" if value is not None else f"{run.name}: -"
            lines.append((run.renderer.accent, text))

        font = theme.get_font(theme.FONT_SMALL)
        box_width = max(font.size(text)[0] for _, text in lines) + 34
        box_height = len(lines) * 17 + 10
        box_x = x + 12 if x + 12 + box_width < plot.right else x - 12 - box_width
        box = pygame.Rect(box_x, plot.top + 6, box_width, box_height)
        pygame.draw.rect(surface, theme.BACKGROUND, box, border_radius=4)
        pygame.draw.rect(surface, theme.PANEL_BORDER, box, 1, border_radius=4)
        for i, (color, text) in enumerate(lines):
            row_y = box.top + 6 + i * 17
            if color is not None:
                pygame.draw.line(surface, color, (box.left + 8, row_y + 6), (box.left + 20, row_y + 6), 3)
            theme.draw_text(surface, text, (box.left + 26 if color else box.left + 8, row_y),
                            theme.TEXT_PRIMARY if color else theme.TEXT_MUTED, theme.FONT_SMALL)
