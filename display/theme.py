"""Shared visual style for every renderer, so all algorithms look the same.
Change colors, fonts and line widths here instead of inside the renderers."""
import pygame

# Surfaces
BACKGROUND = (18, 18, 17)
PANEL_BACKGROUND = (26, 26, 25)
PANEL_BORDER = (58, 58, 55)
GRID_COLOR = (48, 48, 46)
AXIS_COLOR = (90, 90, 86)

# Text
TEXT_PRIMARY = (240, 239, 236)
TEXT_SECONDARY = (195, 194, 183)
TEXT_MUTED = (135, 134, 128)

# Graph
NODE_COLOR = (225, 225, 220)
NODE_RADIUS = 5

# Elements shared by all algorithms
BEST_TOUR_COLOR = (40, 190, 110)
BEST_TOUR_WIDTH = 3
SEARCH_WIDTH = 2
AGENT_RADIUS = 6  # ants / current node of backtracking
AGENT_OUTLINE = (255, 255, 255)

# One accent color per algorithm: used for its search state AND its line in the chart
ACO_ACCENT = (217, 89, 38)          # orange
BACKTRACKING_ACCENT = (57, 135, 229)  # blue
HELD_KARP_ACCENT = (144, 133, 233)    # violet
OPTIMUM_COLOR = (195, 194, 183)

FONT_TITLE = 26
FONT_TEXT = 19
FONT_SMALL = 16

_fonts = {}


def get_font(size: int) -> pygame.font.Font:
    """Fonts are cached, creating a font every frame is slow."""
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def draw_text(surface, text, position, color=TEXT_PRIMARY, size=FONT_TEXT, anchor="topleft"):
    label = get_font(size).render(text, True, color)
    rect = label.get_rect(**{anchor: position})
    surface.blit(label, rect)
    return rect


def draw_tour(surface, nodes, color=BEST_TOUR_COLOR, width=BEST_TOUR_WIDTH):
    if not nodes or len(nodes) < 2:
        return
    points = [(node.x, node.y) for node in nodes]
    pygame.draw.lines(surface, color, False, points, width)


def draw_agent(surface, color, position, radius=AGENT_RADIUS):
    """A filled dot with a white ring - ants and the backtracking 'cursor' look the same."""
    pygame.draw.circle(surface, AGENT_OUTLINE, position, radius + 2)
    pygame.draw.circle(surface, color, position, radius)


def draw_dashed_line(surface, color, start, end, width=SEARCH_WIDTH, dash_length=8, gap_length=5):
    start_vec = pygame.math.Vector2(start)
    end_vec = pygame.math.Vector2(end)
    direction = end_vec - start_vec
    distance = direction.length()
    if distance == 0:
        return
    direction = direction.normalize()

    position = 0
    while position < distance:
        dash_end = min(position + dash_length, distance)
        pygame.draw.line(
            surface,
            color,
            start_vec + direction * position,
            start_vec + direction * dash_end,
            width
        )
        position += dash_length + gap_length


def draw_legend_symbol(surface, kind: str, color, x: int, center_y: int):
    """Draws a 18px wide legend symbol. kind: 'line', 'dashed', 'dot', 'ring' or 'fade'."""
    if kind == "line":
        pygame.draw.line(surface, color, (x, center_y), (x + 18, center_y), BEST_TOUR_WIDTH)
    elif kind == "dashed":
        draw_dashed_line(surface, color, (x, center_y), (x + 18, center_y), dash_length=5, gap_length=3)
    elif kind == "ring":
        pygame.draw.circle(surface, color, (x + 9, center_y), 7, 2)
    elif kind == "dot":
        draw_agent(surface, color, (x + 9, center_y), 5)
    elif kind == "fade":
        # weak -> strong trail
        for i, alpha in enumerate((70, 150, 255)):
            faded = tuple(int(c * alpha / 255 + PANEL_BACKGROUND[j] * (1 - alpha / 255)) for j, c in enumerate(color))
            pygame.draw.line(surface, faded, (x + i * 6, center_y), (x + i * 6 + 6, center_y), 1 + i)
    return x + 18


def format_count(value: float) -> str:
    """1234 -> 1.2k, 4500000 -> 4.5M"""
    for limit, suffix in ((1e9, "G"), (1e6, "M"), (1e3, "k")):
        if abs(value) >= limit:
            return f"{value / limit:.1f}".rstrip("0").rstrip(".") + suffix
    return f"{value:g}" if isinstance(value, float) else str(value)


def format_gap(distance: float, optimum: float) -> str:
    gap = (distance - optimum) / optimum * 100
    if gap < 0.005:
        return "optimal"
    return f"+{gap:.1f}% vs optimum"
