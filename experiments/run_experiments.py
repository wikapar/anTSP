"""Headless experiments: ACO vs exact algorithms on many random graphs.

    python -m experiments.run_experiments --preset quick     # ~1-2 minutes, to try it out
    python -m experiments.run_experiments                    # full run (~20-40 minutes)
    python -m experiments.run_experiments --experiment sensitivity
    python -m experiments.run_experiments --add-to results/experiments/full --experiment sensitivity

Everything is seeded. Results go to results/experiments/<name>/:
    config.json       all settings + seeds + git commit -> rerun with --config config.json
    results.csv       one row per algorithm run
    convergence.csv   best tour length over time for every run (for convergence plots)
    summary.csv       mean / std per algorithm and n
    plots/*.png       figures for the slides (made by experiments/plot_results.py)

Every graph can be opened in the visualizer: the row has graph_seed and algo_seed, and
    python anTSP.py -n <n> --seed <graph_seed> --algo-seed <algo_seed>
shows exactly the same graph (graphs are generated for the default 2-panel window).
"""
import argparse
import csv
import json
import math
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from algorithms.ant_colony import AntColony  # noqa: E402
from algorithms.backtracking import Backtracking  # noqa: E402
from algorithms.held_karp import HeldKarp  # noqa: E402
from application.algorithm_run import AlgorithmRun  # noqa: E402
from display.display import Layout  # noqa: E402
from utils.helpers import generate_random_graph  # noqa: E402

# Graphs are generated for the same area the visualizer uses by default (2 panels),
# so `python anTSP.py -n N --seed S` shows the same graph as the experiment.
VISUALIZER_WINDOW = (1280, 860)
GRAPH_AREA = Layout(*VISUALIZER_WINDOW, 2).graph_size

# name -> (family, factory(graph, algo_seed, params)), the order is the order in the plots
EXACT_ALGORITHMS = {
    "Backtracking (no pruning)": lambda g, s, p: Backtracking(g, bound="none", break_symmetry=False),
    "Backtracking (simple bound)": lambda g, s, p: Backtracking(g, bound="simple"),
    "Backtracking (MST bound)": lambda g, s, p: Backtracking(g, bound="mst"),
    "Backtracking (MST + NN start)": lambda g, s, p: Backtracking(g, bound="mst", initial_tour="nn"),
    "Held-Karp (DP)": lambda g, s, p: HeldKarp(g),
}


def aco_factory(variant: str, local_search: bool = False):
    def create(graph, seed, params):
        return AntColony(graph, number_of_ants=params["ants"] or min(graph.get_size(), 20),
                         alpha=params["alpha"], beta=params["beta"], evaporation_rate=params["rho"],
                         max_iterations=params["iterations"], variant=variant,
                         local_search=local_search, seed=seed)
    return create


ACO_ALGORITHMS = {
    "Ant System": aco_factory("as"),
    "Elitist Ant System": aco_factory("elitist"),
    "MAX-MIN Ant System": aco_factory("mmas"),
    "MAX-MIN AS + 2-opt": aco_factory("mmas", local_search=True),
}

REFERENCE_ITERATIONS = 300  # long MAX-MIN AS + 2-opt run that gives the best known tour for large graphs
DEFAULT_ACO = {"ants": None, "alpha": 1.0, "beta": 2.0, "rho": 0.2, "iterations": 100}

PRESETS = {
    "quick": {
        "sizes": [5, 6, 7, 8, 9, 10, 12, 15, 20],
        "graphs_per_size": 3,
        "aco_repeats": 2,
        "time_limit": 10,
        "max_n": {"Backtracking (no pruning)": 10, "Held-Karp (DP)": 15},
        "convergence_n": 10,
        "sensitivity": {"n": 10, "graphs": 2, "repeats": 2, "iterations": 50,
                        "alpha": [0.5, 1, 2], "beta": [0, 1, 2, 5], "rho": [0.05, 0.2, 0.5, 0.9],
                        "ants": [1, 5, 10, 20]},
    },
    "full": {
        "sizes": [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 25, 30, 40, 50],
        "graphs_per_size": 5,
        "aco_repeats": 3,
        "time_limit": 30,
        "max_n": {"Backtracking (no pruning)": 11, "Held-Karp (DP)": 20},
        "convergence_n": 12,
        "sensitivity": {"n": 40, "graphs": 3, "repeats": 3, "iterations": 100,
                        "alpha": [0.5, 1, 2, 3], "beta": [0, 1, 2, 3, 5], "rho": [0.02, 0.05, 0.1, 0.2, 0.4, 0.6, 0.9],
                        "ants": [1, 2, 5, 10, 15, 20, 40]},
    },
}

