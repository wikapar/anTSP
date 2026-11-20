"""Makes the presentation figures from an experiment folder.

    python -m experiments.plot_results results/experiments/<name>

Writes plots/*.png (and .svg) and summary.csv into that folder.
"""
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import matplotlib.colors  # noqa: E402
import numpy as np  # noqa: E402

# One fixed color per algorithm in every figure (validated categorical palette, light mode)
COLORS = {
    "Backtracking (no pruning)": "#e34948",
    "Backtracking (simple bound)": "#e87ba4",
    "Backtracking (MST bound)": "#6250d6",
    "Backtracking (MST + NN start)": "#2a78d6",
    "Held-Karp (DP)": "#52514e",
    "Ant System": "#eb6834",
    "Elitist Ant System": "#eda100",
    "MAX-MIN Ant System": "#008300",
    "MAX-MIN AS + 2-opt": "#1baf7a",
}
EXACT = list(COLORS)[:5]
ACO = list(COLORS)[5:]
MAIN = ["Backtracking (no pruning)", "Backtracking (MST + NN start)", "Held-Karp (DP)",
        "Ant System", "MAX-MIN AS + 2-opt"]

TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e4e0"
FIGSIZE = (12, 6.2)  # wide slide, legend on the right


def style():
    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "font.size": 13, "axes.titlesize": 17, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": 13, "axes.labelcolor": TEXT_SECONDARY, "axes.edgecolor": "#bdbdb8",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
        "xtick.color": TEXT_SECONDARY, "ytick.color": TEXT_SECONDARY,
        "legend.frameon": False, "legend.fontsize": 11, "lines.linewidth": 2, "lines.markersize": 6,
    })


def marker(name):
    return "s" if name in EXACT else "o"


# ----- loading -----

def to_number(value):
    if value in ("", None):
        return None
    if value in ("True", "False"):
        return value == "True"
    try:
        number = float(value)
        return int(number) if number.is_integer() and "." not in value else number
    except ValueError:
        return value


def load(path: Path) -> list[dict]:
    with path.open() as file:
        return [{key: to_number(value) for key, value in row.items()} for row in csv.DictReader(file)]


def group(rows, *keys):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    return groups


# ----- helpers -----

def title(ax, text, subtitle=None):
    ax.set_title(text, pad=28 if subtitle else 12)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=TEXT_SECONDARY, fontsize=11, va="bottom")


def outside_legend(ax, **kwargs):
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), **kwargs)


def integer_ticks(ax):
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))


def save(fig, out_dir: Path, name: str):
    fig.tight_layout()
    fig.savefig(out_dir / f"{name}.png", dpi=200)
    fig.savefig(out_dir / f"{name}.svg")
    plt.close(fig)
    print(f"  {name}.png")


def median_by_n(rows, algorithm, field, only_finished=True):
    points = []
    for (n,), group_rows in sorted(group([r for r in rows if r["algorithm"] == algorithm], "n").items()):
        values = [r[field] for r in group_rows if r[field] is not None and (r["finished"] or not only_finished)]
        if only_finished and len(values) < len(group_rows):
            continue  # some graphs timed out at this size: a median would be misleading
        if values:
            points.append((n, statistics.median(values), min(values), max(values)))
    return points


# ----- figures -----

def plot_scaling(rows, out_dir, field, ylabel, name, heading, algorithms, time_limit):
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for algorithm in algorithms:
        points = median_by_n(rows, algorithm, field)
        if not points:
            continue
        ns, medians, lows, highs = zip(*points)
        ax.plot(ns, medians, color=COLORS[algorithm], marker=marker(algorithm), label=algorithm)
        ax.fill_between(ns, lows, highs, color=COLORS[algorithm], alpha=0.12, linewidth=0)
    ax.set_yscale("log")
    ax.set_xlabel("number of nodes n")
    ax.set_ylabel(ylabel)
    title(ax, heading, f"median over graphs (band = min-max); exact algorithms are stopped after {time_limit:g} s "
                       f"and not run on larger n")
    integer_ticks(ax)
    outside_legend(ax)
    save(fig, out_dir, name)


