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
    "academic": (70, 170, 150),
    "looks":    (236, 130, 178),
    "athletic": (80, 190, 210),
}

STAT_ORDER = ["physical", "mental", "social", "academic", "looks", "athletic", "wealth"]
# Running any of these to 0 ends the game. Academic, looks and athletic
# can bottom out without killing you.
VITAL_STATS = ["physical", "mental", "social", "wealth"]
STAT_LABELS = {"physical": "Health", "mental": "Mental", "social": "Social", "academic": "Academic",
               "looks": "Looks", "athletic": "Athletic", "wealth": "Wealth"}

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

# ---- shared look: soft cards, quiet outlines, dark-ink text ----
INK = (40, 36, 58)
MUTED = (104, 100, 124)
OUTLINE = (160, 154, 186)

_shadow_cache = {}

def draw_shadow(screen, rect, radius=14, spread=8, strength=46):
    """A soft drop shadow, cached per size."""
    key = (rect.w, rect.h, radius, spread, strength)
    surf = _shadow_cache.get(key)
    if surf is None:
        surf = pygame.Surface((rect.w + spread * 2, rect.h + spread * 2), pygame.SRCALPHA)
        for i in range(spread, 0, -1):
            a = int(strength * (1 - i / spread) ** 2) + 2
            pygame.draw.rect(surf, (30, 20, 60, a), (spread - i, spread - i + 3, rect.w + i * 2, rect.h + i * 2), border_radius=radius + i)
        if len(_shadow_cache) > 60:
            _shadow_cache.clear()
        _shadow_cache[key] = surf
    screen.blit(surf, (rect.x - spread, rect.y - spread))

def draw_card(screen, rect, fill=(255, 255, 255), radius=14, border=True, shadow=True, alpha=None):
    rect = pygame.Rect(rect)
    if shadow:
        draw_shadow(screen, rect, radius)
    if alpha is not None:
        tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(tmp, (*fill[:3], alpha), tmp.get_rect(), border_radius=radius)
        screen.blit(tmp, rect.topleft)
    else:
        pygame.draw.rect(screen, fill, rect, border_radius=radius)
    if border:
        pygame.draw.rect(screen, (225, 220, 238), rect, 1, border_radius=radius)

def draw_pill(screen, rect, label, fnt, mouse_pos=None, primary=False, disabled=False, selected=False):
    """A friendly rounded button with a soft shadow and a hover lift."""
    rect = pygame.Rect(rect)
    hovered = bool(mouse_pos) and rect.collidepoint(mouse_pos) and not disabled
    if hovered:
        rect = rect.move(0, -2)
    draw_shadow(screen, rect, rect.h // 2 if rect.h < 50 else 12, 5, 30)
    if disabled:
        fill, txt = (232, 230, 238), (150, 146, 166)
    elif primary or selected:
        fill, txt = ((255, 128, 48) if hovered else ACCENT), (255, 255, 255)
    else:
        fill, txt = ((255, 236, 218) if hovered else WHITE), INK
    pygame.draw.rect(screen, fill, rect, border_radius=min(rect.h // 2, 14))
    if not (primary or selected) and not disabled:
        pygame.draw.rect(screen, (225, 220, 238), rect, 1, border_radius=min(rect.h // 2, 14))
    draw_text(screen, label, fnt, txt, rect.centerx, rect.centery, centre=True)
    return rect

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
