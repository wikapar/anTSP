from enum import Enum, auto
from typing import Any
from graph.graph import Graph
from algorithms.ant_colony import AntColony
from display.ant_colony_renderer import AntColonyRenderer

class AgorithmType(Enum):
    ANT_COLONY = auto()
    BACKTRACKING = auto()

def create_algorithm_components(algorithm_type: AgorithmType, graph: Graph, config: dict[str, Any]):
    """A simple factory class for coupling the algorithm with the algorithm renderer.
    Add new elements by adding conditions"""
    if algorithm_type == AgorithmType.ANT_COLONY:
        algorithm = AntColony(graph, **config)
        renderer = AntColonyRenderer()
        return algorithm, renderer

    raise ValueError(f"Unknown algorithm type: {algorithm_type}")