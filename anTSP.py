import pygame
import argparse

from graph.graph import Graph
from display.display import Display
from graph.node import Node
from simulation.simulation import Simulation
from utils.helpers import generate_random_graph


DEFAULT_SCREEN_WIDTH = 800
DEFAULT_SCREEN_HEIGHT = 600


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--width', type=int, help='Select screen the width')
    parser.add_argument('h', '--height', type=int, help='Select screen the height')
    parser.parse_args()
    args = parser.parse_args()

    if not (width := args.width):
        width = DEFAULT_SCREEN_WIDTH

    if not (height := args.height):
        height = DEFAULT_SCREEN_HEIGHT

    simulation = Simulation()
    simulation.simulation_loop(height, width)

    


if __name__ == "__main__":
    main()
