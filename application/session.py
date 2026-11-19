from dataclasses import dataclass

from application.algorithm_run import AlgorithmRun
from graph.graph import Graph


@dataclass
class Session:
    """Everything that belongs to one visual run: the graph, the algorithms and the seeds
    needed to reproduce it."""
    graph: Graph
    runs: list[AlgorithmRun]
    graph_seed: int
    algorithm_seed: int
    optimum: float | None = None  # known optimal tour length (computed with Held-Karp for small graphs)


@dataclass
class ViewState:
    """What the user changed with the keyboard."""
    paused: bool = False
    speed: float = 1.0  # steps per frame, can be < 1
    x_mode: str = "step"
    log_x: bool = False
