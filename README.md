## Install

Python 3.10 or newer.

```
pip install -r requirements.txt
```

## Run the visualizer

```
python anTSP.py                    # ants vs. backtracking on a random map
python anTSP.py -a all -n 12       # all algorithms, 12 cities
python anTSP.py --help             # all options
```

Keys: `Space` pause, `+` / `-` speed, `R` new map, `Esc` quit.

## Run the experiments

```
python -m experiments.run_experiments --preset quick   # about 3 minutes
python -m experiments.run_experiments                  # full run, about 25 minutes
```

Results (CSV files and plots) are saved in `results/experiments/<name>/`.

## Tests

```
python -m unittest discover tests
```
