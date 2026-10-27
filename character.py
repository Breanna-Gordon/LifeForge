import asyncio
from avatar import draw_avatar
import colorsys
import math
import pygame
from constants import OUTLINE, INK, MUTED, draw_card, draw_pill, draw_shadow
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, LIGHT_GREY,
    DARK_GREY, GREEN, ACCENT, DEFAULT_HAIR_COLOUR, HAIRSTYLES,
    SKIN_TONES, FACIAL_HAIR_STYLES,
    font, small_font, title_font, draw_text, draw_rounded_rect,
    make_vertical_gradient
)

def load_image(path, size=None):
    try:
        image = pygame.image.load(path).convert()
        if size:
            image = pygame.transform.scale(image, size)
        return image
    except (pygame.error, FileNotFoundError):
        return None

COLLAR_COLORS = {"Male": (70, 110, 190), "Female": (220, 90, 140)}

def make_color_wheel(diameter):
    """Precomputed once — an HSV colour wheel (hue = angle, saturation =
    distance from centre) rendered to a Surface with alpha outside the
    circle, so it can just be blit each frame instead of redrawn."""
    surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    radius = diameter / 2
    for y in range(diameter):
        for x in range(diameter):
            dx = x - radius
            dy = y - radius
            dist = math.hypot(dx, dy)
            if dist <= radius:
                hue = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
                sat = min(dist / radius, 1.0)
                r, g, b = colorsys.hsv_to_rgb(hue, sat, 0.95)
                surface.set_at((x, y), (int(r * 255), int(g * 255), int(b * 255), 255))
    return surface

def pick_color_from_wheel(local_x, local_y, diameter):
    """Given a click position inside the wheel's local coordinates, returns
    the RGB colour at that point (or None if outside the circle)."""
    radius = diameter / 2
    dx = local_x - radius
    dy = local_y - radius
    dist = math.hypot(dx, dy)
    if dist > radius:
        return None
    hue = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
    sat = min(dist / radius, 1.0)
    r, g, b = colorsys.hsv_to_rgb(hue, sat, 0.95)
    return (int(r * 255), int(g * 255), int(b * 255)), (local_x, local_y)

async def character_selection_screen(screen):
    """Name, gender, who you're attracted to, and a full look editor.
    Returns (gender, name, hair_colour, hairstyle, skin_tone, facial_hair, orientation, feat)."""
    import appearance
    fallback_bg = make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, (232, 222, 248), (255, 255, 255))
    name = ""
    gender = "Female"
    look = appearance.default_look(gender)
    ed = {"tab": 0}
    orient_index = 2
    ORIENTS = [("Men", "Men"), ("Women", "Women"), ("Everyone", "Both")]
    clock = pygame.time.Clock()
    name_box = pygame.Rect(60, 96, 300, 34)
    avatar_rect = pygame.Rect(70, 150, 280, 340)
    male_rect = pygame.Rect(70, 505, 130, 32)
    female_rect = pygame.Rect(220, 505, 130, 32)
    continue_rect = pygame.Rect(SCREEN_WIDTH // 2 - 130, 640, 260, 44)
    editor_rect = pygame.Rect(420, 100, 440, 480)
    picked = {"gender": False}

    def current_selection():
        facial = look["facial"] if gender == "Male" else "None"
        return (gender, name.strip(), tuple(look["hair"]), look["style"], tuple(look["skin"]), facial,
                ORIENTS[orient_index][1], appearance.feat_of(look))

    while True:
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(fallback_bg, (0, 0))
        draw_text(screen, "Create Your Character", title_font, INK, SCREEN_WIDTH // 2, 40, centre=True)
        draw_text(screen, "Name", small_font, MUTED, name_box.x, name_box.y - 18)
        pygame.draw.line(screen, OUTLINE, (name_box.x, name_box.bottom), (name_box.right, name_box.bottom), 2)
        draw_text(screen, (name or "Type your name") + ("|" if (pygame.time.get_ticks() // 500) % 2 else ""), font,
                  MUTED if not name else INK, name_box.x + 2, name_box.y + 6)
        appearance.draw_look(screen, avatar_rect, gender, look)
        for label, rect in (("Male", male_rect), ("Female", female_rect)):
            on = gender == label
            if on:
                draw_rounded_rect(screen, ACCENT, rect, radius=16)
            draw_text(screen, label, font, INK if on or rect.collidepoint(mouse_pos) else MUTED, rect.centerx, rect.centery, centre=True)
        draw_text(screen, "Attracted to", small_font, MUTED, 70, 552)
        for i, (label, _v) in enumerate(ORIENTS):
            r = pygame.Rect(70 + i * 96, 572, 90, 26)
            on = i == orient_index
            if on:
                draw_rounded_rect(screen, ACCENT, r, radius=8)
            draw_text(screen, label, small_font, INK if on or r.collidepoint(mouse_pos) else MUTED, r.centerx, r.centery, centre=True)
        hits = appearance.draw_editor(screen, editor_rect, mouse_pos, look, gender, ed)
        enabled = bool(name.strip())
        draw_rounded_rect(screen, (ACCENT if continue_rect.collidepoint(mouse_pos) else GREEN) if enabled else LIGHT_GREY, continue_rect, radius=12)
        draw_text(screen, "Continue", font, INK, continue_rect.centerx, continue_rect.centery, centre=True)
        draw_text(screen, "Press ESC to return to the menu. You can change your look later by clicking your portrait.", small_font, MUTED,
                  SCREEN_WIDTH // 2, 692, centre=True)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None, None, None, None, None, None, None, None
                if event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.key == pygame.K_RETURN and name.strip():
                    return current_selection()
                elif event.unicode and event.unicode.isprintable() and len(name) < 20:
                    name += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if male_rect.collidepoint(mx, my) and gender != "Male":
                    gender = "Male"
                    look["style"] = "Short"
                elif female_rect.collidepoint(mx, my) and gender != "Female":
                    gender = "Female"
                    look["style"] = "Long"
                    look["facial"] = "None"
                for i in range(3):
                    if pygame.Rect(70 + i * 96, 572, 90, 26).collidepoint(mx, my):
                        orient_index = i
                appearance.click_editor(mx, my, hits, look, gender, ed)
                if continue_rect.collidepoint(mx, my) and name.strip():
                    return current_selection()
