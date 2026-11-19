import pygame

from application.algorithm_run import AlgorithmRun
from display.display import Display


class Application:
    """Runs one or more algorithms in lockstep: every frame each algorithm does the same
    number of steps, so their progress can be compared step by step.
    Space pauses / resumes."""

    def __init__(self, runs: list[AlgorithmRun], display: Display, fps: int, steps_per_frame: int):
        self.runs = runs
        self.display = display
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.steps_per_frame = steps_per_frame
        self._is_running = True
        self._paused = False

    def run(self):
        while self._is_running:
            self.handle_events()

            if not self._paused:
                for _ in range(self.steps_per_frame):
                    for run in self.runs:
                        run.step()

            self.display.draw(self.runs, self._paused)
            self.clock.tick(self.fps)

        self.display.close()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._is_running = False
                elif event.key == pygame.K_SPACE:
                    self._paused = not self._paused
