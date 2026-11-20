from enum import Enum

from algorithms.algorithm import Algorithm
from graph.graph import Graph
from graph.node import Node
from utils.tsp import mst_length, nearest_neighbour_tour


class Bound(str, Enum):
    NONE = "none"      # no pruning: every tour is checked, (n - 1)! tours
    SIMPLE = "simple"  # prune when the current path is already longer than the best tour
    MST = "mst"        # prune when path + MST of the rest (lower bound of the remaining path) is too long


class Backtracking(Algorithm):
    """Inherits the abstract Algorithm class.
    Depth first search over all possible tours with backtracking (branch and bound).
    One step = one decision (trying a node, pruning a branch or going back one level),
    so the search can be visualized the same way as the ant colony.

    Improvements (all optional, to be able to compare them):
    - bound: how branches are pruned (see Bound).
    - break_symmetry: a tour and its reverse have the same length, so only the direction where
      the 2nd node has a smaller id than the last node is searched -> half the tours.
    - initial_tour: start with a known tour as the best one, so pruning works from the start.
      "nn" = nearest neighbour tour, or a closed list of nodes (e.g. the result of ACO).
    The result is always the optimal tour (if the search finishes).
    """

    def __init__(
        self,
        graph: Graph,
        bound: Bound | str = Bound.MST,
        break_symmetry: bool = True,
        initial_tour: str | list[Node] | None = None,
        start_node: Node | None = None,  # if None the first node of the graph is the start
        use_pruning: bool | None = None,  # old parameter: False = Bound.NONE
    ):
        super().__init__(graph)
        self.bound = Bound.NONE if use_pruning is False else Bound(bound)
        self.break_symmetry = break_symmetry

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
        self.edge_stack = []  # length of every edge on the path, to go back without recomputing

        self.candidates = []  # candidates[i] = nodes still to be tried after path[i]
        self.candidates.append(self.get_candidates(self.start_node))

        self.best_found_at_step = None
        self.steps = 0
        self.pruned = 0
        self.complete_tours = 0
        self.finished = False

        self.set_initial_tour(initial_tour)

    @property
    def use_pruning(self) -> bool:
        return self.bound != Bound.NONE

    def set_initial_tour(self, initial_tour):
        if initial_tour is None:
            return
        if isinstance(initial_tour, str):
            if initial_tour != "nn":
                raise ValueError("initial_tour must be 'nn', a list of nodes or None")
            ids, evaluations = nearest_neighbour_tour(self.start_node.node_id, self.matrix)
            self.edge_evaluations += evaluations
        else:
            ids = [node.node_id for node in initial_tour]
            if ids[0] != ids[-1] or sorted(ids[:-1]) != list(range(self.graph.get_size())):
                raise ValueError("initial_tour must be a closed tour visiting every node once")
        self.best_tour = self.nodes_from_ids(ids)
        self.best_distance = sum(self.matrix[ids[i]][ids[i + 1]] for i in range(len(ids) - 1))
        self.best_found_at_step = 0

    def get_candidates(self, current: Node):
        """Unvisited nodes, nearest first (a short tour is found early, so pruning works better)."""
        unvisited_nodes = [
            node for node in self.graph.get_nodes()
            if node.node_id not in self.visited_nodes
        ]
        row = self.matrix[current.node_id]
        self.edge_evaluations += len(unvisited_nodes)
        return sorted(unvisited_nodes, key=lambda node: row[node.node_id])

    def move_to(self, node: Node, edge: float):
        self.path.append(node)
        self.visited_nodes.add(node.node_id)
        self.edge_stack.append(edge)
        self.current_distance += edge
        self.candidates.append(self.get_candidates(node))

    def backtrack(self):
        """Goes one level back. If we are back at the start node the whole search is done."""
        self.candidates.pop()

        if len(self.path) == 1:
            self.finished = True
            return

        node = self.path.pop()
        self.visited_nodes.remove(node.node_id)
        self.current_distance -= self.edge_stack.pop()

    def violates_symmetry(self, next_node: Node, remaining: list[int]) -> bool:
        """Only tours where id(2nd node) < id(last node) are searched."""
        if not self.break_symmetry:
            return False
        second_id = self.path[1].node_id if len(self.path) >= 2 else next_node.node_id
        if remaining:
            # some node after this one must be the last node and have a bigger id than the 2nd one
            return max(remaining) < second_id
        return len(self.path) >= 2 and next_node.node_id < second_id

    def can_prune(self, next_node: Node, distance: float, remaining: list[int]) -> bool:
        if self.bound == Bound.NONE:
            return False
        if self.bound == Bound.SIMPLE or not remaining:
            return distance >= self.best_distance
        # The rest of the tour is a path next_node -> remaining nodes -> start,
        # every such path is a spanning tree of these nodes, so it is at least as long as the MST.
        lower_bound, evaluations = mst_length([next_node.node_id] + remaining + [self.start_node.node_id],
                                              self.matrix)
        self.edge_evaluations += evaluations
        return distance + lower_bound >= self.best_distance - 1e-9

    def update_best_tour(self):
        """Called when the path contains all nodes. Closes the tour and compares it with the best one."""
        self.complete_tours += 1
        total_distance = self.current_distance + self.distance(self.path[-1], self.start_node)

        if total_distance < self.best_distance - 1e-9:
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
        edge = self.distance(self.path[-1], next_node)
        distance = self.current_distance + edge
        remaining = [node_id for node_id in range(self.graph.get_size())
                     if node_id not in self.visited_nodes and node_id != next_node.node_id]

        if self.violates_symmetry(next_node, remaining) or self.can_prune(next_node, distance, remaining):
            self.pruned += 1
            return

        self.move_to(next_node, edge)

        if len(self.path) == self.graph.get_size():
            self.update_best_tour()

    @property
    def display_name(self) -> str:
        names = {Bound.NONE: "Backtracking (no pruning)", Bound.SIMPLE: "Backtracking (simple bound)",
                 Bound.MST: "Backtracking (MST bound)"}
        return names[self.bound]

    def is_finished(self):
        return self.finished