def plot_aco_gap(rows, out_dir):
    aco_rows = [r for r in rows if r["family"] == "aco" and r["gap_percent"] is not None]
    if not aco_rows:
        return
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for algorithm in ACO:
        by_n = sorted(group([r for r in aco_rows if r["algorithm"] == algorithm], "n").items())
        if not by_n:
            continue
        ns = [n for (n,), _ in by_n]
        means = [statistics.mean(r["gap_percent"] for r in g) for _, g in by_n]
        stds = [statistics.pstdev([r["gap_percent"] for r in g]) for _, g in by_n]
        ax.plot(ns, means, color=COLORS[algorithm], marker="o", label=algorithm)
        ax.fill_between(ns, np.subtract(means, stds).clip(0), np.add(means, stds),
                        color=COLORS[algorithm], alpha=0.12, linewidth=0)

    unknown = sorted({r["n"] for r in aco_rows if not r["reference_is_optimal"]})
    if unknown:
        start = unknown[0] - 0.5
        ax.axvspan(start, max(r["n"] for r in aco_rows) + 1, color="#f2f2ef", zorder=0)
        ax.text(start + 0.3, 0.97, "optimum unknown:\ngap to best tour found", transform=ax.get_xaxis_transform(),
                color=TEXT_SECONDARY, fontsize=10, va="top")
    ax.set_xlabel("number of nodes n")
    ax.set_ylabel("gap to optimum (%)")
    ax.set_ylim(bottom=0)
    integer_ticks(ax)
    title(ax, "ACO solution quality: how far from the optimal tour?",
          "mean over graphs and runs (band = ±1 std), 100 iterations; 0 % = optimal tour found")
    ax.legend(loc="upper left")
    save(fig, out_dir, "04_aco_gap_vs_n")


def plot_optimal_rate(rows, out_dir):
    aco_rows = [r for r in rows if r["family"] == "aco" and r["reference_is_optimal"]]
    if not aco_rows:
        return
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for algorithm in ACO:
        by_n = sorted(group([r for r in aco_rows if r["algorithm"] == algorithm], "n").items())
        if not by_n:
            continue
        ns = [n for (n,), _ in by_n]
        rates = [100 * sum(1 for r in g if r["is_optimal"]) / len(g) for _, g in by_n]
        ax.plot(ns, rates, color=COLORS[algorithm], marker="o", label=algorithm)
    ax.set_ylim(-3, 103)
    ax.set_xlabel("number of nodes n (only sizes where the optimum is known)")
    ax.set_ylabel("runs that found the optimum (%)")
    title(ax, "How often does ACO find the exact optimum?", "share of ACO runs whose best tour is optimal")
    integer_ticks(ax)
    outside_legend(ax)
    save(fig, out_dir, "05_aco_optimal_rate")


def best_at(history, x):
    """history: sorted list of (x, best). Returns best known at x or nan."""
    value = math.nan
    for hx, best in history:
        if hx > x:
            break
        value = best
    return value


def plot_convergence(rows, convergence, out_dir, n):
    runs = [r for r in rows if r["n"] == n and r["experiment"] == "scaling" and r["reference_is_optimal"]]
    if not runs:
        return
    histories = group(convergence, "run_id")
    fig, ax = plt.subplots(figsize=FIGSIZE)
    max_x = max(r["edge_evaluations"] for r in runs)
    grid = np.logspace(1, math.log10(max_x), 300)
    for algorithm in ACO + EXACT:
        algorithm_runs = [r for r in runs if r["algorithm"] == algorithm and r["finished"]]
        if not algorithm_runs:
            continue
        curves = []
        for run in algorithm_runs:
            history = [(h["edge_evaluations"], h["best_distance"]) for h in histories.get((run["run_id"],), [])]
            # after the run ended its final result stays (the median stays monotone)
            gap = [(best_at(history, x) - run["reference"]) / run["reference"] * 100 for x in grid]
            curves.append(gap)
        curves = np.array(curves)
        # median over runs; no tour yet counts as infinitely bad, shown only once half of the runs have a tour
        with np.errstate(all="ignore"):
            median = np.median(np.where(np.isnan(curves), np.inf, curves), axis=0)
        median[np.isinf(median)] = np.nan
        last_finish = max(r["edge_evaluations"] for r in algorithm_runs)
        median[grid > last_finish * 1.0001] = np.nan
        if np.all(np.isnan(median)):
            continue
        style_kwargs = {"linestyle": "--"} if algorithm in EXACT else {}
        ax.plot(grid, median, color=COLORS[algorithm], label=algorithm, **style_kwargs)
        finish = statistics.median(r["edge_evaluations"] for r in algorithm_runs)
        if algorithm in EXACT:
            ax.plot([finish], [0], marker="s", color=COLORS[algorithm], markersize=9, clip_on=False, zorder=5)

    ax.set_xscale("log")
    ax.set_ylim(bottom=-0.5)
    ax.set_xlabel("work: edge evaluations (log scale)")
    ax.set_ylabel("gap to optimum (%)")
    title(ax, f"Convergence on graphs with n = {n}",
          "median best-so-far tour; dashed = exact algorithms, square = proved optimal (search finished)")
    outside_legend(ax, fontsize=10)
    save(fig, out_dir, f"06_convergence_n{n}")


