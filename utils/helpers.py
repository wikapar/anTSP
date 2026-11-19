import math
import random

from graph.graph import Graph
from graph.node import Node

GRAPH_MARGIN = 30


def euclidean_distance(a: Node, b: Node):
    return math.hypot(a.x - b.x, a.y - b.y)


def generate_random_graph(n: int, max_x: int, max_y: int, rng: random.Random | None = None,
                          min_spacing: float = 12):
    """Random nodes inside [margin, max - margin]. Two nodes never share a position and are
    at least `min_spacing` apart when there is room for it (so they don't overlap on screen).
    Pass an rng (random.Random(seed)) to get the same graph again."""
    rng = rng or random.Random()
    if n < 1:
        raise ValueError("The graph needs at least one node.")
    if max_x <= 2 * GRAPH_MARGIN or max_y <= 2 * GRAPH_MARGIN:
        raise ValueError(f"Area {max_x}x{max_y} is too small for a graph.")

    graph = Graph([])
    positions = []
    attempts = 0
    while len(positions) < n:
        x = rng.randint(GRAPH_MARGIN, max_x - GRAPH_MARGIN)
        y = rng.randint(GRAPH_MARGIN, max_y - GRAPH_MARGIN)
        attempts += 1
        spacing = min_spacing if attempts < 200 * n else 1  # give up spacing on very crowded areas
        if all(math.hypot(x - px, y - py) >= spacing for px, py in positions):
            positions.append((x, y))

    for i, (x, y) in enumerate(positions):
        graph.add_node(Node(i, x, y))

    return graph


def new_seed() -> int:
    """A fresh random seed that can be printed and saved to reproduce a run."""
    return random.SystemRandom().randrange(0, 2**31)
