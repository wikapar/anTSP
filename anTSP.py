import argparse

from algorithms.algorithm_factory import create_algorithm_components
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


#TODO delete Simulatin class - its useless now and algorithm class can be used instead
#TODO add color dscriptons for ant renderer
#TODO the factory should probably take in an enum instead of a string
#TODO rn simulation steps per frame is int, but maybe we should be able to set that there is 0.5 frame per second
#TODO maybe add option to step through the simulation step by step?
#TODO maybe display the iteration on screen somewhere?
#TODO implement backtracking
#TODO run experiments with different seeds, different parameters, take avergaes, std etc, -> make pretty plots
#TODO update readmes

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

    algorithm_type = "ant_colony"

    algorithm_config = {
        "number_of_ants": 5,
        "alpha": 0.2,
        "beta": 0.2,
        "evaporation_rate": 0.5,
        "max_iterations": 100
    }

    algorithm, renderer = create_algorithm_components(
        algorithm_type,
        graph,
        algorithm_config
    )

    simulation = Simulation(graph, algorithm)
    display = Display(width, height, renderer)
    application = Application(simulation, display, fps, steps_per_frame)
    application.run()

if __name__ == "__main__":
    main()
