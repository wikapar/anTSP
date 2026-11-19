import csv
from statistics import median

import matplotlib.pyplot as plt


distances_by_alpha = {}

with open("results_alpha.csv", newline="", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        alpha = float(row["alpha"])
        distance = float(row["best_distance"])
        distances_by_alpha.setdefault(alpha, []).append(distance)

alpha_values = sorted(distances_by_alpha)
fig, ax = plt.subplots(figsize=(7, 4))

for position, alpha in enumerate(alpha_values):
    distances = distances_by_alpha[alpha]

    # Décale les points pour rendre visibles les essais de même distance.
    offsets = [(i - (len(distances) - 1) / 2) * 0.06 for i in range(len(distances))]
    ax.scatter(
        [position + offset for offset in offsets],
        distances,
        color="tab:blue",
        label="Individual run" if position == 0 else None,
    )
    ax.scatter(
        position,
        median(distances),
        color="tab:orange",
        marker="_",
        s=350,
        label="Median" if position == 0 else None,
    )

ax.set_xticks(range(len(alpha_values)), [f"{alpha:g}" for alpha in alpha_values])
ax.set_xlabel("Alpha (pheromone weight)")
ax.set_ylabel("Best tour length")
ax.set_title("Best tour length after 100 iterations (5 ants)")
ax.grid(axis="y", alpha=0.25)
ax.legend()

fig.tight_layout()
fig.savefig("alpha_results.png", dpi=200)
print("Graphique créé : alpha_results.png")