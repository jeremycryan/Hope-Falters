import pygame

import constants as c
import frame as f
import sys

from LevelFileManager import LevelFileManager
from sound_manager import SoundManager
from image_manager import ImageManager
from word_manager import WordManager
import asyncio

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.set_num_channels(10)
        SoundManager.init()
        ImageManager.init()
        WordManager.init()
        LevelFileManager.init()
        self.screen = pygame.display.set_mode(c.WINDOW_SIZE)
        pygame.display.set_caption(c.CAPTION)
        self.clock = pygame.time.Clock()
        self.windowed = False
        self.clicked = False
        self.active_level = 0
        self.just_reset = False
        self.last_level = 0

        self.music_full = pygame.mixer.Sound("assets/sound/LD54.ogg")
        self.music_full.set_volume(0.3)
        self.music_lowpass = pygame.mixer.Sound("assets/sound/LD54_lowpass.ogg")
        self.music_lowpass.set_volume(0)
        self.music_full.play(-1)
        self.music_lowpass.play(-1)

        self.music_state = 1
        self.target_music_state = 1

        asyncio.run(self.main())


    def update_music_volumes(self, dt, events):
        self.music_full.set_volume(0.3*self.music_state)
        self.music_lowpass.set_volume(0.3*(1-self.music_state))
        if self.music_state > self.target_music_state:
            self.music_state -= 2*dt
            if self.music_state < 0:
                self.music_state = 0
        if self.music_state < self.target_music_state:
            self.music_state += 2*dt
            if self.music_state > 1:
                self.music_state = 1

    def raise_music(self):
        self.target_music_state = 1

    def lower_music(self):
        self.target_music_state = 0

    async def main(self):
        current_frame = f.TitleFrame(self)
        current_frame.load()

        self.clock.tick(60)

        while True:
            dt, events = self.get_events()
            await asyncio.sleep(0)
            if dt == 0:
                dt = 1/100000
            pygame.display.set_caption(f"{c.CAPTION} ({int(1/dt)} FPS)")
            if dt > 0.05:
                dt = 0.05
            current_frame.update(dt, events)
            self.update_music_volumes(dt, events)
            current_frame.draw(self.screen, (0, 0))
            pygame.display.flip()

            if current_frame.done:
                LevelFileManager.save()
                if self.last_level==self.active_level:
                    self.just_reset = True
                else:
                    self.just_reset = False

                current_frame = current_frame.next_frame()
                current_frame.load()


                self.last_level = self.active_level

    def get_events(self):
        dt = self.clock.tick(c.FRAMERATE)/1000

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F4:
                    pygame.display.toggle_fullscreen()


        return dt, events


if __name__=="__main__":
    Game()
