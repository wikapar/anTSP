from display.display import Display
from utils.helpers import generate_random_graph

class Simulation:
    def __init__(self, num_of_nodes: int, max_x: int, max_y: int):
        self.num_of_nodes = num_of_nodes
        self.graph = generate_random_graph(self.num_of_nodes, max_x, max_y)

    def step(self):
        pass
    