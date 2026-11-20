"""Creates the pictures and the animation for the presentation into presentation/assets/.

    python presentation/make_assets.py              # everything
    python presentation/make_assets.py emergence    # only one asset (tsp_intro, pruning_tree, ...)

Needs matplotlib and pygame (requirements.txt) and ffmpeg on PATH for the GIF/MP4.
"""
import csv
import math
import os
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent / "assets"
OUT.mkdir(exist_ok=True)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from algorithms.held_karp import HeldKarp  # noqa: E402
from utils.helpers import generate_random_graph  # noqa: E402
from utils.tsp import tour_length  # noqa: E402

INK = "#1d1d1b"
MUTED = "#6b6a66"
GREEN = "#1f9d5c"
ORANGE = "#eb6834"
BLUE = "#2a78d6"
RED = "#e34948"
LIGHT = "#d9d8d3"


def tsp_intro():
    """Same 12 cities: a random tour and the shortest tour."""
    graph = generate_random_graph(12, 620, 440, rng=random.Random(2026))
    matrix = graph.distance_matrix
    exact = HeldKarp(graph)
    exact.solve()
    optimal = [node.node_id for node in exact.best_tour]
    rng = random.Random(7)
    random_tour = [0] + rng.sample(range(1, 12), 11) + [0]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, tour, color, label in ((axes[0], random_tour, MUTED, "a random tour"),
                                   (axes[1], optimal, GREEN, "the shortest tour")):
        xs = [graph.nodes[i].x for i in tour]
        ys = [-graph.nodes[i].y for i in tour]
        ax.plot(xs, ys, color=color, linewidth=2.5, zorder=1)
        ax.scatter([n.x for n in graph.nodes], [-n.y for n in graph.nodes], s=90, color="white",
                   edgecolor=INK, linewidth=1.8, zorder=2)
        ax.set_title(f"{label}: length {tour_length(tour, matrix):.0f}", fontsize=16, color=INK, loc="left")
        ax.set_aspect("equal")
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "tsp_intro.png", dpi=200, transparent=True)
    plt.close(fig)


def pruning_tree():
    """Search tree of backtracking with pruned branches."""
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.axis("off")
    levels = {0: [(0.5, "A")], 1: [(0.17, "B"), (0.5, "C"), (0.83, "D")]}
    positions = {}
    for level, nodes in levels.items():
        for x, name in nodes:
            positions[name] = (x, 1 - level * 0.3)

    children = {
        "B": [(0.06, "C", "ok"), (0.28, "D", "ok")],
        "C": [(0.42, "B", "cut"), (0.58, "D", "ok")],
        "D": [(0.74, "B", "cut"), (0.92, "C", "cut")],
    }

    def node(x, y, text, face="white", edge=INK, size=900, color=INK):
        ax.scatter([x], [y], s=size, color=face, edgecolor=edge, linewidth=2, zorder=3)
        ax.text(x, y, text, ha="center", va="center", fontsize=14, color=color, zorder=4, fontweight="bold")

    for name in ("B", "C", "D"):
        ax.plot([0.5, positions[name][0]], [1, positions[name][1]], color=INK, linewidth=1.8, zorder=1)
    node(0.5, 1, "A", face=INK, color="white")
    for name in ("B", "C", "D"):
        node(*positions[name], name)

    for parent, items in children.items():
        px, py = positions[parent]
        for x, name, state in items:
            y = py - 0.3
            if state == "cut":
                ax.plot([px, x], [py, y], color=RED, linewidth=1.8, linestyle=(0, (4, 3)), zorder=1)
                node(x, y, name, face="#fbe3e3", edge=RED, color=RED)
                ax.text(x, y - 0.12, "cut", ha="center", fontsize=12, color=RED, fontweight="bold")
            else:
                ax.plot([px, x], [py, y], color=INK, linewidth=1.8, zorder=1)
                node(x, y, name)
                ax.plot([x, x], [y - 0.06, y - 0.2], color=LIGHT, linewidth=1.8, zorder=1)
                ax.text(x, y - 0.25, "...", ha="center", fontsize=14, color=MUTED)

    ax.text(0.02, 0.05, "path + lower bound of the rest  ≥  best tour so far   →   cut the whole branch",
            fontsize=12.5, color=INK, transform=ax.transAxes)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(0.0, 1.1)
    fig.tight_layout()
    fig.savefig(OUT / "pruning_tree.png", dpi=200, transparent=True)
    plt.close(fig)


