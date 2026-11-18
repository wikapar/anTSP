import pygame
from display.display import Display
from utils.helpers import generate_random_graph

class Simulation:
    def __init__(self, num_of_nodes: int):
        self.num_of_nodes = num_of_nodes
    
    def simulation_loop(self, width: int, height: int):
        graph = generate_random_graph(self.num_of_nodes, width, height)

        display = Display(width, height)

        running = True
        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False


            display.clear()
            display.draw_graph(graph)
            display.update()

            clock.tick(60)

        display.close()