"""anTSP - visual comparison of ant colony optimization and exact algorithms for the TSP.

Examples:
    python anTSP.py                                  # ACO vs backtracking, side by side
    python anTSP.py -a aco backtracking heldkarp -x 1900
    python anTSP.py --seed 42 --algo-seed 7          # reproduce a run
    python anTSP.py --replay results/runs/run_....json
For the headless experiments (CSV + plots) see experiments/run_experiments.py.
"""
import argparse
import json
import random
import shlex
import sys
from datetime import datetime
from pathlib import Path

from algorithms.algorithm_factory import AlgorithmType, create_algorithm_components
from algorithms.ant_colony import AcoVariant, AntColony, DepositMode, validate_aco_parameters
from algorithms.backtracking import Bound
from algorithms.held_karp import HeldKarp, MAX_HELD_KARP_NODES
from application.algorithm_run import AlgorithmRun
from application.application import Application
from application.session import Session
from display.display import Display, Layout
from graph.graph import Graph
from utils.helpers import generate_random_graph, new_seed

PANEL_WIDTH = 640  # default window width = PANEL_WIDTH * number of algorithms
DEFAULT_SCREEN_HEIGHT = 860
NODE_NUMBER = 10
FPS = 30
STEPS_PER_FRAME = 1.0
MAX_ANTS_DEFAULT = 20
AUTO_OPTIMUM_MAX_NODES = 13  # Held-Karp takes < 1 s up to here
LOG_DIR = Path(__file__).parent / "results" / "runs"

ALGORITHM_CHOICES = {
    "aco": [AlgorithmType.ANT_COLONY],
    "backtracking": [AlgorithmType.BACKTRACKING],
    "heldkarp": [AlgorithmType.HELD_KARP],
    "compare": [AlgorithmType.ANT_COLONY, AlgorithmType.BACKTRACKING],
    "all": [AlgorithmType.ANT_COLONY, AlgorithmType.BACKTRACKING, AlgorithmType.HELD_KARP],
}

SEED_OPTIONS = ("--seed", "--algo-seed", "--replay")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Visualize and compare TSP algorithms.")
    window = parser.add_argument_group("window")
    window.add_argument('-x', '--width', type=int, help='Window width (default 640 per algorithm)')
    window.add_argument('-y', '--height', type=int, help=f'Window height (default {DEFAULT_SCREEN_HEIGHT})')
    window.add_argument('-f', '--fps', type=int, help=f'FPS of the display (default {FPS})')
    window.add_argument('-s', '--steps-per-frame', type=float,
                        help='Algorithm steps per frame, can be < 1, e.g. 0.5 (default 1). +/- keys change it')
    window.add_argument('--no-chart', action='store_true', help='Hide the best-length chart at the bottom')

    general = parser.add_argument_group("problem and reproducibility")
    general.add_argument('-a', '--algorithm', nargs='+', choices=ALGORITHM_CHOICES.keys(),
                         help='One or more of: aco, backtracking, heldkarp, compare (=aco backtracking, '
                              'default), all')
    general.add_argument('-n', '--num-of-nodes', type=int, help=f'Number of nodes (default {NODE_NUMBER})')
    general.add_argument('--seed', type=int, help='Graph seed: same seed (and window size) = same graph. '
                                                  'Random if not given, always printed and saved')
    general.add_argument('--algo-seed', type=int, help='Seed for the randomness of the algorithms (the ants)')
    general.add_argument('--optimum', choices=("auto", "on", "off"), default="auto",
                         help=f'Compute the optimal length with Held-Karp to show the gap '
                              f'(auto = only up to {AUTO_OPTIMUM_MAX_NODES} nodes)')
    general.add_argument('--replay', type=Path, help='Run log (results/runs/*.json) to reproduce exactly')
    general.add_argument('--no-log', action='store_true', help='Do not save the run log')

    aco = parser.add_argument_group("ant colony")
    aco.add_argument('--aco-variant', choices=[v.value for v in AcoVariant], default="as",
                     help='as = Ant System, elitist = Elitist AS, mmas = MAX-MIN Ant System (default as)')
    aco.add_argument('--ants', type=int, help=f'Number of ants (default: number of nodes, max {MAX_ANTS_DEFAULT})')
    aco.add_argument('--alpha', type=float, default=1.0, help='Pheromone weight (default 1)')
    aco.add_argument('--beta', type=float, default=2.0, help='Distance heuristic weight (default 2)')
    aco.add_argument('--rho', type=float, default=0.2, help='Evaporation rate in (0, 1] (default 0.2)')
    aco.add_argument('--iterations', type=int, default=100, help='Maximum iterations (default 100)')
    aco.add_argument('--stagnation', type=int, help='Stop after this many iterations without improvement')
    aco.add_argument('--two-opt', action='store_true', help='Improve every ant tour with 2-opt local search')
    aco.add_argument('--deposit', choices=[d.value for d in DepositMode], default="tour",
                     help='tour = deposit after the tour (classic), step = deposit on every move')

    bt = parser.add_argument_group("backtracking")
    bt.add_argument('--bound', choices=[b.value for b in Bound], default="mst",
                    help='Pruning: none, simple (path length) or mst (path + MST lower bound, default)')
    bt.add_argument('--no-pruning', action='store_true', help='Same as --bound none')
    bt.add_argument('--no-symmetry', action='store_true', help='Also search every tour in reverse direction')
    bt.add_argument('--initial-tour', choices=("none", "nn", "aco"), default="none",
                    help='Start with a known tour as upper bound: nearest neighbour or the result of ACO')

    args = parser.parse_args(argv)
    if args.replay:
        args = load_replay(args, parser)
    fill_defaults(args)
    validate(args, parser)
    return args


