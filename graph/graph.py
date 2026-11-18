from typing import List
from node import Node


class Graph:
    def __init__(self, nodes: List[Node]):
        self.nodes = nodes

    def add_node(self, node: Node):
        self.nodes.append(node)

    def get_size(self):
        return len(self.nodes)

    def get_nodes(self):
        return self.nodes