def plot_tradeoff(rows, out_dir):
    """Bar per algorithm: median CPU time, with the mean gap written next to it.
    Uses the largest n where the optimum is known for every graph."""
    by_n = group([r for r in rows if r["experiment"] == "scaling"], "n")
    solved_sizes = [n for (n,), g in by_n.items() if all(r["reference_is_optimal"] for r in g)]
    if not solved_sizes:
        return
    n = max(solved_sizes)
    at_n = by_n[(n,)]
    bars = []
    for algorithm in EXACT + ACO:
        group_rows = [r for r in at_n if r["algorithm"] == algorithm]
        if not group_rows or not all(r["finished"] for r in group_rows):
            continue
        time = statistics.median(r["cpu_seconds"] for r in group_rows)
        gap = statistics.mean(r["gap_percent"] for r in group_rows)
        optimal = sum(1 for r in group_rows if r["is_optimal"]) / len(group_rows) * 100
        bars.append((algorithm, time, gap, optimal))
    if not bars:
        return

    fig, ax = plt.subplots(figsize=FIGSIZE)
    names = [b[0] for b in bars][::-1]
    times = [b[1] for b in bars][::-1]
    base = 10 ** math.floor(math.log10(min(times) / 3))  # bars start at a round value left of all times
    ax.barh(names, [t - base for t in times], left=base, color=[COLORS[name] for name in names], height=0.6)
    ax.set_xscale("log")
    for y, (name, time, gap, optimal) in enumerate(bars[::-1]):
        text = "exact: 0 % (proved)" if name in EXACT else f"gap {gap:.2f} %, optimal in {optimal:.0f} % of runs"
        ax.annotate(f"{time:.3g} s   {text}", (time, y), xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=10.5, color=TEXT)
    ax.set_xlim(base, max(times) * 60)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("median CPU time per run (s, log scale)")
    title(ax, f"Time and quality at n = {n}",
          "largest size where every graph was solved exactly; ACO runs 100 iterations")
    save(fig, out_dir, "07_tradeoff")


def plot_sensitivity(rows, out_dir):
    rows = [r for r in rows if r["experiment"] == "sensitivity"]
    if not rows:
        return
    n = rows[0]["n"]
    optimal = all(r["reference_is_optimal"] for r in rows)
    gap_label = "gap to optimum (%)" if optimal else "gap to best known tour (%)"
    graphs = len({r["graph_seed"] for r in rows})
    runs = len({r["algo_seed"] for r in rows}) // max(1, graphs)
    setup = (f"{graphs} graphs x {runs} runs, {rows[0]['iterations']} iterations; "
             + ("reference = optimum (Held-Karp)" if optimal else "reference = best tour ever found on the graph"))

    grid_rows = [r for r in rows if r["param"] == "alpha,beta"]
    if grid_rows:
        cells = group(grid_rows, "param_value")
        alphas = sorted({float(str(v).split(",")[0]) for (v,) in cells})
        betas = sorted({float(str(v).split(",")[1]) for (v,) in cells})
        matrix = np.full((len(alphas), len(betas)), np.nan)
        for (value,), cell in cells.items():
            a, b = (float(x) for x in str(value).split(","))
            matrix[alphas.index(a), betas.index(b)] = statistics.mean(r["gap_percent"] for r in cell)
        fig, ax = plt.subplots(figsize=FIGSIZE)
        # log colors: one bad setting (e.g. beta = 0) would otherwise make all other cells look the same
        norm = matplotlib.colors.LogNorm(vmin=max(np.nanmin(matrix), 0.1), vmax=max(np.nanmax(matrix), 0.2))
        image = ax.imshow(np.clip(matrix, norm.vmin, None), cmap="Blues", aspect="auto", origin="lower", norm=norm)
        ax.grid(False)
        ax.set_xticks(range(len(betas)), [f"{b:g}" for b in betas])
        ax.set_yticks(range(len(alphas)), [f"{a:g}" for a in alphas])
        ax.set_xlabel("beta (weight of the distance heuristic)")
        ax.set_ylabel("alpha (weight of pheromone)")
        for i in range(len(alphas)):
            for j in range(len(betas)):
                dark = norm(max(matrix[i, j], norm.vmin)) > 0.6
                ax.text(j, i, f"{matrix[i, j]:.1f}%", ha="center", va="center", fontsize=12,
                        color="white" if dark else TEXT)
        fig.colorbar(image, ax=ax, label="mean " + gap_label)
        title(ax, f"Ant System: effect of alpha and beta (n = {n})", "mean gap (log color scale), lower is better; " + setup)
        save(fig, out_dir, "08_sensitivity_alpha_beta")

    for param, label, name in (("rho", "evaporation rate rho", "09_sensitivity_rho"),
                               ("ants", "number of ants", "10_sensitivity_ants")):
        param_rows = [r for r in rows if r["param"] == param]
        if not param_rows:
            continue
        by_value = sorted(group(param_rows, "param_value").items(), key=lambda item: float(item[0][0]))
        xs = [float(v) for (v,), _ in by_value]
        means = [statistics.mean(r["gap_percent"] for r in g) for _, g in by_value]
        stds = [statistics.pstdev([r["gap_percent"] for r in g]) for _, g in by_value]
        fig, ax = plt.subplots(figsize=FIGSIZE)
        ax.plot(xs, means, color=COLORS["Ant System"], marker="o")
        ax.fill_between(xs, np.subtract(means, stds).clip(0), np.add(means, stds), color=COLORS["Ant System"],
                        alpha=0.15, linewidth=0)
        if param == "ants":
            ax.set_xscale("log")
            ax.set_xticks(xs, [f"{x:g}" for x in xs])
        ax.set_ylim(bottom=0)
        ax.set_xlabel(label)
        ax.set_ylabel(gap_label)
        title(ax, f"Ant System: effect of the {label} (n = {n})", "mean (band = ±1 std); " + setup)
        save(fig, out_dir, name)


