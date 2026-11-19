import csv
from statistics import median

import matplotlib.pyplot as plt


distances_by_ant_count = {}

with open("results.csv", newline="", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        ant_count = int(row["number_of_ants"])
        distance = float(row["best_distance"])
        distances_by_ant_count.setdefault(ant_count, []).append(distance)

fig, ax = plt.subplots(figsize=(7, 4))
ant_counts = sorted(distances_by_ant_count)

for position, ant_count in enumerate(ant_counts):
    distances = distances_by_ant_count[ant_count]

    # Décale légèrement les points pour voir les essais de même distance.
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

ax.set_xticks(range(len(ant_counts)), ant_counts)
ax.set_xlabel("Number of ants")
ax.set_ylabel("Best tour length")
ax.set_title("Best tour length after 100 iterations")
ax.grid(axis="y", alpha=0.25)
ax.legend()

fig.tight_layout()
fig.savefig("ant_results.png", dpi=200)
print("Graphique créé : ant_results.png")