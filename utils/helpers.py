import math
import random
from graph.graph import Graph
from graph.node import Node


def euclidean_distance(a: Node, b: Node):
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx**2 + dy**2)

def generate_random_graph(n: int, max_x: int, max_y: int, seed: int | None = None):
    rng = random.Random(seed)
    graph = Graph([])

    for i in range(n):
        x = rng.randint(30, max_x - 30)
        y = rng.randint(30, max_y - 30)
        graph.add_node(Node(i, x, y))

    return graph