import pygame
import random

from graph.graph import Graph
from display.display import Display
from graph.node import Node


def generate_random_graph(n, width, height):
    graph = Graph([])

    for i in range(n):
        x = random.randint(30, width - 30)
        y = random.randint(30, height - 30)
        graph.add_node(Node(i, x, y))

    return graph


def main():
    width = 800
    height = 600

    graph = generate_random_graph(15, width, height)

    display = Display(width, height)

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        display.draw_graph(graph)

        clock.tick(60)

    display.close()


if __name__ == "__main__":
    main()
