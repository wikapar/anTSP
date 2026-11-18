import pygame
import argparse

from graph.graph import Graph
from display.display import Display
from graph.node import Node
from simulation.simulation import Simulation
from utils.helpers import generate_random_graph


DEFAULT_SCREEN_WIDTH = 600
DEFAULT_SCREEN_HEIGHT = 800
NODE_NUMBER = 10


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--width', type=int, help='Select the screen width')
    parser.add_argument('-y', '--height', type=int, help='Select the screen height')
    parser.add_argument('-n', '--num-of-nodes', type=int, help='Number of nodes in the graph')
    parser.parse_args()
    args = parser.parse_args()

    if not (width := args.width):
        width = DEFAULT_SCREEN_WIDTH

    if not (height := args.height):
        height = DEFAULT_SCREEN_HEIGHT

    if not (num_of_nodes := args.num_of_nodes):
        num_of_nodes = NODE_NUMBER

    simulation = Simulation(num_of_nodes)
    simulation.simulation_loop(height, width)


if __name__ == "__main__":
    main()
