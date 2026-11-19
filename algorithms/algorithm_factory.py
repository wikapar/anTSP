from enum import Enum, auto
from typing import Any

from graph.graph import Graph
from algorithms.ant_colony import AntColony
from algorithms.backtracking import Backtracking
from algorithms.held_karp import HeldKarp
from display.ant_colony_renderer import AntColonyRenderer
from display.backtracking_renderer import BacktrackingRenderer
from display.held_karp_renderer import HeldKarpRenderer


class AlgorithmType(Enum):
    ANT_COLONY = auto()
    BACKTRACKING = auto()
    HELD_KARP = auto()


AgorithmType = AlgorithmType  # old (misspelled) name, kept so older code still works


def create_algorithm(algorithm_type: AlgorithmType, graph: Graph, config: dict[str, Any]):
    if algorithm_type == AlgorithmType.ANT_COLONY:
        return AntColony(graph, **config)
    if algorithm_type == AlgorithmType.BACKTRACKING:
        return Backtracking(graph, **config)
    if algorithm_type == AlgorithmType.HELD_KARP:
        return HeldKarp(graph, **config)
    raise ValueError(f"Unknown algorithm type: {algorithm_type}")


def create_algorithm_components(algorithm_type: AlgorithmType, graph: Graph, config: dict[str, Any]):
    """A simple factory for coupling the algorithm with the algorithm renderer.
    Add new elements by adding conditions"""
    algorithm = create_algorithm(algorithm_type, graph, config)
    renderers = {
        AlgorithmType.ANT_COLONY: AntColonyRenderer,
        AlgorithmType.BACKTRACKING: BacktrackingRenderer,
        AlgorithmType.HELD_KARP: HeldKarpRenderer,
    }
    return algorithm, renderers[algorithm_type]()