RESULT_FIELDS = [
    "run_id", "experiment", "family", "algorithm", "n", "graph_seed", "algo_seed", "finished", "timed_out",
    "best_distance", "reference", "reference_is_optimal", "gap_percent", "is_optimal",
    "steps", "edge_evaluations", "cpu_seconds", "evaluations_to_best", "seconds_to_best",
    "param", "param_value", "ants", "alpha", "beta", "rho", "iterations",
]
CONVERGENCE_FIELDS = ["run_id", "step", "edge_evaluations", "cpu_seconds", "best_distance"]


def graph_seed_for(base_seed: int, n: int, index: int) -> int:
    return base_seed * 100_000 + n * 100 + index


def git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


class Writer:
    """Writes rows immediately, so the results survive Ctrl+C."""

    def __init__(self, out_dir: Path, replace_experiment: str | None = None):
        """replace_experiment: keep the existing files but drop the rows of this experiment."""
        kept_results, kept_convergence = [], []
        if replace_experiment is not None:
            with (out_dir / "results.csv").open() as file:
                old = list(csv.DictReader(file))
            kept_results = [row for row in old if row["experiment"] != replace_experiment]
            kept_ids = {row["run_id"] for row in kept_results}
            with (out_dir / "convergence.csv").open() as file:
                kept_convergence = [row for row in csv.DictReader(file) if row["run_id"] in kept_ids]

        self.results_file = (out_dir / "results.csv").open("w", newline="")
        self.convergence_file = (out_dir / "convergence.csv").open("w", newline="")
        self.results = csv.DictWriter(self.results_file, RESULT_FIELDS, extrasaction="ignore")
        self.convergence = csv.DictWriter(self.convergence_file, CONVERGENCE_FIELDS)
        self.results.writeheader()
        self.convergence.writeheader()
        self.results.writerows(kept_results)
        self.convergence.writerows(kept_convergence)
        self.run_id = max((int(row["run_id"]) for row in kept_results), default=0)

    def write(self, row: dict, run: AlgorithmRun):
        self.run_id += 1
        row["run_id"] = self.run_id
        self.results.writerow(row)
        for record in run.history:
            self.convergence.writerow({"run_id": self.run_id, "step": record.step,
                                       "edge_evaluations": record.evaluations,
                                       "cpu_seconds": round(record.time, 6), "best_distance": record.best})
        self.results_file.flush()
        self.convergence_file.flush()

    def close(self):
        self.results_file.close()
        self.convergence_file.close()


def execute(name, family, factory, graph, algo_seed, params, time_limit=None) -> tuple[dict, AlgorithmRun]:
    algorithm = factory(graph, algo_seed, params)
    run = AlgorithmRun(algorithm, name=name)
    finished = run.run_to_end(time_limit)
    best = run.best_distance
    last = run.history[-1] if run.history else None
    row = {
        "family": family, "algorithm": name, "n": graph.get_size(), "algo_seed": algo_seed,
        "finished": finished, "timed_out": not finished,
        "best_distance": round(best, 6) if math.isfinite(best) else "",
        "steps": run.steps, "edge_evaluations": run.evaluations, "cpu_seconds": round(run.elapsed, 6),
        "evaluations_to_best": last.evaluations if last else "",
        "seconds_to_best": round(last.time, 6) if last else "",
    }
    if family == "aco":
        row.update({"ants": algorithm.number_of_ants, "alpha": params["alpha"], "beta": params["beta"],
                    "rho": params["rho"], "iterations": params["iterations"]})
    return row, run


def add_reference(rows: list[dict], optimum: float | None):
    """Gap to the optimum (if an exact algorithm finished) or to the best known tour."""
    known = [row["best_distance"] for row in rows if row["best_distance"] != ""]
    reference = optimum if optimum is not None else (min(known) if known else None)
    for row in rows:
        row["reference"] = round(reference, 6) if reference else ""
        row["reference_is_optimal"] = optimum is not None
        if reference and row["best_distance"] != "":
            gap = (row["best_distance"] - reference) / reference * 100
            row["gap_percent"] = round(max(gap, 0.0), 6)
            row["is_optimal"] = optimum is not None and gap < 1e-6
        else:
            row["gap_percent"] = ""
            row["is_optimal"] = ""


