from algorithms.algorithm import Algorithm
from graph.graph import Graph
from graph.node import Node
from utils.helpers import euclidean_distance


class Backtracking(Algorithm):
    """Inherits the abstract Algorithm class.
    Depth first search over all possible tours with backtracking.
    One step = one decision (trying a node, pruning a branch or going back one level),
    so the search can be visualized the same way as the ant colony.
    With use_pruning the branch is abandoned as soon as it is already longer than the best tour found (branch and bound).
    Without it every possible tour is checked, which is (n - 1)! tours."""
    def __init__(
        self,
        graph: Graph,
        use_pruning: bool=True,
        start_node: Node | None=None #if None the first node of the graph is the start
    ):
        self.graph = graph
        self.use_pruning = use_pruning

        nodes = self.graph.get_nodes()
        if start_node is None:
            self.start_node = nodes[0]
        else:
            if start_node not in nodes:
                raise ValueError("Starting node is not in the graph.")
            self.start_node = start_node

        self.path = [self.start_node]
        self.visited_nodes = {self.start_node.node_id}
        self.current_distance = 0.0

        self.candidates = [] #candidates[i] = nodes still to be tried after path[i]
        self.candidates.append(self.get_candidates(self.start_node))

        self.best_tour = None
        self.best_distance = float("inf")
        self.best_found_at_step = None

        self.steps = 0
        self.finished = False

    def get_candidates(self, current: Node):
        """Unvisited nodes, nearest first (a short tour is found early, so pruning works better)."""
        unvisited_nodes = [
            node for node in self.graph.get_nodes()
            if node.node_id not in self.visited_nodes
        ]

        return sorted(
            unvisited_nodes,
            key=lambda node: euclidean_distance(current, node)
        )

    def move_to(self, node: Node, distance: float):
        self.path.append(node)
        self.visited_nodes.add(node.node_id)
        self.current_distance = distance
        self.candidates.append(self.get_candidates(node))

    def backtrack(self):
        """Goes one level back. If we are back at the start node the whole search is done."""
        self.candidates.pop()

        if len(self.path) == 1:
            self.finished = True
            return

        node = self.path.pop()
        self.visited_nodes.remove(node.node_id)
        self.current_distance -= euclidean_distance(self.path[-1], node)

    def update_best_tour(self):
        """Called when the path contains all nodes. Closes the tour and compares it with the best one."""
        total_distance = self.current_distance + euclidean_distance(
            self.path[-1],
            self.start_node
        )

        if total_distance < self.best_distance:
            self.best_distance = total_distance
            self.best_tour = self.path + [self.start_node]
            self.best_found_at_step = self.steps

    def step(self):
        """Advances the algorithm by one step."""
        if self.is_finished():
            return

        self.steps += 1
        options = self.candidates[-1]

        if not options:
            self.backtrack()
            return

        next_node = options.pop(0)
        distance = self.current_distance + euclidean_distance(self.path[-1], next_node)

        if self.use_pruning and distance >= self.best_distance:
            return

        self.move_to(next_node, distance)

        if len(self.path) == self.graph.get_size():
            self.update_best_tour()

    def is_finished(self):
        return self.finished