def write_summary(rows, out_dir: Path):
    fields = ["algorithm", "n", "runs", "finished", "mean_gap_percent", "std_gap_percent", "optimal_rate",
              "median_cpu_seconds", "median_edge_evaluations", "reference_is_optimal"]
    with (out_dir / "summary.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fields)
        writer.writeheader()
        scaling = [r for r in rows if r["experiment"] == "scaling"]
        order = {name: i for i, name in enumerate(COLORS)}
        for (algorithm, n), g in sorted(group(scaling, "algorithm", "n").items(),
                                        key=lambda item: (order.get(item[0][0], 99), item[0][1])):
            gaps = [r["gap_percent"] for r in g if r["gap_percent"] is not None and r["finished"]]
            finished = [r for r in g if r["finished"]]
            writer.writerow({
                "algorithm": algorithm, "n": n, "runs": len(g), "finished": len(finished),
                "mean_gap_percent": round(statistics.mean(gaps), 3) if gaps else "",
                "std_gap_percent": round(statistics.pstdev(gaps), 3) if gaps else "",
                "optimal_rate": round(sum(1 for r in finished if r["is_optimal"]) / len(g), 3)
                if g[0]["reference_is_optimal"] else "",
                "median_cpu_seconds": round(statistics.median(r["cpu_seconds"] for r in finished), 4)
                if finished else "",
                "median_edge_evaluations": statistics.median(r["edge_evaluations"] for r in finished)
                if finished else "",
                "reference_is_optimal": g[0]["reference_is_optimal"],
            })
    print("  summary.csv")


def make_all_plots(folder: Path):
    import json
    folder = Path(folder)
    config = json.loads((folder / "config.json").read_text())
    rows = load(folder / "results.csv")
    convergence = load(folder / "convergence.csv")
    out_dir = folder / "plots"
    out_dir.mkdir(exist_ok=True)
    style()
    print(f"Plots for {folder}:")

    scaling = [r for r in rows if r["experiment"] == "scaling"]
    if scaling:
        time_limit = config["time_limit"]
        plot_scaling(scaling, out_dir, "cpu_seconds", "CPU time per run (s, log scale)", "01_runtime_vs_n",
                     "Runtime: exact algorithms explode, ACO grows slowly", MAIN, time_limit)
        plot_scaling(scaling, out_dir, "edge_evaluations", "edge evaluations (log scale)", "02_work_vs_n",
                     "Work (machine independent): edge evaluations per run", MAIN, time_limit)
        plot_scaling(scaling, out_dir, "cpu_seconds", "CPU time per run (s, log scale)", "03_exact_algorithms",
                     "Exact algorithms: effect of pruning, symmetry and a start tour", EXACT, time_limit)
        plot_aco_gap(scaling, out_dir)
        plot_optimal_rate(scaling, out_dir)
        convergence_n = config.get("convergence_n")
        available = sorted({r["n"] for r in scaling if r["reference_is_optimal"]})
        if available:
            n = convergence_n if convergence_n in available else available[-1]
            plot_convergence(scaling, convergence, out_dir, n)
        plot_tradeoff(scaling, out_dir)
        write_summary(rows, folder)
    plot_sensitivity(rows, out_dir)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    make_all_plots(Path(sys.argv[1]))
