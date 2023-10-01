import math
import time
import random

import pygame
import asyncio
import constants as c
from LevelFileManager import LevelFileManager

from grid import Grid
from image_manager import ImageManager
from pyracy.sprite_tools import Sprite, Animation

from Button import Button
from sound_manager import SoundManager


class Frame:
    STAR_MANAGER = None

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


class LevelSelect(Frame):
    def load(self):
        self.woman_sprite = Sprite(8, (0, 0))
        woman_animation = ImageManager.load("assets/images/human_test.png")
        animation = Animation(woman_animation, (4, 1), 4)
        self.woman_sprite.add_animation({"Idle": animation}, loop=True)
        self.woman_sprite.start_animation("Idle")
        self.clicked = False

        self.title_sprite = Sprite(8, (0, 0))
        title_animation = ImageManager.load("assets/images/title_animation.png")
        animation = Animation(title_animation, (3, 1), 3)
        self.title_sprite.add_animation({"Idle": animation}, loop=True)
        self.title_sprite.start_animation("Idle")

        self.title_yoff = 0
        self.title_speed = 0
        self.since_click = 0
        self.flip = SoundManager.load("assets/sound/flip.wav")

        self.dark = pygame.Surface(c.WINDOW_SIZE)
        self.dark.fill((c.BLACK))
        self.dark_alpha = 255

        self.whoosh = SoundManager.load("assets/sound/whoosh.wav")
        self.whoosh.set_volume(0.8)

        self.buttons = []
        self.generate_buttons()
        print(self.buttons)

    def generate_buttons(self):
        spacing = 200
        xoff = 150
        x_left = c.CENTER_X - spacing + xoff
        x_right = c.CENTER_X + spacing + xoff
        y = 200



        for i,level in enumerate(c.LEVELS):
            x = x_left if i%2==0 else x_right
            surf = pygame.Surface((300, 55))
            surf.fill(c.BLACK)
            enabled = LevelFileManager.level_has_been_beat(i) or i==0
            with open(f"levels/{level}") as f:
                text = f.readline().strip()


            hovered = ImageManager.load("assets/images/level_hovered.png")



            button = Button(surf,(x, y),text,self.start_level,hover_surf=hovered,click_surf=None,disabled_surf=None,enabled=enabled,grow_percent=0,pulse=False,on_click_args=(i,))
            self.buttons.append(button)
            if i%2 != 0:
                y += 75

    def start_level(self, level):
        self.game.active_level = level
        self.done = True
        self.flip.play()

    def update(self, dt, events):
        self.woman_sprite.update(dt, events)
        self.title_sprite.update(dt, events)

        if self.clicked:
            self.since_click += dt
            self.title_yoff = self.since_click * 600 - self.since_click**2 * 6000

        if self.title_yoff < -c.WINDOW_HEIGHT:
            self.done = True
            self.flip.play()

        self.dark_alpha -= 800*dt

        for button in self.buttons:
            button.update(dt, events)

    def draw(self, surface, offset=(0, 0)):
        super().draw(surface, offset)
        woman = self.woman_sprite.get_image().copy()

        self.dark.set_alpha(self.dark_alpha)
        surface.blit(self.dark, (0, 0))

        tint = woman.copy()
        tint.fill(c.GRAY_BLUE)
        woman.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
        surface.blit(woman, (0, 0))

        for button in self.buttons:
            button.draw(surface, *offset)


        xoff = 150
        y = 60
        level_select = ImageManager.load("assets/images/select_a_level.png")
        x = c.CENTER_X + xoff - level_select.get_width()//2
        surface.blit(level_select, (x, y))

    def next_frame(self):
        return LevelFrame(self.game)


class TitleFrame(Frame):
    def load(self):
        self.woman_sprite = Sprite(8, (0, 0))
        woman_animation = ImageManager.load("assets/images/human_test.png")
        animation = Animation(woman_animation, (4, 1), 4)
        self.woman_sprite.add_animation({"Idle": animation}, loop=True)
        self.woman_sprite.start_animation("Idle")
        self.clicked = False

        self.title_sprite = Sprite(8, (0, 0))
        title_animation = ImageManager.load("assets/images/title_animation.png")
        animation = Animation(title_animation, (3, 1), 3)
        self.title_sprite.add_animation({"Idle": animation}, loop=True)
        self.title_sprite.start_animation("Idle")

        self.title_yoff = 0
        self.title_speed = 0
        self.since_click = 0
        self.flip = SoundManager.load("assets/sound/flip.wav")

        self.dark = pygame.Surface(c.WINDOW_SIZE)
        self.dark.fill((c.BLACK))
        self.dark_alpha = 255

        self.whoosh = SoundManager.load("assets/sound/whoosh.wav")
        self.whoosh.set_volume(0.8)

    def update(self, dt, events):
        self.woman_sprite.update(dt, events)
        self.title_sprite.update(dt, events)

        if self.clicked:
            self.since_click += dt
            self.title_yoff = self.since_click * 600 - self.since_click**2 * 6000

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.click()

        if self.title_yoff < -c.WINDOW_HEIGHT:
            self.done = True
            self.flip.play()

        self.dark_alpha -= 800*dt

    def click(self):
        if self.dark_alpha> 0:
            return
        self.clicked = True
        self.whoosh.play()

    def draw(self, surface, offset=(0, 0)):
        super().draw(surface, offset)
        woman = self.woman_sprite.get_image().copy()

        tint = woman.copy()
        tint.fill(c.GRAY_BLUE)
        woman.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
        surface.blit(woman, (0, 0))

        title = self.title_sprite.get_image()
        surface.blit(title, (0, self.title_yoff))

        self.dark.set_alpha(self.dark_alpha)
        surface.blit(self.dark, (0, 0))

    def next_frame(self):
        return LevelSelect(self.game)



