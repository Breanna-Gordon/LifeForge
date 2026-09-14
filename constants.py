import pygame

pygame.font.init()

SCREEN_WIDTH = 900
# Taller than before — the character creator now has enough controls
# (skin tone, a hair colour wheel, more hairstyles, facial hair) that it
# needed the extra room to lay out cleanly without crowding.
SCREEN_HEIGHT = 700

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GREY = (225, 225, 230)
DARK_GREY = (70, 70, 78)
GREEN = (76, 175, 120)
RED = (215, 80, 80)
ACCENT = (255, 149, 66)

# Soft background tint per life stage — gives each era its own mood
STAGE_COLORS = {
    "Baby":        (255, 235, 240),
    "Childhood":   (224, 246, 228),
    "Teenage":     (232, 222, 248),
    "Young Adult": (255, 235, 205),
    "Adult":       (215, 232, 255),
    "Elderly":     (230, 230, 232),
}

# Fallback colours for stat icons when no image file is found
STAT_COLORS = {
    "physical": (230, 100, 90),
    "wealth":   (230, 180, 60),
    "mental":   (90, 140, 230),
    "social":   (160, 100, 220),
}

# Default hair colour before the player touches the colour wheel — hair
# colour itself is now freely pickable, not limited to a fixed swatch list.
DEFAULT_HAIR_COLOUR = (35, 28, 24)

HAIRSTYLES = ["Bald", "Buzzcut", "Short", "Long", "Ponytail", "Spiky", "Mohawk", "Curly"]

# Skin tone options — separate from hair colour, applies to the avatar's face
SKIN_TONES = [
    (255, 235, 215),
    (255, 219, 172),
    (241, 194, 125),
    (224, 172, 105),
    (198, 134, 66),
    (161, 102, 62),
    (110, 74, 48),
    (74, 49, 33),
]

# Facial hair — offered only when gender is "Male"
FACIAL_HAIR_STYLES = ["None", "Stubble", "Moustache", "Beard"]

# Pygame's bundled default font instead of SysFont — SysFont depends on fonts
# installed on the machine (or browser sandbox) it runs on, which can't be
# relied on once this ships as a pygbag/browser build.
font = pygame.font.Font(None, 28)
small_font = pygame.font.Font(None, 22)
title_font = pygame.font.Font(None, 52)
title_font.set_bold(True)

def draw_text(screen, text, selected_font, colour, x, y, centre=False):
    surface = selected_font.render(str(text), True, colour)
    rect = surface.get_rect()
    if centre:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)

def draw_rounded_rect(screen, colour, rect, radius=10, width=0):
    pygame.draw.rect(screen, colour, rect, width, border_radius=radius)

def lerp(a, b, t):
    return a + (b - a) * t

def make_vertical_gradient(width, height, top_colour, bottom_colour):
    """Precompute a gradient once as a Surface, so screens can blit it each
    frame instead of redrawing hundreds of lines every frame."""
    surface = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(height - 1, 1)
        colour = (
            int(lerp(top_colour[0], bottom_colour[0], t)),
            int(lerp(top_colour[1], bottom_colour[1], t)),
            int(lerp(top_colour[2], bottom_colour[2], t)),
        )
        pygame.draw.line(surface, colour, (0, y), (width, y))
    return surface