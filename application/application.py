import pygame

from algorithms.algorithm import Algorithm
from display.display import Display


class Application:
    def __init__(self, algorithm: Algorithm, display: Display, fps: int, steps_per_frame: int):
        self.algorithm = algorithm
        self.display = display
        self.clock = pygame.time.Clock()
        self.fps = fps
        self._is_running = True
        self.steps_per_frame = steps_per_frame

    def run(self):
        while self._is_running:
            self.handle_events()

            for _ in range(self.steps_per_frame):
                if not self.algorithm.is_finished():
                    self.algorithm.step()

            self.display.draw(self.algorithm)

            self.clock.tick(self.fps)

        self.display.close()


    def handle_events(self):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._is_running = False