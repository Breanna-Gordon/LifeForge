import pygame

pygame.font.init()

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GREY = (220, 220, 220)
DARK_GREY = (60, 60, 60)
GREEN = (70, 160, 90)
RED = (190, 70, 70)

font = pygame.font.SysFont("arial", 24)
small_font = pygame.font.SysFont("arial", 18)
title_font = pygame.font.SysFont("arial", 42, bold=True)

def draw_text(screen, text, selected_font, colour, x, y, centre=False):
    surface = selected_font.render(str(text), True, colour)
    rect = surface.get_rect()
    if centre:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)
