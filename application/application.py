from typing import Callable

import pygame

from application.algorithm_run import X_MODES
from application.session import Session, ViewState
from display.display import Display

SPEEDS = [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 5000]


class Application:
    """Runs one or more algorithms in lockstep: every frame each algorithm does the same
    number of steps, so their progress can be compared step by step.

    Keys: Space pause/resume, N (or Right) one step while paused, +/- speed,
    X switch x-axis (step / edge evaluations / CPU time), L log x-axis, R new random graph, Esc quit.
    """

    def __init__(self, create_session: Callable[[int | None, int | None], Session], display: Display,
                 fps: int, steps_per_frame: float, graph_seed: int | None, algorithm_seed: int | None,
                 on_session_end: Callable[[Session], None] | None = None):
        self.create_session = create_session
        self.on_session_end = on_session_end
        self.display = display
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.view = ViewState(speed=steps_per_frame)
        self.session = create_session(graph_seed, algorithm_seed)
        self._is_running = True
        self._step_budget = 0.0  # allows less than one step per frame

    def run(self):
        while self._is_running:
            self.handle_events()

            if not self.view.paused:
                self._step_budget += self.view.speed
                steps = int(self._step_budget)
                self._step_budget -= steps
                self.step_all(steps)

            self.display.draw(self.session, self.view)
            self.clock.tick(self.fps)

        self.end_session()
        self.display.close()

    def step_all(self, steps: int):
        for _ in range(steps):
            for run in self.session.runs:
                run.step()

    def end_session(self):
        if self.on_session_end is not None:
            self.on_session_end(self.session)

    def change_speed(self, direction: int):
        faster = [speed for speed in SPEEDS if speed > self.view.speed]
        slower = [speed for speed in SPEEDS if speed < self.view.speed]
        if direction > 0 and faster:
            self.view.speed = faster[0]
        elif direction < 0 and slower:
            self.view.speed = slower[-1]

    def restart(self):
        """New graph and new ants with fresh random seeds."""
        self.end_session()
        self.session = self.create_session(None, None)
        self._step_budget = 0.0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._is_running = False
            elif event.type == pygame.KEYDOWN:
                key = event.key
                if key == pygame.K_ESCAPE:
                    self._is_running = False
                elif key == pygame.K_SPACE:
                    self.view.paused = not self.view.paused
                elif key in (pygame.K_n, pygame.K_RIGHT):
                    self.view.paused = True
                    self.step_all(1)
                elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS, pygame.K_UP):
                    self.change_speed(+1)
                elif key in (pygame.K_MINUS, pygame.K_KP_MINUS, pygame.K_DOWN):
                    self.change_speed(-1)
                elif key == pygame.K_x:
                    index = X_MODES.index(self.view.x_mode)
                    self.view.x_mode = X_MODES[(index + 1) % len(X_MODES)]
                elif key == pygame.K_l:
                    self.view.log_x = not self.view.log_x
                elif key == pygame.K_r:
                    self.restart()
