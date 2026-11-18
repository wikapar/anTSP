import random

from algorithms.ant import Ant
from graph.graph import Graph
from graph.node import Node
from utils.helpers import euclidean_distance


class AntColony:
    def __init__(
        self,
        graph: Graph,
        number_of_ants: int,
        alpha: float,
        beta: float,
        evaporation_rate: float,
        initial_pheromone: float=1.0,
        start_node: Node=None #if None each ant will have a different starting point
    ):
        self.graph = graph
        self.number_of_ants = number_of_ants

        self.alpha = alpha
        self.beta = beta #setting it to 0 disables the distance heuristic
        self.evaporation_rate = evaporation_rate

        self.ants = []
        self.pheromones = {} #dict where tuples are indexes

        self.best_tour = None
        self.best_distance = float("inf")
        self.start_node = start_node

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
        pass

    def evaporate_pheromones(self):
        pass

    def deposit_pheromones(self):
        pass

    def update_best_tour(self):
        pass

    def step(self):
        pass

    def get_edge_key(self, node_a: Node, node_b: Node):
        return tuple(sorted((node_a.id, node_b.id)))

    def get_pheromone(self, node_a: Node, node_b: Node):
        edge = self.get_edge_key(node_a.id, node_b.id)
        return self.pheromones[edge]