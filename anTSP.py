import argparse

from application.application import Application
from simulation.simulation import Simulation
from algorithms.ant_colony import AntColony
from utils.helpers import generate_random_graph
from display.display import Display
from display.ant_colony_renderer import AntColonyRenderer


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

    graph = generate_random_graph(num_of_nodes, width, height) #TODO generating should take in a seed so we can objectively compare runs
    algorithm = AntColony(graph, number_of_ants=5, alpha=0.2, beta=0.2, evaporation_rate=0.5)
    simulation = Simulation(graph, algorithm)
    display = Display(width, height, AntColonyRenderer())
    application = Application(simulation, display, fps, steps_per_frame)
    application.run()

if __name__ == "__main__":
    main()
