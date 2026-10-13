"""Shared fonts, colours and small widgets (Button, bars, text)."""
import pygame

WHITE = (240, 244, 255)
GREY = (140, 150, 170)
DARK = (14, 16, 30)
PANEL = (24, 28, 52)
ACCENT = (90, 200, 255)
RED = (235, 70, 70)
GREEN = (90, 220, 120)
YELLOW = (250, 210, 70)
BLUE = (80, 140, 255)
CYAN = (90, 230, 240)

FONTS = {}


def init_fonts():
    for name, size in (("s", 20), ("m", 28), ("l", 44), ("xl", 80)):
        FONTS[name] = pygame.font.Font(None, size)


def text(surf, s, pos, size="m", color=WHITE, center=False, right=False):
    img = FONTS[size].render(str(s), True, color)
    r = img.get_rect()
    if center:
        r.center = pos
    elif right:
        r.topright = pos
    else:
        r.topleft = pos
    surf.blit(img, r)
    return r


def bar(surf, rect, frac, color, label=None):
    x, y, w, h = rect
    pygame.draw.rect(surf, (10, 10, 20), rect, border_radius=4)
    frac = max(0.0, min(1.0, frac))
    if frac > 0:
        pygame.draw.rect(surf, color, (x, y, int(w * frac), h), border_radius=4)
    pygame.draw.rect(surf, (200, 210, 230), rect, 1, border_radius=4)
    if label:
        text(surf, label, (x + w // 2, y + h // 2), "s", WHITE, center=True)


class Button:
    def __init__(self, rect, label, callback, enabled=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.callback = callback
        self.enabled = enabled

    def handle(self, e):
        if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.enabled
                and self.rect.collidepoint(e.pos)):
            self.callback()
            return True
        return False

    def draw(self, surf):
        hover = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        col = (60, 90, 160) if hover else (38, 50, 96)
        if not self.enabled:
            col = (30, 32, 44)
        pygame.draw.rect(surf, col, self.rect, border_radius=8)
        pygame.draw.rect(surf, ACCENT if self.enabled else (70, 70, 80), self.rect, 2, border_radius=8)
        text(surf, self.label, self.rect.center, "m", WHITE if self.enabled else GREY, center=True)
