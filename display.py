import pygame
import os


WHITE = 255, 255, 255
RED = 255, 0, 0
GREEN = 0, 255, 0
BLUE = 0, 0, 255
YELLOW = 255, 255, 0
PINK = 255, 192, 203
BLACK = 0, 0, 0


class Screen(object):
    def __init__(self, width=320, height=240, on_tft=False):
        if on_tft:
            os.putenv('SDL_FBDEV', '/dev/fb1')
            os.putenv('SDL_VIDEODRIVER', 'fbcon')
            os.putenv('SDL_MOUSEDRV', 'TSLIB')
            os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.mouse.set_visible(not on_tft)
        self.clock = pygame.time.Clock()

    def clear(self):
        self.screen.fill(BLACK)

    def render_circle(self, center, radius, color):
        pygame.draw.circle(self.screen, color, center, radius, 0)

    def render_polygon(self, points, color, width=0):
        pygame.draw.polygon(self.screen, color, points, width)

    def render_text(self, text_pos, font, color):
        text_font = pygame.font.Font(None, font)
        for text, pos in text_pos.items():
            text_surface = text_font.render(text, True, color)
            self.screen.blit(text_surface, text_surface.get_rect(center=pos))

    def load_music(self, music_path):
        pygame.mixer.init()
        pygame.mixer.music.load(music_path)

    def play_music(self):
        pygame.mixer.music.play()

    def tick(self, frame_rate):
        self.clock.tick(frame_rate)

    @classmethod
    def display(cls):
        pygame.display.flip()

    @classmethod
    def get_click_pos(cls):
        return [pygame.mouse.get_pos() for event in pygame.event.get()
                if event.type is pygame.MOUSEBUTTONUP]
