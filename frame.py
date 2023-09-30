import math
import time

import pygame
import asyncio
import constants as c

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
        self.grid = Grid(c.LEVELS[self.game.active_level], self)
        self.shake_amp = 0
        self.since_shake = 999

    def draw(self, surface, offset=(0, 0)):
        super().draw(surface, offset)

        offset = self.update_pos_to_shake(offset)

        self.grid.draw(surface, offset)

    def update(self, dt, events):
        super().update(dt, events)
        self.since_shake += dt
        self.grid.update(dt, events)
        if self.grid.ready_for_next() and not self.done:
            self.done = True
            self.game.active_level += 1

        self.shake_amp -= (self.shake_amp*4 + 5)*dt
        if self.shake_amp < 1:
            self.shake_amp = 0

    def next_frame(self):
        return LevelFrame(self.game)

    def shake(self, amt=10):
        self.since_shake = 0
        self.shake_amp = amt
        pass

    def update_pos_to_shake(self, pos):
        xoff = math.cos(self.since_shake*25)*self.shake_amp
        yoff = math.cos(self.since_shake*25)*self.shake_amp
        return pos[0] + xoff, pos[1]+yoff
