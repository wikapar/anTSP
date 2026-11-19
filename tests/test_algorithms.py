"""Run with:  python -m unittest discover tests"""
import itertools
import random
import unittest

from algorithms.ant_colony import AntColony
from algorithms.backtracking import Backtracking
from algorithms.held_karp import HeldKarp
from application.algorithm_run import AlgorithmRun
from utils.helpers import generate_random_graph
from utils.tsp import mst_length, nearest_neighbour_tour, tour_length, two_opt


def brute_force(graph) -> float:
    matrix = graph.distance_matrix
    n = graph.get_size()
    return min(tour_length([0, *perm, 0], matrix) for perm in itertools.permutations(range(1, n)))


def random_graph(n, seed):
    return generate_random_graph(n, 800, 600, rng=random.Random(seed))


def assert_valid_tour(test, tour_nodes, n):
    ids = [node.node_id for node in tour_nodes]
    test.assertEqual(ids[0], ids[-1], "tour must be closed")
    test.assertEqual(sorted(ids[:-1]), list(range(n)), "tour must visit every node exactly once")


class ExactAlgorithmsTest(unittest.TestCase):
    def test_backtracking_variants_find_optimum(self):
        for seed in range(6):
            for n in (3, 4, 6, 8):
                graph = random_graph(n, seed)
                optimum = brute_force(graph)
                for bound in ("none", "simple", "mst"):
                    for symmetry in (False, True):
                        for initial in (None, "nn"):
                            algorithm = Backtracking(graph, bound=bound, break_symmetry=symmetry,
                                                     initial_tour=initial)
                            self.assertTrue(algorithm.solve())
                            self.assertAlmostEqual(algorithm.best_distance, optimum, places=6,
                                                   msg=f"n={n} seed={seed} {bound} {symmetry} {initial}")
                            assert_valid_tour(self, algorithm.best_tour, n)

    def test_pruning_reduces_steps(self):
        graph = random_graph(8, 1)
        steps = {}
        for bound in ("none", "simple", "mst"):
            algorithm = Backtracking(graph, bound=bound, break_symmetry=False)
            algorithm.solve()
            steps[bound] = algorithm.steps
        self.assertLess(steps["simple"], steps["none"])
        self.assertLess(steps["mst"], steps["simple"])

    def test_held_karp_finds_optimum(self):
        for seed in range(5):
            for n in (3, 5, 8):
                graph = random_graph(n, seed)
                algorithm = HeldKarp(graph)
                algorithm.solve()
                self.assertAlmostEqual(algorithm.best_distance, brute_force(graph), places=6)
                assert_valid_tour(self, algorithm.best_tour, n)
                self.assertAlmostEqual(tour_length([node.node_id for node in algorithm.best_tour],
                                                   graph.distance_matrix), algorithm.best_distance, places=6)

    def test_backtracking_with_aco_initial_tour(self):
        graph = random_graph(8, 3)
        colony = AntColony(graph, 5, 1, 2, 0.2, max_iterations=10, seed=1)
        colony.solve()
        algorithm = Backtracking(graph, initial_tour=colony.best_tour)
        algorithm.solve()
        self.assertAlmostEqual(algorithm.best_distance, brute_force(graph), places=6)


class AntColonyTest(unittest.TestCase):
    def test_variants_produce_valid_tours(self):
        graph = random_graph(9, 0)
        optimum = brute_force(graph)
        for variant in ("as", "elitist", "mmas"):
            for local_search in (False, True):
                for deposit in ("tour", "step"):
                    colony = AntColony(graph, 6, 1, 2, 0.2, max_iterations=15, variant=variant,
                                       local_search=local_search, deposit_mode=deposit, seed=4)
                    colony.solve()
                    assert_valid_tour(self, colony.best_tour, 9)
                    self.assertGreaterEqual(colony.best_distance, optimum - 1e-6)
                    self.assertAlmostEqual(
                        tour_length([node.node_id for node in colony.best_tour], graph.distance_matrix),
                        colony.best_distance, places=6)

    def test_same_seed_same_result(self):
        graph = random_graph(12, 2)
        results = []
        for _ in range(2):
            colony = AntColony(graph, 8, 1, 2, 0.3, max_iterations=20, seed=99)
            colony.solve()
            results.append(([n.node_id for n in colony.best_tour], colony.edge_evaluations))
        self.assertEqual(results[0], results[1])

    def test_more_ants_than_nodes(self):
        graph = random_graph(4, 0)
        colony = AntColony(graph, 11, 1, 2, 0.2, max_iterations=3, seed=0)
        colony.solve()
        assert_valid_tour(self, colony.best_tour, 4)

    def test_stagnation_stops_early(self):
        graph = random_graph(6, 0)
        colony = AntColony(graph, 6, 1, 2, 0.2, max_iterations=1000, stagnation_limit=5, seed=0)
        colony.solve()
        self.assertLess(colony.current_iteration, 1000)

    def test_invalid_parameters(self):
        graph = random_graph(5, 0)
        for kwargs in ({"number_of_ants": 0}, {"alpha": -1}, {"beta": -1}, {"evaporation_rate": 0},
                       {"evaporation_rate": 1.5}, {"max_iterations": 0}):
            params = {"number_of_ants": 3, "alpha": 1, "beta": 2, "evaporation_rate": 0.2, **kwargs}
            with self.assertRaises(ValueError):
                AntColony(graph, **params)


class HelpersTest(unittest.TestCase):
    def test_graph_seed_reproducible_and_unique_positions(self):
        a = random_graph(30, 5)
        b = random_graph(30, 5)
        self.assertEqual(a.to_dict(), b.to_dict())
        positions = {(node.x, node.y) for node in a.get_nodes()}
        self.assertEqual(len(positions), 30)

    def test_two_opt_never_worse(self):
        graph = random_graph(15, 1)
        matrix = graph.distance_matrix
        tour = [0, *random.Random(1).sample(range(1, 15), 14), 0]
        improved, _ = two_opt(tour, matrix)
        self.assertLessEqual(tour_length(improved, matrix), tour_length(tour, matrix) + 1e-9)
        self.assertEqual(sorted(improved[:-1]), list(range(15)))

    def test_mst_is_lower_bound_of_hamiltonian_path(self):
        graph = random_graph(7, 2)
        matrix = graph.distance_matrix
        length, _ = mst_length(list(range(7)), matrix)
        nn, _ = nearest_neighbour_tour(0, matrix)
        self.assertLessEqual(length, tour_length(nn, matrix))

    def test_run_records_history(self):
        graph = random_graph(7, 0)
        run = AlgorithmRun(Backtracking(graph, initial_tour="nn"))
        self.assertEqual(run.history[0].step, 0)
        run.run_to_end()
        bests = [record.best for record in run.history]
        self.assertEqual(bests, sorted(bests, reverse=True))
        self.assertAlmostEqual(bests[-1], brute_force(graph), places=6)


if __name__ == "__main__":
    unittest.main()
