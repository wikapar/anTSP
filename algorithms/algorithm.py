import math
import time
from abc import ABC, abstractmethod

from graph.graph import Graph
from graph.node import Node


class Algorithm(ABC):
    """Common interface of all TSP algorithms.

    Every algorithm works step by step (so it can be visualized) and provides:
    - graph, best_tour (closed list of nodes or None), best_distance (inf if no tour yet)
    - edge_evaluations: how many times it looked at the length of an edge.
      This is the machine independent measure of work used to compare the algorithms
      (a 'step' means very different amounts of work in each algorithm).
    """

    def __init__(self, graph: Graph):
        if graph.get_size() < 3:
            raise ValueError("A TSP instance needs at least 3 nodes.")
        self.graph = graph
        self.matrix = graph.distance_matrix
        self.best_tour: list[Node] | None = None
        self.best_distance: float = math.inf
        self.edge_evaluations = 0

    @abstractmethod
    def step(self):
        pass

    @abstractmethod
    def is_finished(self) -> bool:
        pass

    def distance(self, a: Node, b: Node) -> float:
        self.edge_evaluations += 1
        return self.matrix[a.node_id][b.node_id]

    def nodes_from_ids(self, ids: list[int]) -> list[Node]:
        nodes = self.graph.get_nodes()
        return [nodes[i] for i in ids]

    def solve(self, time_limit: float | None = None) -> bool:
        """Runs until finished (or until the time limit in seconds). Returns True if finished."""
        start = time.perf_counter()
        while not self.is_finished():
            for _ in range(1000):
                self.step()
                if self.is_finished():
                    return True
            if time_limit is not None and time.perf_counter() - start > time_limit:
                return False
        return True
