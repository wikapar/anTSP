from typing import Any
from graph.graph import Graph
from algorithms.ant_colony import AntColony
from display.ant_colony_renderer import AntColonyRenderer

def create_algorithm_components(algorithm_type, graph: Graph, config: dict[str, Any]):
    """A simple factory class for coupling the algorithm with the algorithm renderer.
    Add new elements by adding conditions"""
    if algorithm_type == "ant_colony":
        algorithm = AntColony(graph, **config)
        renderer = AntColonyRenderer()
        return algorithm, renderer

    raise ValueError(f"Unknown algorithm type: {algorithm_type}")