def double_bridge():
    """Nest and food connected by a short and a long path; pheromone builds up on the short one."""
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.axis("off")
    nest, food = (0.08, 0.5), (0.92, 0.5)

    def curve(peak_y):
        """Quadratic Bezier from nest to food through height peak_y; returns a point function."""
        control_y = 2 * peak_y - 0.5
        return lambda t: ((1 - t) ** 2 * nest[0] + 2 * (1 - t) * t * 0.5 + t ** 2 * food[0],
                          (1 - t) ** 2 * nest[1] + 2 * (1 - t) * t * control_y + t ** 2 * food[1])

    short, long = curve(0.38), curve(0.88)
    for path, width, alpha in ((short, 16, 0.85), (long, 3, 0.4)):
        points = [path(i / 100) for i in range(101)]
        ax.plot([p[0] for p in points], [p[1] for p in points], color=ORANGE, linewidth=width, alpha=alpha,
                solid_capstyle="round", zorder=1)
    for t in (0.2, 0.32, 0.44, 0.56, 0.68, 0.8):
        x, y = short(t)
        ax.scatter([x], [y], s=60, color=INK, zorder=3)
    for t in (0.3, 0.7):
        x, y = long(t)
        ax.scatter([x], [y], s=60, color=INK, zorder=3)
    for (x, y), label in ((nest, "nest"), (food, "food")):
        ax.scatter([x], [y], s=1400, color="white", edgecolor=INK, linewidth=2, zorder=4)
        ax.text(x, y, label, ha="center", va="center", fontsize=13, fontweight="bold", color=INK, zorder=5)
    ax.text(0.5, 0.27, "short path: ants return sooner → more pheromone → more ants",
            ha="center", fontsize=12.5, color=INK)
    ax.text(0.5, 0.94, "long path: pheromone evaporates before it is reinforced",
            ha="center", fontsize=12.5, color=MUTED)
    ax.set_xlim(0, 1)
    ax.set_ylim(0.2, 1.0)
    fig.tight_layout()
    fig.savefig(OUT / "double_bridge.png", dpi=200, transparent=True)
    plt.close(fig)


