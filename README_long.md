# anTSP

Solving the Travelling Salesman Problem with **Ant Colony Optimization (ACO)** and comparing it with
**exact algorithms** (backtracking / branch and bound, Held-Karp dynamic programming).

The project has two parts:

1. **Visualizer** (`anTSP.py`): shows the algorithms side by side on the same graph, step by step,
   with a live chart of the best tour length.
2. **Experiments** (`experiments/`): run all algorithms on many seeded random graphs without a window,
   save CSV files, and make the figures for the presentation.

## Setup

```
pip install -r requirements.txt
```

## 1. Visualizer

```
python anTSP.py                                   # ACO vs backtracking (default)
python anTSP.py -a all -x 1900                    # ACO, backtracking and Held-Karp
python anTSP.py -n 12 -s 20                       # 12 nodes, 20 steps per frame
python anTSP.py --aco-variant mmas --two-opt      # MAX-MIN Ant System with 2-opt
python anTSP.py --initial-tour aco                # hybrid: ACO result is the start bound of backtracking
python anTSP.py --help                            # all options
```

**Keys:** `Space` pause, `N` / `→` one step, `+` / `-` speed (also below 1 step per frame),
`X` switches the chart x-axis (steps, edge evaluations, CPU time), `L` log x-axis,
`R` new random graph, `Esc` quit. Hover over the chart to read the values.

When the graph is small enough (13 nodes or fewer by default, see `--optimum`), the optimal length is
computed first. The chart then shows it as a dashed line, and each panel shows the gap to it.

### Reproducing a run

Every run uses two seeds: the **graph seed** (`--seed`) and the **algorithm seed** (`--algo-seed`, used
by the ants). If you don't give them, random seeds are chosen. Either way, the seeds are:

* printed at start together with the full command to reproduce the run,
* shown at the bottom of the window,
* saved with all settings and results in `results/runs/run_<date>_g<seed>.json` when the window
  closes (or `R` is pressed).

```
python anTSP.py --seed 42 --algo-seed 7           # same graph, same ants, same result
python anTSP.py --replay results/runs/run_....json
```

The graph also depends on the window size (`-x`, `-y`) and the number of algorithms, because the nodes
are placed inside the panel. Replay stores all of this.

## 2. Experiments (CSV + figures)

```
python -m experiments.run_experiments --preset quick    # ~3 minutes, to try it out
python -m experiments.run_experiments                   # full experiment (~25 minutes)
python -m experiments.run_experiments --experiment sensitivity   # only the parameter study
python -m experiments.run_experiments --add-to results/experiments/full --experiment sensitivity  # redo one part in an existing folder
python -m experiments.plot_results results/experiments/<name>    # remake the figures
```

Options: `--sizes 5 10 15`, `--graphs 10`, `--repeats 5`, `--time-limit 60`, `--seed 3`, `--name my_run`.
You can stop it with `Ctrl+C` at any time. The rows written so far are kept.

Output in `results/experiments/<name>/`:

| file | content |
|---|---|
| `config.json` | all settings, base seed, git commit. Repeat with `--config config.json` |
| `results.csv` | one row per run: algorithm, n, seeds, best length, gap to optimum, steps, edge evaluations, CPU time |
| `convergence.csv` | best length after every improvement, per run (`run_id` links it to `results.csv`) |
| `summary.csv` | mean / std / median per algorithm and n |
| `plots/*.png`, `*.svg` | figures for the slides |

Any graph from the experiment can be opened in the visualizer:
`python anTSP.py -n <n> --seed <graph_seed> --algo-seed <algo_seed>`. The experiments place the
nodes in the same area as the default 2-panel window.

### What is measured

* **Gap to optimum** = (length − optimal length) / optimal length. The optimum comes from the exact
  algorithms, and all of them must agree (this is checked). For sizes where no exact algorithm
  finished, the reference is the best tour any algorithm found. The figures mark this.
* **Edge evaluations**: how many times an algorithm looked at an edge length. This measures work
  independently of the machine. A "step" means very different things (one ant move vs. one
  backtracking decision), so steps are not used to compare work.
* **CPU time** of the algorithm itself (drawing is not included).
* Exact algorithms are stopped after a time limit. After a timeout they are not run on larger n.

### Figures

| figure | question it answers |
|---|---|
| `01_runtime_vs_n` | How does runtime grow with n? (exact: exponential, ACO: polynomial) |
| `02_work_vs_n` | Same, measured in edge evaluations (independent of the machine) |
| `03_exact_algorithms` | How much do pruning, symmetry breaking and a start tour help backtracking? |
| `04_aco_gap_vs_n` | How far from the optimum is ACO? (per variant) |
| `05_aco_optimal_rate` | How often does ACO find the exact optimum? |
| `06_convergence_n*` | Best-so-far vs. work: ACO finds good tours early, exact algorithms need longer to *prove* optimality |
| `07_tradeoff` | Time and quality of every algorithm at the largest size solved exactly |
| `08–10_sensitivity_*` | Effect of α/β, evaporation ρ and the number of ants (Ant System, n = 40, gap to the best known tour) |

## Algorithms

**Ant colony** (`algorithms/ant_colony.py`), one step = every ant moves one node:

* variants: Ant System (`as`), Elitist AS (`elitist`), MAX-MIN AS (`mmas`, pheromone limits τmin/τmax,
  only the iteration-best ant deposits)
* τ₀ = m / C_nn (MMAS: 1 / (ρ·C_nn)), where C_nn is the nearest-neighbour tour length
* optional 2-opt local search on every ant tour (`--two-opt`)
* deposit after the tour (classic) or on every move (`--deposit step`)
* optional stop after k iterations without improvement (`--stagnation k`)

**Backtracking** (`algorithms/backtracking.py`), one step = one decision, always returns the optimum:

* `--bound none | simple | mst`: no pruning; prune if the path is already too long; prune if path +
  minimum spanning tree of the rest is too long (a valid lower bound)
* symmetry breaking: a tour and its reverse are the same, so only one direction is searched
* `--initial-tour nn | aco`: start with a known tour as the upper bound

**Held-Karp** (`algorithms/held_karp.py`): exact dynamic programming, O(n²·2ⁿ), one step = one subset.

## Project structure

```
anTSP.py                  command line + visualizer entry point
algorithms/               ACO, backtracking, Held-Karp (+ common Algorithm interface)
application/              main loop, run statistics (AlgorithmRun), session
display/                  renderers; theme.py holds all shared colors/fonts
experiments/              headless experiments and plotting
graph/, utils/            graph with a distance matrix, graph generation, TSP helpers (2-opt, MST, NN tour)
tests/                    python -m unittest discover tests
```

## Tests

```
python -m unittest discover tests
```

The tests check every backtracking variant and Held-Karp against brute force, check that ACO tours are
valid and reproducible from the seed, and test the helpers.
