import pygame
import argparse

from graph.graph import Graph
from display.display import Display
from graph.node import Node
from utils.helpers import generate_random_graph


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


        display.clear()
        display.draw_graph(graph)
        display.update()

        clock.tick(60)

    display.close()


if __name__ == "__main__":
    main()
