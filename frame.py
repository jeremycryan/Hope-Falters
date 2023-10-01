import math
import time

import pygame
import asyncio
import constants as c
from LevelFileManager import LevelFileManager

from grid import Grid
from image_manager import ImageManager
from pyracy.sprite_tools import Sprite, Animation

from Button import Button


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
        self.grid = Grid(c.LEVELS[self.game.active_level], self, offset = (130, 0))
        self.shake_amp = 0
        self.since_shake = 999
        self.delayed_shakes = []
        self.switching_out = False
        self.since_switching_out = 0
        self.wiper = ImageManager.load("assets/images/wiper.png")
        self.left_wiper = pygame.transform.flip(self.wiper, True, True)
        self.age = 0

        self.woman_sprite = Sprite(8, (0, 0))
        woman_animation = ImageManager.load("assets/images/human_test.png")
        animation = Animation(woman_animation, (4, 1), 4)
        self.woman_sprite.add_animation({"Idle":animation},loop=True)
        self.woman_sprite.start_animation("Idle")

        reset_button_surf = ImageManager.load("assets/images/reset_button.png")
        reset_button_surf_hover = ImageManager.load("assets/images/reset_button_hover.png")
        self.reset_button = Button(reset_button_surf,(c.WINDOW_WIDTH-68, c.WINDOW_HEIGHT*0.18),"",self.reset,reset_button_surf_hover,grow_percent=5,pulse=False)

        hint_button_surf = ImageManager.load("assets/images/hint_button.png")
        hint_button_hover = ImageManager.load("assets/images/hint_button_hover.png")
        self.hint_button = Button(hint_button_surf, (c.WINDOW_WIDTH-68, c.WINDOW_HEIGHT*0.32),"",self.hint,hint_button_hover,pulse=False)

        self.hint_surf = ImageManager.load_copy("assets/images/hint_frame.png")
        self.hint_font = pygame.font.Font("assets/fonts/Rudiment.ttf",28)
        self.process_hint_surf()

        self.hint_showing = 0
        self.should_show_hint = False

    def draw(self, surface, offset=(0, 0)):
        super().draw(surface, offset)

        offset = self.update_pos_to_shake(offset)

        self.grid.draw(surface, offset)
        self.reset_button.draw(surface, *offset)
        self.hint_button.draw(surface, *offset)

        wipe_out = 0.5
        if self.since_switching_out > 0:
            through = self.since_switching_out/wipe_out
            x_left = c.WINDOW_WIDTH - (c.WINDOW_WIDTH + self.wiper.get_width())*through
            surface.blit(self.wiper, (x_left, 0))
            if x_left < c.WINDOW_WIDTH - self.wiper.get_width():
                pygame.draw.rect(surface, c.BLACK, (x_left + self.wiper.get_width(), 0, c.WINDOW_WIDTH - x_left - self.wiper.get_width(), c.WINDOW_HEIGHT),0)
            if through > 1:
                if self.grid.ready_for_next():
                    LevelFileManager.beat_level(self.game.active_level)
                self.done = True

        wipe_in = 0.5
        if self.age < wipe_in:
            through = (self.age)/wipe_in
            x_left = c.WINDOW_WIDTH - (c.WINDOW_WIDTH + self.left_wiper.get_width())*through
            surface.blit(self.left_wiper, (x_left, 0))
            if x_left > 0:
                pygame.draw.rect(surface, c.BLACK, (0, 0, x_left, c.WINDOW_HEIGHT))

        surf = self.woman_sprite.get_image()
        tint = surf.copy()
        tint.fill(c.GRAY_BLUE)
        if self.grid.won:
            tint2 = tint.copy()
            tint2.fill(c.LIGHT_YELLOW)
            alpha=self.grid.flash_alpha
            tint2.set_alpha(alpha)
            tint.blit(tint2, (0, 0))

        surface.blit(surf, (offset[0], offset[1]))
        surface.blit(tint, (offset[0], offset[1]), special_flags=pygame.BLEND_MULT)

        y_start = -self.hint_surf.get_height()
        y_scale = self.hint_surf.get_height() + 50
        y = (-(self.hint_showing - 1)**2 + 1)
        y = y*y_scale + y_start
        surface.blit(self.hint_surf, (30 + offset[0], y + offset[1]))

    def process_hint_surf(self):
        cx = self.hint_surf.get_width()//2
        cy = self.hint_surf.get_height()//2
        if not self.grid.hints:
            y = 75
            for hint_text in ["No hint for this level.","You can do it!"]:
                surface = self.hint_font.render(hint_text, True, c.GRAY_BLUE)
                self.hint_surf.blit(surface, (cx - surface.get_width() // 2, y))
                y += 32
            return
        hint_text = "These words may be helpful:"
        surface = self.hint_font.render(hint_text, True, c.GRAY_BLUE)
        self.hint_surf.blit(surface, (cx - surface.get_width()//2, 45))
        spacing = 32
        start_y = 85
        if len(self.grid.hints) > 3:
            spacing = 28
            start_y = 80
        y = start_y
        for word in self.grid.hints:
            text = word.upper()
            surf = self.hint_font.render(text, True, c.LIGHT_YELLOW)
            self.hint_surf.blit(surf, (cx - surf.get_width()//2, y))
            y += spacing


    def hint(self):
        self.should_show_hint = True
        self.hint_button.disable()


    def reset(self):
        if not self.grid.ready_for_next() and not self.grid.won:
            self.switching_out = True

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
                if shake[2]:
                    shake[2].play()

        if self.switching_out:
            self.since_switching_out += dt

        self.woman_sprite.update(dt, events)

        self.reset_button.update(dt, events)
        self.hint_button.update(dt, events)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()

        if self.should_show_hint and self.hint_showing < 1:
            self.hint_showing += dt * 3
        if not self.should_show_hint and self.hint_showing > 0:
            self.hint_showing -= dt * 3




    def next_frame(self):
        return LevelFrame(self.game)

    def shake(self, amt=10, delay=0, sound=None):
        if not delay:
            self.since_shake = 0
            self.shake_amp = amt
            if sound:
                sound.play()
        else:
            self.delayed_shakes.append([amt, delay, sound])


    def update_pos_to_shake(self, pos):
        xoff = math.cos(self.since_shake*25)*self.shake_amp
        yoff = math.cos(self.since_shake*25)*self.shake_amp
        return pos[0] + xoff, pos[1]+yoff
