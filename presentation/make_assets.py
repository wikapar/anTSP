"""Creates the pictures and the animation for the presentation into presentation/assets/.

    python presentation/make_assets.py

Needs matplotlib and pygame (requirements.txt) and ffmpeg on PATH for the GIF/MP4.
"""
import math
import os
import random
import shutil
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


if __name__ == "__main__":
    tsp_intro()
    pruning_tree()
    double_bridge()
    simulation_animation()
    for path in sorted(OUT.iterdir()):
        print(f"  {path.name}  {path.stat().st_size / 1e6:.1f} MB")
