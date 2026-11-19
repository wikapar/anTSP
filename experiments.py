import csv
from time import perf_counter

from algorithms.ant_colony import AntColony
from utils.helpers import generate_random_graph


def main():
    graph_seed = 42
    graph = generate_random_graph(10, 800, 600, seed=graph_seed)

    with open("results.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "number_of_ants",
            "graph_seed",
            "simulation_seed",
            "best_distance",
            "time_seconds",
        ])

        for number_of_ants in (1, 5, 10):
            for simulation_seed in (1, 2, 3, 4, 5):
                start = perf_counter()
                algorithm = AntColony(
                    graph,
                    number_of_ants=number_of_ants,
                    alpha=0.2,
                    beta=0.2,
                    evaporation_rate=0.5,
                    max_iterations=100,
                    seed=simulation_seed,
                )

                while not algorithm.is_finished():
                    algorithm.step()

                elapsed = perf_counter() - start
                writer.writerow([
                    number_of_ants,
                    graph_seed,
                    simulation_seed,
                    algorithm.best_distance,
                    elapsed,
                ])

    print("15 essais terminés. Ouvre results.csv pour voir les résultats.")


if __name__ == "__main__":
    main()