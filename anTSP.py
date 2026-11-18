import argparse

from application.application import Application
from graph.graph import Graph
from display.display import Display
from graph.node import Node
from simulation.simulation import Simulation
from utils.helpers import generate_random_graph


DEFAULT_SCREEN_WIDTH = 800
DEFAULT_SCREEN_HEIGHT = 600
NODE_NUMBER = 10
FPS = 30
STEPS_PER_FRAME = 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--width', type=int, help='Select the screen width')
    parser.add_argument('-y', '--height', type=int, help='Select the screen height')
    parser.add_argument('-n', '--num-of-nodes', type=int, help='Number of nodes in the graph')
    parser.add_argument('-f', '--fps', type=int, help='FPS of the display')
    parser.add_argument('-s', '--steps-per-frame', type=int, help='Number of steps per one frame of display')
    parser.parse_args()
    args = parser.parse_args()

    if not (width := args.width):
        width = DEFAULT_SCREEN_WIDTH

    if not (height := args.height):
        height = DEFAULT_SCREEN_HEIGHT

    if not (num_of_nodes := args.num_of_nodes):
        num_of_nodes = NODE_NUMBER

    if not (fps := args.fps):
            fps = FPS

    if not (steps_per_frame := args.steps_per_frame):
                steps_per_frame = STEPS_PER_FRAME

    simulation = Simulation(num_of_nodes, width, height)
    application = Application(simulation, width, height, fps, steps_per_frame)
    application.run()

if __name__ == "__main__":
    main()
