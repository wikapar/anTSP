import csv
from time import perf_counter

from algorithms.ant_colony import AntColony
from utils.helpers import generate_random_graph


def main():
    graph_seed = 42
    graph = generate_random_graph(10, 800, 600, seed=graph_seed)
    number_of_ants = 5
    alpha_values = (0, 0.2, 1, 2)
    simulation_seeds = (1, 2, 3, 4, 5)

    with open("results_alpha.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "number_of_ants",
            "alpha",
            "graph_seed",
            "simulation_seed",
            "best_distance",
            "time_seconds",
        ])

        for alpha in alpha_values:
            for simulation_seed in simulation_seeds:
                start = perf_counter()
                algorithm = AntColony(
                    graph,
                    number_of_ants=number_of_ants,
                    alpha=alpha,
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
                    alpha,
                    graph_seed,
                    simulation_seed,
                    algorithm.best_distance,
                    elapsed,
                ])

    print("20 essais terminés. Ouvre results_alpha.csv pour voir les résultats.")


if __name__ == "__main__":
    main()