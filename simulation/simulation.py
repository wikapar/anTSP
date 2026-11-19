from algorithms.algorithm import Algorithm
from graph.graph import Graph

class Simulation:
    def __init__(self, graph: Graph, algorithm: Algorithm):
        self.algorithm = algorithm
        self.graph = graph
        

    def step(self):
        self.algorithm.step()
