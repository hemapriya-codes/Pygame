"""Moon Royale - entry point.  Run with:  python main.py"""
import sys
import pygame

from core import config as C
from core.progression import Profile
from ui import theme
from ui.screens import MenuScreen


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Moon Royale")
        self.surface = pygame.display.set_mode((C.SCREEN_W, C.SCREEN_H))
        self.clock = pygame.time.Clock()
        theme.init_fonts()
        self.profile = Profile.load()
        self.running = True
        self.screen = MenuScreen(self)

    def go(self, screen):
        self.screen = screen

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            dt = self.clock.tick(C.FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                else:
                    self.screen.handle(e)
            self.screen.update(dt)
            self.screen.draw(self.surface)
            pygame.display.flip()
        self.profile.save()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    App().run()
