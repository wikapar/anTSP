import argparse
import random

from algorithms.algorithm_factory import create_algorithm_components, AgorithmType
from application.algorithm_run import AlgorithmRun
from application.application import Application
from utils.helpers import generate_random_graph
from display.display import Display, Layout


PANEL_WIDTH = 640  # default window width = PANEL_WIDTH * number of algorithms
DEFAULT_SCREEN_HEIGHT = 820
NODE_NUMBER = 10
FPS = 30
STEPS_PER_FRAME = 1
DEFAULT_ALGORITHM = "compare"

ALGORITHM_TYPES = {
    "aco": [AgorithmType.ANT_COLONY],
    "backtracking": [AgorithmType.BACKTRACKING],
    "compare": [AgorithmType.ANT_COLONY, AgorithmType.BACKTRACKING],
}


#TODO Parameter for seed for graph and for ants!!!!
#TODO rn simulation steps per frame is int, but maybe we should be able to set that there is 0.5 frame per second
#TODO maybe add option to step through the simulation step by step?
#TODO run experiments with different seeds, different parameters, take avergaes, std etc, -> make pretty plots
#TODO update readmes
#TODO We're not validating parameters anywhere (eg is alpha, beta in a good range, is framerate not negative etc.)

def print_result(run: AlgorithmRun):
    """Prints the best tour found so it can be compared between the algorithms."""
    algorithm = run.algorithm
    status = "finished" if algorithm.is_finished() else "stopped before finishing"
    print(f"Algorithm: {run.name} ({status}, {run.steps} steps)")

    if algorithm.best_tour is None:
        print("No complete tour found.")
        return

    print(f"Best distance: {algorithm.best_distance:.2f} (found at step {run.best_found_at_step})")
    print("Best tour: " + " -> ".join(str(node.node_id) for node in algorithm.best_tour))


def build_config(algorithm_type: AgorithmType, args) -> dict:
    if algorithm_type == AgorithmType.ANT_COLONY:
        return {
            "number_of_ants": 5,
            "alpha": 1.0,
            "beta": 2.0,
            "evaporation_rate": 0.2,
            "max_iterations": 100
        }
    return {
        "use_pruning": not args.no_pruning
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--width', type=int, help='Select the window width')
    parser.add_argument('-y', '--height', type=int, help='Select the window height')
    parser.add_argument('-n', '--num-of-nodes', type=int, help='Number of nodes in the graph')
    parser.add_argument('-f', '--fps', type=int, help='FPS of the display')
    parser.add_argument('-s', '--steps-per-frame', type=int, help='Number of steps per one frame of display')
    parser.add_argument('-a', '--algorithm', choices=ALGORITHM_TYPES.keys(),
                        help='Algorithm to run: aco, backtracking or compare (both side by side, default)')
    parser.add_argument('--seed', type=int, help='Seed for the random generator, same seed gives the same graph')
    parser.add_argument('--no-pruning', action='store_true', help='Backtracking only: check every tour, no branch and bound')
    parser.add_argument('--no-chart', action='store_true', help='Hide the best-length chart at the bottom')
    args = parser.parse_args()

    algorithm_name = args.algorithm or DEFAULT_ALGORITHM
    algorithm_types = ALGORITHM_TYPES[algorithm_name]

    width = args.width or PANEL_WIDTH * len(algorithm_types)
    height = args.height or DEFAULT_SCREEN_HEIGHT
    num_of_nodes = args.num_of_nodes or NODE_NUMBER
    fps = args.fps or FPS
    steps_per_frame = args.steps_per_frame or STEPS_PER_FRAME

    if args.seed is not None:
        random.seed(args.seed)

    layout = Layout(width, height, len(algorithm_types), show_chart=not args.no_chart)

    # one graph shared by all algorithms, so the comparison is fair
    graph = generate_random_graph(num_of_nodes, *layout.graph_size)

    runs = []
    for algorithm_type in algorithm_types:
        algorithm, renderer = create_algorithm_components(
            algorithm_type,
            graph,
            build_config(algorithm_type, args)
        )
        runs.append(AlgorithmRun(algorithm, renderer))

    display = Display(layout)
    application = Application(runs, display, fps, steps_per_frame)
    application.run()

    for run in runs:
        print_result(run)


if __name__ == "__main__":
    main()