def run_scaling(config: dict, writer: Writer, log):
    """For every size n and graph: all exact algorithms (until they get too slow) and all ACO variants."""
    disabled = set()
    for n in config["sizes"]:
        timed_out_at_n = set()
        for graph_index in range(config["graphs_per_size"]):
            graph_seed = graph_seed_for(config["seed"], n, graph_index)
            graph = generate_random_graph(n, *GRAPH_AREA, rng=random.Random(graph_seed))
            pending = []  # (row, run) - written after the reference (optimum) is known

            exact_lengths = []
            for name, factory in EXACT_ALGORITHMS.items():
                if name in disabled or n > config["max_n"].get(name, math.inf):
                    continue
                row, run = execute(name, "exact", factory, graph, 0, None, config["time_limit"])
                if row["timed_out"]:
                    timed_out_at_n.add(name)
                else:
                    exact_lengths.append(row["best_distance"])
                pending.append((row, run))
                log(f"n={n:<3} graph {graph_index}  {name:<30} {row['cpu_seconds']:>8.3f}s"
                    f"{'  TIMEOUT' if row['timed_out'] else ''}")

            if exact_lengths and max(exact_lengths) - min(exact_lengths) > 1e-6:
                raise RuntimeError(f"Exact algorithms disagree on n={n} seed={graph_seed}: {exact_lengths}")
            optimum = min(exact_lengths) if exact_lengths else None

            for name, factory in ACO_ALGORITHMS.items():
                for repeat in range(config["aco_repeats"]):
                    algo_seed = graph_seed * 10 + repeat
                    row, run = execute(name, "aco", factory, graph, algo_seed, config["aco"])
                    pending.append((row, run))
            aco_rows = [row for row, _ in pending if row["family"] == "aco"]
            add_reference([row for row, _ in pending], optimum)
            summary = ", ".join(f"{name.split(' ')[0]}{'+2opt' if '2-opt' in name else ''}="
                                f"{sum(r['gap_percent'] for r in aco_rows if r['algorithm'] == name) / config['aco_repeats']:.1f}%"
                                for name in ACO_ALGORITHMS)
            log(f"n={n:<3} graph {graph_index}  ACO gaps ({'optimum' if optimum else 'best known'}): {summary}")

            for row, run in pending:
                row.update({"experiment": "scaling", "graph_seed": graph_seed})
                writer.write(row, run)
        disabled |= timed_out_at_n  # too slow at this size -> skip bigger sizes


def run_sensitivity(config: dict, writer: Writer, log):
    """Ant System on fixed graphs, changing one parameter at a time (alpha x beta as a grid).
    Reference: the optimum (Held-Karp) for n <= 16, otherwise the best tour known on that graph
    (a long MAX-MIN AS + 2-opt run and all runs of the sweep)."""
    settings = config["sensitivity"]
    n = settings["n"]
    base = dict(config["aco"], iterations=settings["iterations"])
    graphs = []
    for graph_index in range(settings["graphs"]):
        graph_seed = graph_seed_for(config["seed"] + 1, n, graph_index)
        graph = generate_random_graph(n, *GRAPH_AREA, rng=random.Random(graph_seed))
        if n <= 16:
            exact = HeldKarp(graph)
            exact.solve()
            graphs.append((graph_seed, graph, exact.best_distance, True))
        else:
            reference = AntColony(graph, number_of_ants=min(n, 20), alpha=1, beta=2, evaporation_rate=0.1,
                                  max_iterations=REFERENCE_ITERATIONS, variant="mmas", local_search=True,
                                  seed=graph_seed)
            reference.solve()
            graphs.append((graph_seed, graph, reference.best_distance, False))
        log(f"sensitivity graph {graph_index}: reference length {graphs[-1][2]:.1f}"
            f" ({'optimum' if graphs[-1][3] else 'best known'})")

    variations = [("alpha,beta", {"alpha": a, "beta": b}, f"{a},{b}")
                  for a in settings["alpha"] for b in settings["beta"]]
    variations += [("rho", {"rho": rho}, rho) for rho in settings["rho"]]
    variations += [("ants", {"ants": ants}, ants) for ants in settings["ants"]]

    factory = ACO_ALGORITHMS["Ant System"]
    pending = {graph_seed: [] for graph_seed, *_ in graphs}
    for param, change, value in variations:
        params = dict(base, **change)
        lengths = []
        for graph_seed, graph, _, _ in graphs:
            for repeat in range(settings["repeats"]):
                row, run = execute("Ant System", "aco", factory, graph, graph_seed * 10 + repeat, params)
                row.update({"experiment": "sensitivity", "graph_seed": graph_seed,
                            "param": param, "param_value": value})
                pending[graph_seed].append((row, run))
                lengths.append(row["best_distance"])
        log(f"sensitivity n={n} {param}={value}: mean length {sum(lengths) / len(lengths):.1f}")

    for graph_seed, _, reference, is_optimal in graphs:
        rows = [row for row, _ in pending[graph_seed]]
        if is_optimal:
            add_reference(rows, reference)
        else:
            best_known = min([reference] + [row["best_distance"] for row in rows])
            for row in rows:
                row["reference"] = round(best_known, 6)
                row["reference_is_optimal"] = False
                row["gap_percent"] = round(max((row["best_distance"] - best_known) / best_known * 100, 0.0), 6)
                row["is_optimal"] = ""
        for row, run in pending[graph_seed]:
            writer.write(row, run)


