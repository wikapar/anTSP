import math
from typing import List

from graph.node import Node


class Graph:
    """Complete euclidean graph. Node ids must be 0..n-1 (they are used as matrix indexes).
    Distances are computed once and stored in a matrix that all algorithms share."""

    def __init__(self, nodes: List[Node]):
        self.nodes = nodes
        self._matrix = None

    def add_node(self, node: Node):
        self.nodes.append(node)
        self._matrix = None

    def get_size(self):
        return len(self.nodes)

    def get_nodes(self):
        return self.nodes

    @property
    def distance_matrix(self) -> list[list[float]]:
        if self._matrix is None:
            for index, node in enumerate(self.nodes):
                if node.node_id != index:
                    raise ValueError("Node ids must be 0..n-1 in the order of the nodes.")
            self._matrix = [
                [math.hypot(a.x - b.x, a.y - b.y) for b in self.nodes]
                for a in self.nodes
            ]
        return self._matrix

    def distance(self, a: Node, b: Node) -> float:
        return self.distance_matrix[a.node_id][b.node_id]

    def to_dict(self) -> dict:
        return {"nodes": [[node.node_id, node.x, node.y] for node in self.nodes]}

    @staticmethod
    def from_dict(data: dict) -> "Graph":
        return Graph([Node(node_id, x, y) for node_id, x, y in data["nodes"]])
