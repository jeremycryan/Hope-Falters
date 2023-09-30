import time

import pygame
import asyncio

from grid import Grid


class Frame:
    def __init__(self, game):
        self.game = game
        self.done = False

    def load(self):
        pass

    def update(self, dt, events):
        pass

    def draw(self, surface, offset=(0, 0)):
        surface.fill((0, 0, 0))

    def next_frame(self):
        return Frame(self.game)


class LevelFrame(Frame):
    def __init__(self, game):
        super().__init__(game)
        self.grid = Grid("levels/level_3.txt")

    def draw(self, surface, offset=(0, 0)):
        super().draw(surface, offset)
        self.grid.draw(surface, offset)

    def update(self, dt, events):
        super().update(dt, events)
        self.grid.update(dt, events)