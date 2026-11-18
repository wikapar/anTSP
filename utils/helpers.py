import math
import random
from graph.graph import Graph
from graph.node import Node


def euclidean_distance(a: Node, b: Node):
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx**2 + dy**2)

def generate_random_graph(n: int, maxWidth: int, maxHeight: int):
    graph = Graph([])

    for i in range(n):
        x = random.randint(30, maxWidth - 30)
        y = random.randint(30, maxHeight - 30)
        graph.add_node(Node(i, x, y))

    return graph