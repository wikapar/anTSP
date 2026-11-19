import pygame

from display import display
from display.display import Display
from simulation.simulation import Simulation


class Application:
    def __init__(self, simulation: Simulation, display: Display, fps: int, steps_per_frame: int):
        self.simulation = simulation
        self.display = display
        self.clock = pygame.time.Clock()
        self.fps = fps
        self._is_running = True
        self.steps_per_frame = steps_per_frame

    def run(self):
        while self._is_running:
            self.handle_events()

            for _ in range(self.steps_per_frame):
                if not self.simulation.algorithm.is_finished():
                    self.simulation.step()

            self.display.draw(self.simulation)

            self.clock.tick(self.fps)

        self.display.close()


    def handle_events(self):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._is_running = False