import math
from graph.node import Node


def euclidean_distance(a:Node, b:Node):
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx**2 + dy**2)