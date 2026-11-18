import random

from algorithms.algorithm import Algorithm
from algorithms.ant import Ant
from graph.graph import Graph
from graph.node import Node
from utils.helpers import euclidean_distance


class AntColony(Algorithm):
    """Inherits the abstract Algorithm class.
    Implements the classic Ant System (AS) algorithm."""
    def __init__(
        self,
        graph: Graph,
        number_of_ants: int,
        alpha: float,
        beta: float,
        evaporation_rate: float,
        initial_pheromone: float=1.0,
        max_iterations: int=100,
        start_node: Node=None #if None each ant will have a different starting point
    ):
        self.graph = graph
        self.number_of_ants = number_of_ants

        self.alpha = alpha
        self.beta = beta #setting it to 0 disables the distance heuristic
        self.evaporation_rate = evaporation_rate
        self.initial_pheromone = initial_pheromone

        self.ants = []
        self.pheromones = {} #dict where tuples are indexes

        self.best_tour = None
        self.best_distance = float("inf")
        self.start_node = start_node

        self.current_iteration = 1
        self.max_iterations = max_iterations

        self.initialize_pheromones()
        self.initialize_ants()


    def initialize_pheromones(self):
        nodes = self.graph.get_nodes()

        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                edge = tuple(sorted((nodes[i].id, nodes[j].id)))
                self.pheromones[edge] = self.initial_pheromone

    def initialize_ants(self):
        nodes = self.graph.get_nodes()
        if self.start_node is None:
            starting_nodes = random.sample(nodes, self.number_of_ants)
        else:
            if self.start_node not in nodes:
                raise ValueError("Starting node is not in the graph.")
            starting_nodes = [self.start_node] * self.number_of_ants

        self.ants = [Ant(node) for node in starting_nodes]

    def choose_next_node(self, ant: Ant):
        """Choice of next node for a given ant. Can return None if no unvisited nodes are left."""
        nodes = self.graph.get_nodes()

        unvisited_nodes = [
            node for node in nodes
            if node not in ant.visited_nodes
        ]

        if not unvisited_nodes:
            return None
        
        weights = []

        weights = [
        self.calculate_weight(ant.current_node, node)
        for node in unvisited_nodes
        ]

        return random.choices(
            unvisited_nodes,
            weights=weights,
            k=1
        )[0]

    def calculate_weight(self, current: Node, candidate: Node):
        pheromone = self.get_pheromone(current, candidate)
        distance = euclidean_distance(current, candidate)
        heuristic = 1 / max(distance, 1e-10) #safeguard against 0 division

        return pheromone ** self.alpha * heuristic ** self.beta


    def move_ants(self):
        for ant in self.ants:
            if ant.finished:
                continue

            next_node = self.choose_next_node(ant)

        if next_node is None:
            ant.return_to_start()
        else:
            ant.move_to(next_node)

    def evaporate_pheromones(self):
        for edge in self.pheromones:
            self.pheromones[edge] *= (1 - self.evaporation_rate)

    #TODO: Make more modular - how about a version where ants deposit pheromones every step -> 
    # that would be closer to real ants
    def deposit_pheromones(self):
        """Ants deposit pheromones after finishing the tour based on the distance of the tour. """
        Q = 1.0
        for ant in self.ants:
            if not ant.finished:
                continue

            route_distance = self.calculate_route_distance(ant.route)

            if route_distance <= 0:
                continue

            deposit_amount = Q / route_distance

            for i in range(len(ant.route) - 1):
                node_a = ant.route[i]
                node_b = ant.route[i + 1]

                edge = self.get_edge_key(node_a, node_b)

                self.pheromones[edge] += deposit_amount

    def update_best_tour(self):
        for ant in self.ants:
            if not ant.finished:
                continue

            distance = self.calculate_route_distance(ant.route)

            if distance < self.best_distance:
                self.best_distance = distance
                self.best_tour = ant.route.copy()

    def step(self):
        """Advances the algorithm by one step. 
        If all ants finished their tour the next iteration starts - ants are reset but the pheromones are not.
        Upon new iteration the best found tour is updated.
        """
        if self.iteration_complete:
            self.initialize_ants()
            self.iteration_complete = False

        self.move_ants()

        if all(ant.finished for ant in self.ants):
            self.update_best_tour()
            self.evaporate_pheromones()
            self.deposit_pheromones()

            self.iteration_complete = True

    def calculate_route_distance(self, route):
        total_distance = 0

        for i in range(len(route) - 1):
            total_distance += euclidean_distance(
                route[i],
                route[i + 1]
            )

        return total_distance

    def get_edge_key(self, node_a: Node, node_b: Node):
        return tuple(sorted((node_a.id, node_b.id)))

    def get_pheromone(self, node_a: Node, node_b: Node):
        edge = self.get_edge_key(node_a.id, node_b.id)
        return self.pheromones[edge]

    def is_finished(self):
        return self.current_iteration >= self.max_iterations