def main():
    parser = argparse.ArgumentParser(description="Run the ACO vs exact algorithm experiments.")
    parser.add_argument("--preset", choices=PRESETS.keys(), default="full")
    parser.add_argument("--experiment", choices=("scaling", "sensitivity", "all"), default="all")
    parser.add_argument("--seed", type=int, default=1, help="Base seed, all graph and ant seeds derive from it")
    parser.add_argument("--sizes", type=int, nargs="+", help="Override the graph sizes")
    parser.add_argument("--graphs", type=int, help="Override graphs per size")
    parser.add_argument("--repeats", type=int, help="Override ACO runs per graph")
    parser.add_argument("--time-limit", type=float, help="Seconds before an exact algorithm is stopped")
    parser.add_argument("--name", help="Folder name in results/experiments (default: preset + date)")
    parser.add_argument("--config", type=Path, help="config.json of an earlier run to repeat it exactly")
    parser.add_argument("--add-to", type=Path, help="Existing result folder: (re)run only --experiment there "
                                                    "and keep the other results (e.g. redo the sensitivity part)")
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    if args.add_to:
        if args.experiment == "all":
            parser.error("--add-to needs --experiment scaling or sensitivity")
        config = json.loads((args.add_to / "config.json").read_text())
        preset = PRESETS[config["preset"]]
        config["sensitivity"] = preset["sensitivity"]
        config["sizes"] = args.sizes or preset["sizes"]
        config["experiment"] = args.experiment
    elif args.config:
        config = json.loads(args.config.read_text())
    else:
        config = json.loads(json.dumps(PRESETS[args.preset]))
        config.update({"preset": args.preset, "experiment": args.experiment, "seed": args.seed,
                       "aco": DEFAULT_ACO, "graph_area": GRAPH_AREA})
        if args.sizes:
            config["sizes"] = sorted(args.sizes)
        if args.graphs:
            config["graphs_per_size"] = args.graphs
        if args.repeats:
            config["aco_repeats"] = args.repeats
        if args.time_limit:
            config["time_limit"] = args.time_limit
    if min(config["sizes"]) < 3 or config["graphs_per_size"] < 1 or config["aco_repeats"] < 1:
        parser.error("sizes must be >= 3, graphs and repeats >= 1")

    if args.add_to:
        out_dir = args.add_to
        config.setdefault("updates", []).append({"experiment": args.experiment, "git_commit": git_commit(),
                                                 "date": datetime.now().isoformat(timespec="seconds")})
        saved = dict(config, experiment="all")
        (out_dir / "config.json").write_text(json.dumps(saved, indent=2))
    else:
        name = args.name or f"{config['preset']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        out_dir = ROOT / "results" / "experiments" / name
        out_dir.mkdir(parents=True, exist_ok=True)
        config.update({"started": datetime.now().isoformat(timespec="seconds"), "git_commit": git_commit(),
                       "python": sys.version.split()[0]})
        (out_dir / "config.json").write_text(json.dumps(config, indent=2))

    start = time.time()

    def log(message):
        print(f"[{time.time() - start:7.1f}s] {message}", flush=True)

    writer = Writer(out_dir, replace_experiment=config["experiment"] if args.add_to else None)
    try:
        if config["experiment"] in ("scaling", "all"):
            run_scaling(config, writer, log)
        if config["experiment"] in ("sensitivity", "all"):
            run_sensitivity(config, writer, log)
    except KeyboardInterrupt:
        log("Interrupted - the results so far are saved.")
    finally:
        writer.close()

    log(f"Results saved in {out_dir}")
    if not args.no_plots:
        from experiments.plot_results import make_all_plots
        make_all_plots(out_dir)


if __name__ == "__main__":
    main()