class LevelFrame(Frame):
    HINT_SHOWING = False

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
        hint_button_disabled = ImageManager.load("assets/images/hint_button_disabled.png")
        self.hint_button = Button(hint_button_surf, (c.WINDOW_WIDTH-68, c.WINDOW_HEIGHT*0.32),"",self.hint,hint_button_hover,pulse=False,disabled_surf=hint_button_disabled)

        self.hint_surf = ImageManager.load_copy("assets/images/hint_frame.png")
        self.hint_font = pygame.font.Font("assets/fonts/Rudiment.ttf",28)
        self.process_hint_surf()

        self.hint_showing = 0
        self.should_show_hint = False
        if LevelFrame.HINT_SHOWING and self.game.just_reset:
            self.hint()
            self.hint_showing = 1
        else:
            LevelFrame.HINT_SHOWING= False

        self.flip = SoundManager.load("assets/sound/flip.wav")

        LevelFrame.STAR_MANAGER = StarManager()
        for i in range(50):
            LevelFrame.STAR_MANAGER.update(0.2, [])

    def draw(self, surface, offset=(0, 0)):
        super().draw(surface, offset)

        offset = self.update_pos_to_shake(offset)

        self.grid.draw(surface, offset)
        self.reset_button.draw(surface, *offset)
        self.hint_button.draw(surface, *offset)
        LevelFrame.STAR_MANAGER.draw(surface, offset)

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

        y_start = -self.hint_surf.get_height() - 100
        y_scale = self.hint_surf.get_height() + 50 + 100
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
        LevelFrame.HINT_SHOWING = True


    def reset(self):
        if not self.grid.ready_for_next() and not self.grid.won:
            self.switching_out = True
            self.flip.play()

    def update(self, dt, events):
        super().update(dt, events)
        self.age += dt
        self.since_shake += dt
        self.grid.update(dt, events)
        if self.grid.ready_for_next() and not self.switching_out:
            self.switching_out = True
            self.game.active_level += 1
            self.flip.play()

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

        if self.switching_out or self.grid.won:
            LevelFrame.STAR_MANAGER.age_quickly = True

        self.woman_sprite.update(dt, events)

        self.reset_button.update(dt, events)
        self.hint_button.update(dt, events)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()

        if self.should_show_hint and self.hint_showing < 1 and not self.switching_out:
            self.hint_showing += dt * 3
            if self.hint_showing > 1:
                self.hint_showing = 1
        if (not self.should_show_hint and self.hint_showing > 0) or (self.switching_out and self.grid.won):
            self.hint_showing -= dt * 3

        LevelFrame.STAR_MANAGER.update(dt, events)


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


class StarManager:

    def __init__(self):
        self.since_spawn = 0
        self.stars = []
        self.age_quickly = False

    def update(self, dt, events):
        self.since_spawn += dt

        new_stars = []
        for star in self.stars[:]:
            star.update(dt, events)
            if self.age_quickly:
                star.age += dt*8
            if star.through()<1:
                new_stars.append(star)
        rate = 0.2
        if self.since_spawn > rate and not self.age_quickly:
            new_stars.append(Star())
            self.since_spawn -= rate
        self.stars = new_stars

    def draw(self, surface, offset):
        for star in self.stars:
            star.draw(surface, offset)


class Star:

    SIZES = [c.MEDIUM, c.SMALL]
    SHADE = {}

    def __init__(self):
        size = random.choice(self.SIZES)
        if size==c.SMALL:
            surf = ImageManager.load_copy("assets/images/small_star.png")
            self.x_velocity = random.random() * -30 -30
        elif size == c.MEDIUM:
            surf = ImageManager.load_copy("assets/images/medium_star.png")
            self.x_velocity = random.random() * -50 - 50
        else:
            surf = ImageManager.load_copy("assets/images/large_star.png")
            self.x_velocity = random.random() * -25 - 25
        self.x_velocity *= 0.7

        self.surf = surf
        self.angle = random.random()*360

        self.spin = random.random()*20 + 10

        self.x = c.WINDOW_WIDTH - 130
        off = 0.06
        self.y = (random.random()*off + 0.5 - off/2) * c.WINDOW_HEIGHT

        self.destroyed = False
        self.age = 0
        self.duration = abs(200/self.x_velocity)

        if size not in self.SHADE:
            shade = self.surf.copy()
            shade.fill((0, 0, 0))
            Star.SHADE[size] = shade
        self.size = size

    def update(self, dt, events):
        self.age += dt
        self.angle += self.spin*dt
        self.x += self.x_velocity*dt


    def through(self):
        through = self.age / self.duration
        if through < 0:
            return 0
        if through > 1:
            return 1
        return through

    def get_alpha(self):
        return min(70 - self.through()*70, self.through()*1000)

    def get_scale(self):
        return 1.2 - self.through()*0.4


    def draw(self, surface, offset=(0, 0)):
        surf = self.surf.copy()
        Star.SHADE[self.size].set_alpha(255 - self.get_alpha())
        surf.blit(Star.SHADE[self.size], (0, 0))
        surf = pygame.transform.scale(surf, (surf.get_width()*self.get_scale(), surf.get_height()*self.get_scale()))
        surf = pygame.transform.rotate(surf, self.angle)
        x = offset[0] + self.x - surf.get_width()//2
        y = offset[1] + self.y - surf.get_height()//2
        surface.blit(surf, (x, y), special_flags=pygame.BLEND_ADD)