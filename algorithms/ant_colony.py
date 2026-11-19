import math
import random
from enum import Enum

from algorithms.algorithm import Algorithm
from algorithms.ant import Ant
from graph.graph import Graph
from graph.node import Node
from utils.tsp import nearest_neighbour_tour, two_opt


class AcoVariant(str, Enum):
    ANT_SYSTEM = "as"            # classic Ant System: every ant deposits
    ELITIST = "elitist"          # + extra deposit on the best tour found so far
    MAX_MIN = "mmas"             # MAX-MIN Ant System: only the iteration best deposits, trails are bounded


class DepositMode(str, Enum):
    TOUR = "tour"   # ants deposit Q / tour_length after finishing their tour (classic)
    STEP = "step"   # ants deposit Q / edge_length immediately on every move (closer to real ants)


MMAS_P_BEST = 0.05  # probability of building the best tour once converged, sets tau_min


class AntColony(Algorithm):
    """Inherits the abstract Algorithm class.
    Ant colony optimization for the TSP with the Ant System (AS), Elitist AS and MAX-MIN AS variants.

    One step = every ant moves to its next node. When all ants finished their tour the next step
    ends the iteration: (optional 2-opt), best tour update, evaporation, deposit, new ants.
    """

    def __init__(
        self,
        graph: Graph,
        number_of_ants: int,
        alpha: float,
        beta: float,
        evaporation_rate: float,
        initial_pheromone: float | None = None,  # None = standard choice for the variant (m / C_nn)
        max_iterations: int = 100,
        start_node: Node | None = None,  # if None each ant will have a different starting point
        variant: AcoVariant | str = AcoVariant.ANT_SYSTEM,
        elitist_weight: float | None = None,  # Elitist AS: weight of the best tour (None = number of nodes)
        local_search: bool = False,  # improve every ant's tour with 2-opt
        deposit_mode: DepositMode | str = DepositMode.TOUR,
        stagnation_limit: int | None = None,  # stop after this many iterations without improvement
        q: float = 1.0,
        seed: int | None = None,
    ):
        super().__init__(graph)
        self.variant = AcoVariant(variant)
        self.deposit_mode = DepositMode(deposit_mode)
        validate_aco_parameters(number_of_ants, alpha, beta, evaporation_rate, max_iterations,
                                initial_pheromone, stagnation_limit, q)

        self.number_of_ants = number_of_ants
        self.alpha = alpha
        self.beta = beta  # setting it to 0 disables the distance heuristic
        self.evaporation_rate = evaporation_rate
        self.max_iterations = max_iterations
        self.local_search = local_search
        self.stagnation_limit = stagnation_limit
        self.q = q
        self.start_node = start_node
        if start_node is not None and start_node not in graph.get_nodes():
            raise ValueError("Starting node is not in the graph.")

        self.n = graph.get_size()
        self.elitist_weight = elitist_weight if elitist_weight is not None else self.n
        self.rng = random.Random(seed)

        self.ants: list[Ant] = []
        self.current_iteration = 0
        self.iterations_without_improvement = 0
        self.stagnated = False
        self.iteration_best_distance = math.inf

        # Nearest neighbour tour gives the scale of the problem (standard way to set tau_0)
        nn_tour, evaluations = nearest_neighbour_tour(0, self.matrix)
        self.edge_evaluations += evaluations
        self.nearest_neighbour_length = sum(self.matrix[nn_tour[i]][nn_tour[i + 1]] for i in range(self.n))

        self.tau_max = math.inf
        self.tau_min = 0.0
        if initial_pheromone is None:
            if self.variant == AcoVariant.MAX_MIN:
                initial_pheromone = 1 / (self.evaporation_rate * self.nearest_neighbour_length)
            else:
                initial_pheromone = self.number_of_ants / self.nearest_neighbour_length
        self.initial_pheromone = initial_pheromone
        if self.variant == AcoVariant.MAX_MIN:
            self.update_mmas_limits(self.nearest_neighbour_length)

        # heuristic (1/d)^beta never changes - computed once
        self.heuristic = [
            [0.0 if i == j else (1 / max(self.matrix[i][j], 1e-10)) ** self.beta for j in range(self.n)]
            for i in range(self.n)
        ]
        self.pheromones = [[initial_pheromone] * self.n for _ in range(self.n)]
        self.choice_info = [[0.0] * self.n for _ in range(self.n)]
        self.update_choice_info()

        self.initialize_ants()

    # ----- setup -----

    def initialize_ants(self):
        nodes = self.graph.get_nodes()
        if self.start_node is not None:
            starting_nodes = [self.start_node] * self.number_of_ants
        elif self.number_of_ants <= len(nodes):
            starting_nodes = self.rng.sample(nodes, self.number_of_ants)
        else:
            # more ants than nodes: every node gets ants, the rest start randomly
            starting_nodes = nodes * (self.number_of_ants // len(nodes))
            starting_nodes += self.rng.sample(nodes, self.number_of_ants % len(nodes))

        self.ants = [Ant(node) for node in starting_nodes]

    def update_choice_info(self):
        """choice_info[i][j] = tau^alpha * eta^beta, recomputed after every pheromone update."""
        for i in range(self.n):
            pheromone_row = self.pheromones[i]
            heuristic_row = self.heuristic[i]
            self.choice_info[i] = [
                (pheromone_row[j] ** self.alpha) * heuristic_row[j] for j in range(self.n)
            ]

    def update_mmas_limits(self, best_length: float):
        n = self.n
        self.tau_max = 1 / (self.evaporation_rate * best_length)
        p_root = MMAS_P_BEST ** (1 / n)
        average_choices = max(n / 2 - 1, 1)
        self.tau_min = self.tau_max * (1 - p_root) / (average_choices * p_root)

    # ----- one step -----

    def step(self):
        """Advances the algorithm by one step.
        If all ants finished their tour the next iteration starts - ants are reset but the pheromones are not.
        Upon new iteration the best found tour is updated.
        """
        if self.is_finished():
            return

        if all(ant.finished for ant in self.ants):
            self.end_iteration()
            return

        self.move_ants()

    def move_ants(self):
        for ant in self.ants:
            if ant.finished:
                continue

            previous = ant.current_node
            next_node = self.choose_next_node(ant)

            if next_node is None:
                ant.return_to_start()
            else:
                ant.move_to(next_node)

            if self.deposit_mode == DepositMode.STEP:
                self.deposit_on_edge(previous.node_id, ant.current_node.node_id,
                                     self.q / max(self.matrix[previous.node_id][ant.current_node.node_id], 1e-10))

    def choose_next_node(self, ant: Ant):
        """Choice of next node for a given ant. Can return None if no unvisited nodes are left."""
        nodes = self.graph.get_nodes()
        unvisited_nodes = [node for node in nodes if node.node_id not in ant.visited_nodes]

        if not unvisited_nodes:
            return None

        row = self.choice_info[ant.current_node.node_id]
        weights = [row[node.node_id] for node in unvisited_nodes]
        self.edge_evaluations += len(unvisited_nodes)

        if sum(weights) <= 0 or not all(math.isfinite(w) for w in weights):
            return self.rng.choice(unvisited_nodes)

        return self.rng.choices(unvisited_nodes, weights=weights, k=1)[0]

    # ----- end of iteration -----

    def end_iteration(self):
        tours = [[node.node_id for node in ant.tour] for ant in self.ants]

        if self.local_search:
            for index, tour in enumerate(tours):
                tours[index], evaluations = two_opt(tour, self.matrix)
                self.edge_evaluations += evaluations
                self.ants[index].tour = self.nodes_from_ids(tours[index])

        lengths = [self.tour_length(tour) for tour in tours]
        improved = self.update_best_tour(tours, lengths)

        self.evaporate_pheromones()
        if self.deposit_mode == DepositMode.TOUR:
            self.deposit_pheromones(tours, lengths)
        if self.variant == AcoVariant.MAX_MIN:
            self.clamp_pheromones()
        self.update_choice_info()

        self.current_iteration += 1
        self.iterations_without_improvement = 0 if improved else self.iterations_without_improvement + 1
        if self.stagnation_limit is not None and self.iterations_without_improvement >= self.stagnation_limit:
            self.stagnated = True

        if not self.is_finished():
            self.initialize_ants()

    def tour_length(self, tour_ids: list[int]) -> float:
        self.edge_evaluations += len(tour_ids) - 1
        return sum(self.matrix[tour_ids[i]][tour_ids[i + 1]] for i in range(len(tour_ids) - 1))

    def update_best_tour(self, tours, lengths) -> bool:
        best_index = min(range(len(tours)), key=lambda i: lengths[i])
        self.iteration_best_tour = tours[best_index]
        self.iteration_best_distance = lengths[best_index]

        if lengths[best_index] < self.best_distance - 1e-9:
            self.best_distance = lengths[best_index]
            self.best_tour = self.nodes_from_ids(tours[best_index])
            if self.variant == AcoVariant.MAX_MIN:
                self.update_mmas_limits(self.best_distance)
            return True
        return False

    def evaporate_pheromones(self):
        keep = 1 - self.evaporation_rate
        for row in self.pheromones:
            for j in range(self.n):
                row[j] *= keep

    def deposit_on_edge(self, a: int, b: int, amount: float):
        self.pheromones[a][b] += amount
        self.pheromones[b][a] += amount
        if self.variant == AcoVariant.MAX_MIN:
            self.pheromones[a][b] = self.pheromones[b][a] = min(self.pheromones[a][b], self.tau_max)
        for i, j in ((a, b), (b, a)):
            self.choice_info[i][j] = (self.pheromones[i][j] ** self.alpha) * self.heuristic[i][j]

    def deposit_tour(self, tour_ids: list[int], amount: float):
        for i in range(len(tour_ids) - 1):
            a, b = tour_ids[i], tour_ids[i + 1]
            self.pheromones[a][b] += amount
            self.pheromones[b][a] += amount

    def deposit_pheromones(self, tours, lengths):
        """Ants deposit pheromones after finishing the tour based on the distance of the tour."""
        if self.variant == AcoVariant.MAX_MIN:
            self.deposit_tour(self.iteration_best_tour, self.q / self.iteration_best_distance)
            return

        for tour, length in zip(tours, lengths):
            if length > 0:
                self.deposit_tour(tour, self.q / length)

        if self.variant == AcoVariant.ELITIST and self.best_tour is not None:
            best_ids = [node.node_id for node in self.best_tour]
            self.deposit_tour(best_ids, self.elitist_weight * self.q / self.best_distance)

    def clamp_pheromones(self):
        for row in self.pheromones:
            for j in range(self.n):
                row[j] = min(max(row[j], self.tau_min), self.tau_max)

    # ----- helpers for renderers -----

    def pheromone_edges(self):
        """Yields ((node_a_id, node_b_id), pheromone) for every edge once."""
        for i in range(self.n):
            row = self.pheromones[i]
            for j in range(i + 1, self.n):
                yield (i, j), row[j]

    @property
    def display_name(self) -> str:
        names = {
            AcoVariant.ANT_SYSTEM: "Ant System",
            AcoVariant.ELITIST: "Elitist Ant System",
            AcoVariant.MAX_MIN: "MAX-MIN Ant System",
        }
        name = names[self.variant]
        if self.local_search:
            name += " + 2-opt"
        return name

    def is_finished(self):
        return self.current_iteration >= self.max_iterations or self.stagnated


def validate_aco_parameters(number_of_ants, alpha, beta, evaporation_rate, max_iterations,
                            initial_pheromone=None, stagnation_limit=None, q=1.0):
    if not isinstance(number_of_ants, int) or number_of_ants < 1:
        raise ValueError("number_of_ants must be an integer >= 1")
    if alpha < 0:
        raise ValueError("alpha must be >= 0")
    if beta < 0:
        raise ValueError("beta must be >= 0")
    if not 0 < evaporation_rate <= 1:
        raise ValueError("evaporation_rate must be in (0, 1]")
    if not isinstance(max_iterations, int) or max_iterations < 1:
        raise ValueError("max_iterations must be an integer >= 1")
    if initial_pheromone is not None and initial_pheromone <= 0:
        raise ValueError("initial_pheromone must be > 0")
    if stagnation_limit is not None and stagnation_limit < 1:
        raise ValueError("stagnation_limit must be >= 1")
    if q <= 0:
        raise ValueError("q must be > 0")