def load_replay(args, parser):
    try:
        data = json.loads(args.replay.read_text())
    except (OSError, ValueError) as error:
        parser.error(f"Cannot read replay file: {error}")
    replay = args.replay
    args = argparse.Namespace(**data["args"])
    args.replay = replay
    args.seed = data["graph_seed"]
    args.algo_seed = data["algorithm_seed"]
    args.command = data.get("command")
    return args


def fill_defaults(args):
    args.algorithm = args.algorithm or ["compare"]
    args.types = []
    for name in args.algorithm:
        for algorithm_type in ALGORITHM_CHOICES[name]:
            if algorithm_type not in args.types:
                args.types.append(algorithm_type)
    args.width = args.width or PANEL_WIDTH * len(args.types)
    args.height = args.height or DEFAULT_SCREEN_HEIGHT
    args.num_of_nodes = args.num_of_nodes or NODE_NUMBER
    args.fps = args.fps or FPS
    args.steps_per_frame = args.steps_per_frame or STEPS_PER_FRAME
    args.ants = args.ants or min(args.num_of_nodes, MAX_ANTS_DEFAULT)
    if args.no_pruning:
        args.bound = "none"


def validate(args, parser):
    """All parameters are checked here so the program fails with a clear message."""
    checks = [
        (args.num_of_nodes >= 3, "--num-of-nodes must be at least 3"),
        (args.fps >= 1, "--fps must be >= 1"),
        (args.steps_per_frame > 0, "--steps-per-frame must be > 0"),
        (args.width >= 300 and args.height >= 450, "window must be at least 300x450"),
        (args.seed is None or args.seed >= 0, "--seed must be >= 0"),
        (args.algo_seed is None or args.algo_seed >= 0, "--algo-seed must be >= 0"),
        (AlgorithmType.HELD_KARP not in args.types or args.num_of_nodes <= MAX_HELD_KARP_NODES,
         f"heldkarp supports at most {MAX_HELD_KARP_NODES} nodes"),
    ]
    for ok, message in checks:
        if not ok:
            parser.error(message)
    try:
        validate_aco_parameters(args.ants, args.alpha, args.beta, args.rho, args.iterations,
                                stagnation_limit=args.stagnation)
    except ValueError as error:
        parser.error(str(error).replace("number_of_ants", "--ants").replace("evaporation_rate", "--rho")
                     .replace("max_iterations", "--iterations").replace("stagnation_limit", "--stagnation"))


def aco_config(args, seed: int) -> dict:
    return {
        "number_of_ants": args.ants,
        "alpha": args.alpha,
        "beta": args.beta,
        "evaporation_rate": args.rho,
        "max_iterations": args.iterations,
        "variant": args.aco_variant,
        "local_search": args.two_opt,
        "deposit_mode": args.deposit,
        "stagnation_limit": args.stagnation,
        "seed": seed,
    }


def build_config(algorithm_type: AlgorithmType, args, graph: Graph, seed: int) -> tuple[dict, int]:
    """Returns (config, extra edge evaluations that were spent before the algorithm started)."""
    if algorithm_type == AlgorithmType.ANT_COLONY:
        return aco_config(args, seed), 0
    if algorithm_type == AlgorithmType.HELD_KARP:
        return {}, 0

    config = {"bound": args.bound, "break_symmetry": not args.no_symmetry}
    extra = 0
    if args.initial_tour == "nn":
        config["initial_tour"] = "nn"
    elif args.initial_tour == "aco":
        # hybrid: ACO finds a good tour fast, backtracking proves (or improves) it
        colony = AntColony(graph, **aco_config(args, seed))
        colony.solve()
        config["initial_tour"] = colony.best_tour
        extra = colony.edge_evaluations
    return config, extra


def compute_optimum(args, graph: Graph):
    n = graph.get_size()
    if args.optimum == "off" or (args.optimum == "auto" and n > AUTO_OPTIMUM_MAX_NODES):
        return None
    if n > MAX_HELD_KARP_NODES:
        print(f"Optimum not computed: more than {MAX_HELD_KARP_NODES} nodes.")
        return None
    if n > 15:
        print(f"Computing the optimum for {n} nodes with Held-Karp, this can take a while...")
    held_karp = HeldKarp(graph)
    held_karp.solve()
    return held_karp.best_distance


