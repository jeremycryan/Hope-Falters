import math
import time

import pygame
import asyncio
import constants as c

from grid import Grid
from image_manager import ImageManager


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
        self.grid = Grid(c.LEVELS[self.game.active_level], self, offset = (100, 0))
        self.shake_amp = 0
        self.since_shake = 999
        self.delayed_shakes = []
        self.switching_out = False
        self.since_switching_out = 0
        self.wiper = ImageManager.load("assets/images/wiper.png")
        self.left_wiper = pygame.transform.flip(self.wiper, True, True)
        self.age = 0

    def draw(self, surface, offset=(0, 0)):
        super().draw(surface, offset)

        offset = self.update_pos_to_shake(offset)

        self.grid.draw(surface, offset)

        wipe_out = 0.5
        if self.since_switching_out > 0:
            through = self.since_switching_out/wipe_out
            x_left = c.WINDOW_WIDTH - (c.WINDOW_WIDTH + self.wiper.get_width())*through
            surface.blit(self.wiper, (x_left, 0))
            if x_left < c.WINDOW_WIDTH - self.wiper.get_width():
                pygame.draw.rect(surface, c.BLACK, (x_left + self.wiper.get_width(), 0, c.WINDOW_WIDTH - x_left - self.wiper.get_width(), c.WINDOW_HEIGHT),0)
            if through > 1:
                self.done = True

        wipe_in = 0.5
        if self.age < wipe_in:
            through = (self.age)/wipe_in
            x_left = c.WINDOW_WIDTH - (c.WINDOW_WIDTH + self.left_wiper.get_width())*through
            surface.blit(self.left_wiper, (x_left, 0))
            if x_left > 0:
                pygame.draw.rect(surface, c.BLACK, (0, 0, x_left, c.WINDOW_HEIGHT))
            print(x_left)

    def update(self, dt, events):
        super().update(dt, events)
        self.age += dt
        self.since_shake += dt
        self.grid.update(dt, events)
        if self.grid.ready_for_next() and not self.switching_out:
            self.switching_out = True
            self.game.active_level += 1

        self.shake_amp -= (self.shake_amp*4 + 5)*dt
        if self.shake_amp < 1:
            self.shake_amp = 0

        for shake in self.delayed_shakes[:]:
            shake[1]-=dt
            if shake[1] <= 0:
                self.delayed_shakes.remove(shake)
                self.shake(shake[0])

        if self.switching_out:
            self.since_switching_out += dt

    def next_frame(self):
        return LevelFrame(self.game)

    def shake(self, amt=10, delay=0):
        if not delay:
            self.since_shake = 0
            self.shake_amp = amt
        else:
            self.delayed_shakes.append([amt, delay])


    def update_pos_to_shake(self, pos):
        xoff = math.cos(self.since_shake*25)*self.shake_amp
        yoff = math.cos(self.since_shake*25)*self.shake_amp
        return pos[0] + xoff, pos[1]+yoff
