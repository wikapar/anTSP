import pygame

from display import display
from display.display import Display
from simulation.simulation import Simulation


class Application:
    def __init__(self, simulation: Simulation, width: int, height: int, fps: int, steps_per_frame: int):
        self.simulation = simulation
        self.display = Display(width, height)
        self.clock = pygame.time.Clock()
        self.fps = fps
        self._is_running = True
        self.steps_per_frame = steps_per_frame

    def run(self):
        while self._is_running:
            self.handle_events()
            for _ in range(self.steps_per_frame):
                self.simulation.step()

            self.display.clear()
            self.display.draw_graph(self.simulation.graph)
            self.display.update()
            self.clock.tick(self.fps)

        pygame.quit()


    def handle_events(self):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._is_running = False