def reproduce_command(graph_seed: int, algorithm_seed: int, args=None) -> str:
    """The command line that was used, with the seeds that were actually used."""
    if args is not None and getattr(args, "command", None):
        argv = shlex.split(args.command)[2:]  # replay: the original command
    else:
        argv = sys.argv[1:]
    cleaned = []
    skip = False
    for arg in argv:
        if skip:
            skip = False
            continue
        if arg in SEED_OPTIONS:
            skip = True
            continue
        if any(arg.startswith(option + "=") for option in SEED_OPTIONS):
            continue
        cleaned.append(arg)
    cleaned += ["--seed", str(graph_seed), "--algo-seed", str(algorithm_seed)]
    return "python anTSP.py " + " ".join(shlex.quote(arg) for arg in cleaned)


def make_session_factory(args, layout: Layout):
    first = {"used": False}

    def create_session(graph_seed, algorithm_seed) -> Session:
        # the seeds from the command line are only used for the first graph, R creates a new one
        if not first["used"]:
            first["used"] = True
            graph_seed = args.seed if graph_seed is None else graph_seed
            algorithm_seed = args.algo_seed if algorithm_seed is None else algorithm_seed
        graph_seed = new_seed() if graph_seed is None else graph_seed
        algorithm_seed = new_seed() if algorithm_seed is None else algorithm_seed

        graph = generate_random_graph(args.num_of_nodes, *layout.graph_size, rng=random.Random(graph_seed))

        runs = []
        for index, algorithm_type in enumerate(args.types):
            config, extra_evaluations = build_config(algorithm_type, args, graph, algorithm_seed + index)
            algorithm, renderer = create_algorithm_components(algorithm_type, graph, config)
            algorithm.edge_evaluations += extra_evaluations
            if algorithm_type == AlgorithmType.ANT_COLONY:
                renderer.name = algorithm.display_name
            elif algorithm_type == AlgorithmType.BACKTRACKING:
                renderer.name = "Backtracking"
                if args.initial_tour != "none":
                    renderer.name += f" (start: {args.initial_tour.upper()})"
            runs.append(AlgorithmRun(algorithm, renderer, renderer.name))

        optimum = compute_optimum(args, graph)
        print(f"Graph seed: {graph_seed}   Algorithm seed: {algorithm_seed}")
        print(f"Reproduce with: {reproduce_command(graph_seed, algorithm_seed, args)}")
        return Session(graph, runs, graph_seed, algorithm_seed, optimum)

    return create_session


def print_result(run: AlgorithmRun, optimum):
    """Prints the best tour found so it can be compared between the algorithms."""
    algorithm = run.algorithm
    status = "finished" if algorithm.is_finished() else "stopped before finishing"
    print(f"Algorithm: {run.name} ({status}, {run.steps} steps, "
          f"{run.evaluations} edge evaluations, {run.elapsed:.3f} s)")

    if algorithm.best_tour is None:
        print("  No complete tour found.")
        return

    gap = f"  gap to optimum: {(run.best_distance - optimum) / optimum * 100:.2f}%" if optimum else ""
    print(f"  Best distance: {algorithm.best_distance:.2f} (found at step {run.best_found_at_step}){gap}")
    print("  Best tour: " + " -> ".join(str(node.node_id) for node in algorithm.best_tour))


def save_run_log(args, session: Session) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = LOG_DIR / f"run_{stamp}_g{session.graph_seed}.json"
    saved_args = {key: value for key, value in vars(args).items()
                  if key not in ("types", "replay", "command", "seed", "algo_seed")}
    data = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "command": reproduce_command(session.graph_seed, session.algorithm_seed, args),
        "graph_seed": session.graph_seed,
        "algorithm_seed": session.algorithm_seed,
        "args": saved_args,
        "optimum": session.optimum,
        "graph": session.graph.to_dict(),
        "results": [run.to_dict() for run in session.runs],
    }
    path.write_text(json.dumps(data, indent=1))
    return path


def main():
    args = parse_args()
    layout = Layout(args.width, args.height, len(args.types), show_chart=not args.no_chart)

    def on_session_end(session: Session):
        print()
        for run in session.runs:
            print_result(run, session.optimum)
        if session.optimum:
            print(f"Optimal distance: {session.optimum:.2f}")
        if not args.no_log:
            path = save_run_log(args, session)
            print(f"Run saved to {path}  (replay: python anTSP.py --replay {path})")

    display = Display(layout)
    application = Application(make_session_factory(args, layout), display, args.fps, args.steps_per_frame,
                              args.seed, args.algo_seed, on_session_end)
    application.run()


if __name__ == "__main__":
    main()
