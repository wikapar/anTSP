from statistics import mean, median, stdev

import matplotlib.pyplot as plt

from algorithms.ant_colony import AntColony
from utils.helpers import generate_random_graph


def plot_experiment(ax, graph, parameter, values, xlabel):
    baseline = {
        "number_of_ants": 5,
        "alpha": 0.2,
        "beta": 0.2,
        "evaporation_rate": 0.5,
        "max_iterations": 100,
    }

    means = []
    medians = []
    deviations = []

    for value in values:
        settings = {**baseline, parameter: value}
        distances = []

        for seed in range(1, 31):
            colony = AntColony(graph, **settings, seed=seed)
            while not colony.is_finished():
                colony.step()
            distances.append(colony.best_distance)

        means.append(mean(distances))
        medians.append(median(distances))
        deviations.append(stdev(distances))
        print(f"{parameter} = {value:g} | median = {medians[-1]:.1f}")

    ax.plot(values, means, "o-", label="Mean")
    ax.plot(values, medians, "s--", label="Median")
    ax.fill_between(
        values,
        [m - s for m, s in zip(means, deviations)],
        [m + s for m, s in zip(means, deviations)],
        alpha=0.2,
        label="Mean ± 1 standard deviation",
    )
    ax.set_xlabel(xlabel)
    ax.set_xticks(values, [f"{value:g}" for value in values])
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=8)


def main():
    graph = generate_random_graph(10, 800, 600, seed=42)
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    plot_experiment(left, graph, "number_of_ants", list(range(1, 11)), "Number of ants")
    plot_experiment(
        right, graph, "alpha",
        [0, 0.2, 0.4, 0.6, 0.8, 1, 1.25, 1.5, 1.75, 2],
        "Alpha (pheromone weight)",
    )

    left.set_title("Fixed alpha = 0.2")
    right.set_title("Fixed number of ants = 5")
    left.set_ylabel("Best tour length after 100 iterations")
    fig.suptitle(
        "Same 10-city map (seed 42) · 30 runs per setting · beta = 0.2 · evaporation = 0.5"
    )
    fig.tight_layout()
    fig.savefig("parameter_comparison.png", dpi=200)
    print("Graphique créé : parameter_comparison.png")


if __name__ == "__main__":
    main()