import math
from array import array

from algorithms.algorithm import Algorithm
from graph.graph import Graph

MAX_HELD_KARP_NODES = 22  # 2^21 subsets, more does not fit into memory / time


class HeldKarp(Algorithm):
    """Exact dynamic programming algorithm (Held-Karp), O(n^2 * 2^n) time.

    cost[S][j] = length of the shortest path that starts at the start node, visits exactly the
    nodes in subset S and ends in j (j in S). Subsets are processed from small to large.
    One step = one subset S. The tour is only known at the very end.
    """

    def __init__(self, graph: Graph):
        super().__init__(graph)
        n = graph.get_size()
        if n > MAX_HELD_KARP_NODES:
            raise ValueError(f"Held-Karp needs too much memory for more than {MAX_HELD_KARP_NODES} nodes.")

        self.start_id = 0
        self.others = list(range(1, n))  # bit i of a subset = node others[i]
        self.m = len(self.others)
        full = (1 << self.m) - 1

        self.subsets = sorted(range(1, full + 1), key=lambda mask: (bin(mask).count("1"), mask))
        self.next_subset = 0
        self.current_subset = 0

        self.cost: list = [None] * (full + 1)
        self.parent: list = [None] * (full + 1)
        self.steps = 0
        self.finished = False

    def subset_size(self, mask: int) -> int:
        return bin(mask).count("1")

    def step(self):
        if self.finished:
            return
        self.steps += 1

        if self.next_subset == len(self.subsets):
            self.close_tour()
            return

        mask = self.subsets[self.next_subset]
        self.next_subset += 1
        self.current_subset = mask
        members = [i for i in range(self.m) if mask >> i & 1]
        cost = array("d", [math.inf]) * self.m
        parent = array("b", [-1]) * self.m
        matrix = self.matrix

        if len(members) == 1:
            j = members[0]
            cost[j] = matrix[self.start_id][self.others[j]]
            self.edge_evaluations += 1
        else:
            for j in members:
                previous_mask = mask ^ (1 << j)
                previous_cost = self.cost[previous_mask]
                node_j = self.others[j]
                best, best_k = math.inf, -1
                for k in members:
                    if k == j:
                        continue
                    value = previous_cost[k] + matrix[self.others[k]][node_j]
                    if value < best:
                        best, best_k = value, k
                cost[j] = best
                parent[j] = best_k
            self.edge_evaluations += len(members) * (len(members) - 1)

        self.cost[mask] = cost
        self.parent[mask] = parent

    def close_tour(self):
        full = (1 << self.m) - 1
        cost = self.cost[full]
        best, last = math.inf, -1
        for j in range(self.m):
            value = cost[j] + self.matrix[self.others[j]][self.start_id]
            if value < best:
                best, last = value, j
        self.edge_evaluations += self.m

        self.best_distance = best
        self.best_tour = self.nodes_from_ids([self.start_id] + self.path_ids(full, last) + [self.start_id])
        self.finished = True
        self.cost = None  # free the memory
        self.parent = None

    def path_ids(self, mask: int, last: int) -> list[int]:
        """Reconstructs the best path for subset `mask` ending in `last` (without the start node)."""
        ids = []
        while last != -1:
            ids.append(self.others[last])
            previous = self.parent[mask][last]
            mask ^= 1 << last
            last = previous
        return ids[::-1]

    def current_best_path(self) -> list[int]:
        """Best known partial path for the current subset (for visualization)."""
        mask = self.current_subset
        if self.finished or mask == 0:
            return []
        cost = self.cost[mask]
        last = min((j for j in range(self.m) if mask >> j & 1), key=lambda j: cost[j])
        return [self.start_id] + self.path_ids(mask, last)

    def current_subset_ids(self) -> list[int]:
        return [self.others[i] for i in range(self.m) if self.current_subset >> i & 1]

    @property
    def display_name(self) -> str:
        return "Held-Karp (DP)"

    def is_finished(self):
        return self.finished
