import math
import time
from bisect import bisect_right
from dataclasses import dataclass

from algorithms.algorithm import Algorithm


@dataclass
class Record:
    """Snapshot taken whenever the best tour improves."""
    step: int
    evaluations: int
    time: float  # CPU seconds spent inside step() so far
    best: float


X_MODES = ("step", "evaluations", "time")


class AlgorithmRun:
    """One algorithm + (optional) renderer + the statistics needed to compare it with other algorithms.
    Counts steps, edge evaluations and time the same way for every algorithm
    and records the best tour length every time it improves."""

    def __init__(self, algorithm: Algorithm, renderer=None, name: str | None = None):
        self.algorithm = algorithm
        self.renderer = renderer
        self.name = name or getattr(algorithm, "display_name", None) or getattr(renderer, "name", "Algorithm")
        self.steps = 0
        self.elapsed = 0.0
        self.history: list[Record] = []
        self.record_if_improved()  # e.g. backtracking that starts with a known tour

    @property
    def best_distance(self) -> float:
        return self.algorithm.best_distance

    @property
    def evaluations(self) -> int:
        return self.algorithm.edge_evaluations

    @property
    def best_found_at_step(self):
        return self.history[-1].step if self.history else None

    def is_finished(self) -> bool:
        return self.algorithm.is_finished()

    def record_if_improved(self):
        best = self.algorithm.best_distance
        if math.isfinite(best) and (not self.history or best < self.history[-1].best - 1e-9):
            self.history.append(Record(self.steps, self.evaluations, self.elapsed, best))

    def step(self):
        if self.algorithm.is_finished():
            return
        start = time.perf_counter()
        self.algorithm.step()
        self.elapsed += time.perf_counter() - start
        self.steps += 1
        self.record_if_improved()

    def run_to_end(self, time_limit: float | None = None) -> bool:
        """Headless: runs until finished or until the time limit (seconds). Returns True if finished."""
        while not self.algorithm.is_finished():
            for _ in range(500):
                self.step()
                if self.algorithm.is_finished():
                    return True
            if time_limit is not None and self.elapsed > time_limit:
                return False
        return True

    # ----- for the chart -----

    def current_x(self, mode: str) -> float:
        return {"step": self.steps, "evaluations": self.evaluations, "time": self.elapsed}[mode]

    @staticmethod
    def record_x(record: Record, mode: str) -> float:
        return {"step": record.step, "evaluations": record.evaluations, "time": record.time}[mode]

    def best_at(self, x: float, mode: str = "step"):
        """Best tour length that was known at the given x (None if no tour yet)."""
        xs = [self.record_x(record, mode) for record in self.history]
        index = bisect_right(xs, x) - 1
        return self.history[index].best if index >= 0 else None

    def best_at_step(self, step: int):
        return self.best_at(step, "step")

    def to_dict(self) -> dict:
        tour = self.algorithm.best_tour
        return {
            "name": self.name,
            "finished": self.is_finished(),
            "steps": self.steps,
            "edge_evaluations": self.evaluations,
            "cpu_seconds": round(self.elapsed, 4),
            "best_distance": self.best_distance if math.isfinite(self.best_distance) else None,
            "best_found_at_step": self.best_found_at_step,
            "best_tour": [node.node_id for node in tour] if tour else None,
            "history": [[r.step, r.evaluations, round(r.time, 4), r.best] for r in self.history],
        }