def simulation_animation(graph_seed=30, algo_seed=4, nodes=10, steps_per_frame=6, max_frames=360):
    """Records the visualizer (ACO vs backtracking, same graph) and makes a GIF and an MP4."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame
    import anTSP
    from display.display import Display, Layout
    from application.session import ViewState

    argv = ["-n", str(nodes), "--seed", str(graph_seed), "--algo-seed", str(algo_seed), "--no-log"]
    sys.argv = ["anTSP.py"] + argv
    args = anTSP.parse_args(argv)
    layout = Layout(args.width, args.height, len(args.types))
    display = Display(layout)
    session = anTSP.make_session_factory(args, layout)(graph_seed, algo_seed)
    view = ViewState(speed=steps_per_frame)

    frames_dir = Path(tempfile.mkdtemp())
    frame = 0
    hold = 0
    while frame < max_frames:
        for _ in range(steps_per_frame):
            for run in session.runs:
                run.step()
        display.draw(session, view)
        pygame.image.save(display.screen, str(frames_dir / f"f{frame:04d}.png"))
        frame += 1
        if all(run.is_finished() for run in session.runs):
            hold += 1
            if hold > 30:  # keep the final state on screen for ~2.5 s
                break
    pygame.quit()
    print(f"animation: {frame} frames; " + ", ".join(
        f"{run.name}: {run.best_distance:.1f} after {run.steps} steps" for run in session.runs))

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print("ffmpeg not found - frames are in", frames_dir)
        return
    pattern = str(frames_dir / "f%04d.png")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-framerate", "12", "-i", pattern,
                    "-vf", "scale=1280:-2", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(OUT / "simulation.mp4")],
                   check=True)
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-framerate", "12", "-i", pattern, "-vf",
                    "scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=none",
                    str(OUT / "simulation.gif")], check=True)
    shutil.copy(frames_dir / f"f{frame - 1:04d}.png", OUT / "simulation_last_frame.png")
    shutil.copy(frames_dir / f"f{min(60, frame - 1):04d}.png", OUT / "simulation_frame.png")
    shutil.rmtree(frames_dir)


def emergence(n=30, graphs=5, repeats=3, ants=20, iterations=100):
    """One ant vs. a colony with the same budget of tours (ants * iterations) on the 30-city maps of the
    full experiment. Three groups, all Ant System with beta = 2, rho = 0.2:
      * colony: 20 ants that follow the shared pheromone (alpha = 1)
      * one ant: a single ant with its own trail, 2000 iterations (alpha = 1)
      * no trails: 20 ants that ignore pheromone (alpha = 0), i.e. 2000 independent tours
    Writes emergence.png and emergence.csv (gap of the best tour so far after every tour)."""
    from algorithms.ant_colony import AntColony
    from experiments.run_experiments import GRAPH_AREA, graph_seed_for

    # best known tour per map (from the full experiment)
    reference = {}
    with (ROOT / "results" / "experiments" / "full" / "results.csv").open() as file:
        for row in csv.DictReader(file):
            if row["experiment"] == "scaling" and int(row["n"]) == n:
                reference[int(row["graph_seed"])] = float(row["reference"])

    budget = ants * iterations
    groups = {"colony": (ants, iterations, 1.0), "one ant": (1, budget, 1.0), "no trails": (ants, iterations, 0.0)}
    curves = {name: [] for name in groups}
    mean_tour = {name: [] for name in groups}  # average single ant tour in the first / last iteration
    for graph_index in range(graphs):
        graph_seed = graph_seed_for(1, n, graph_index)
        graph = generate_random_graph(n, *GRAPH_AREA, rng=random.Random(graph_seed))
        matrix = graph.distance_matrix
        best_known = reference[graph_seed]
        for repeat in range(repeats):
            for name, (m, its, alpha) in groups.items():
                colony = AntColony(graph, number_of_ants=m, alpha=alpha, beta=2.0, evaporation_rate=0.2,
                                   max_iterations=its, seed=graph_seed * 10 + repeat)
                best, curve, means = math.inf, [], []
                while not colony.is_finished():
                    if all(ant.finished for ant in colony.ants):
                        lengths = [tour_length([node.node_id for node in ant.tour], matrix) for ant in colony.ants]
                        for length in lengths:
                            best = min(best, length)
                            curve.append((best - best_known) / best_known * 100)
                        means.append((statistics.mean(lengths) - best_known) / best_known * 100)
                    colony.step()
                curves[name].append(curve)
                mean_tour[name].append((means[0], means[-1]))

    median = {name: [statistics.median(run[i] for run in runs) for i in range(budget)]
              for name, runs in curves.items()}
    with (OUT / "emergence.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["tours"] + [f"{name} (median gap %)" for name in groups])
        for i in range(budget):
            writer.writerow([i + 1] + [f"{median[name][i]:.3f}" for name in groups])
    for name in groups:
        first = statistics.median(a for a, _ in mean_tour[name])
        last = statistics.median(b for _, b in mean_tour[name])
        print(f"emergence {name:10s}: best after {budget} tours {median[name][-1]:5.1f} %, "
              f"after {ants} tours {median[name][ants - 1]:5.1f} %; "
              f"average tour first/last iteration {first:5.1f} / {last:5.1f} %")

    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e4e4e0", linewidth=0.8)
    ax.set_axisbelow(True)
    x = range(1, budget + 1)
    styles = {"no trails": (MUTED, f"{ants} ants that ignore the trails"),
              "one ant": ("#f0a27f", "1 ant with its own trail"),
              "colony": (ORANGE, f"colony: {ants} ants sharing trails")}
    label_y = {"no trails": median["no trails"][-1], "colony": max(median["colony"][-1], 3)}
    label_y["one ant"] = max(median["one ant"][-1] + 2, label_y["colony"] + 8)  # keep the labels apart
    for name in ("no trails", "one ant", "colony"):
        color, label = styles[name]
        ax.plot(x, median[name], color=color, linewidth=3)
        gap = median[name][-1]
        ax.text(budget * 1.02, label_y[name], f"{gap:.0f} %  {label}" if gap >= 1 else f"{gap:.1f} %  {label}",
                va="center", fontsize=13, color=color, fontweight="bold")
    ax.annotate("fast at first, then stuck\non its own route", xy=(300, median["one ant"][300]),
                xytext=(560, 22), fontsize=12, color=MUTED,
                arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 1})
    ax.spines["left"].set_color("#bdbdb8")
    ax.spines["bottom"].set_color("#bdbdb8")
    ax.set_xticks(range(0, budget + 1, budget // 4))
    ax.set_xlim(0, budget)
    ax.set_ylim(-1, 92)
    ax.set_xlabel("tours built (all ants together)", fontsize=13, color=MUTED)
    ax.set_ylabel("best tour so far: % above best known", fontsize=13, color=MUTED)
    ax.tick_params(colors=MUTED, labelsize=12)
    fig.tight_layout()
    fig.savefig(OUT / "emergence.png", dpi=200, transparent=True, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    assets = {"tsp_intro": tsp_intro, "pruning_tree": pruning_tree, "double_bridge": double_bridge,
              "emergence": emergence, "simulation": simulation_animation}
    for name in sys.argv[1:] or assets:
        assets[name]()
    for path in sorted(OUT.iterdir()):
        print(f"  {path.name}  {path.stat().st_size / 1e6:.1f} MB")
