from graph.node import Node

class Ant:
    def __init__(self, start_node: Node):
        self.start_node = start_node
        self.current_node = start_node

        self.visited_nodes = {start_node.node_id}
        self.tour = [start_node]

        self.finished = False

    def move_to(self, node: Node):
        if node.node_id in self.visited_nodes:
            raise ValueError("Ant cannot visit a node twice")

        self.current_node = node
        self.visited_nodes.add(node.node_id)
        self.tour.append(node)

    def return_to_start(self):
        self.current_node = self.start_node
        self.tour.append(self.start_node)
        self.finished = True
