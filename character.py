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
    background = load_image("images/selection_background.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT))
    fallback_bg = make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT,
                                          (232, 222, 248), (255, 255, 255))

    name = ""
    gender = None
    skin_index = 2
    hair_colour = DEFAULT_HAIR_COLOUR
    hairstyle_index = 2  # "Short"
    facial_hair_index = 0  # "None"
    orient_index = 2  # Everyone
    ORIENTS = [("Men", "Men"), ("Women", "Women"), ("Everyone", "Both")]
    clock = pygame.time.Clock()

    name_box = pygame.Rect(300, 60, 300, 34)
    avatar_rect = pygame.Rect(385, 98, 130, 130)

    male_rect = pygame.Rect(330, 230, 110, 32)
    female_rect = pygame.Rect(460, 230, 110, 32)

    skin_gap = 34
    skin_radius = 10
    skin_y = 292
    skin_start_x = SCREEN_WIDTH // 2 - (len(SKIN_TONES) - 1) * skin_gap // 2

    wheel_diameter = 100
    wheel_rect = pygame.Rect(0, 0, wheel_diameter, wheel_diameter)
    wheel_rect.center = (SCREEN_WIDTH // 2, 380)
    wheel_surface = make_color_wheel(wheel_diameter)
    wheel_marker = (wheel_diameter / 2, wheel_diameter / 2)  # starts centred (dark/low-sat)

    style_button_width = 130
    style_gap = 14
    style_cols = 4
    style_total = style_cols * style_button_width + (style_cols - 1) * style_gap
    style_start_x = (SCREEN_WIDTH - style_total) // 2
    style_row1_y = 462
    style_row2_y = 496
    style_height = 28

    facial_button_width = 130
    facial_gap = 14
    facial_total = len(FACIAL_HAIR_STYLES) * facial_button_width + (len(FACIAL_HAIR_STYLES) - 1) * facial_gap
    facial_start_x = (SCREEN_WIDTH - facial_total) // 2
    facial_y = 554
    facial_height = 26

    orient_y = 604
    orient_w = 130
    orient_start_x = (SCREEN_WIDTH - (3 * orient_w + 2 * 14)) // 2
    continue_rect = pygame.Rect(325, 642, 250, 40)

    def style_rect(index):
        row = index // style_cols
        col = index % style_cols
        y = style_row1_y if row == 0 else style_row2_y
        x = style_start_x + col * (style_button_width + style_gap)
        return pygame.Rect(x, y, style_button_width, style_height)

    def current_selection():
        facial = FACIAL_HAIR_STYLES[facial_hair_index] if gender == "Male" else "None"
        return (gender, name.strip(), hair_colour,
                HAIRSTYLES[hairstyle_index], SKIN_TONES[skin_index], facial, ORIENTS[orient_index][1])

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None, None, None, None, None, None, None
                if event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.key == pygame.K_RETURN and name.strip() and gender:
                    return current_selection()
                elif event.unicode.isprintable() and len(name) < 20:
                    name += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if male_rect.collidepoint(mx, my):
                    gender = "Male"
                elif female_rect.collidepoint(mx, my):
                    gender = "Female"

                for i in range(len(SKIN_TONES)):
                    sx = skin_start_x + i * skin_gap
                    if (mx - sx) ** 2 + (my - skin_y) ** 2 <= skin_radius ** 2:
                        skin_index = i

                if wheel_rect.collidepoint(mx, my):
                    result = pick_color_from_wheel(mx - wheel_rect.x, my - wheel_rect.y, wheel_diameter)
                    if result:
                        hair_colour, wheel_marker = result

                for i in range(len(HAIRSTYLES)):
                    if style_rect(i).collidepoint(mx, my):
                        hairstyle_index = i

                if gender == "Male":
                    for i in range(len(FACIAL_HAIR_STYLES)):
                        bx = facial_start_x + i * (facial_button_width + facial_gap)
                        rect = pygame.Rect(bx, facial_y, facial_button_width, facial_height)
                        if rect.collidepoint(mx, my):
                            facial_hair_index = i

                for i in range(3):
                    if pygame.Rect(orient_start_x + i * (orient_w + 14), orient_y, orient_w, 26).collidepoint(mx, my):
                        orient_index = i

                if continue_rect.collidepoint(mx, my) and name.strip() and gender:
                    return current_selection()

        if background:
            screen.blit(background, (0, 0))
        else:
            screen.blit(fallback_bg, (0, 0))

        draw_text(screen, "Create Your Character", title_font, INK,
                  SCREEN_WIDTH // 2, 30, centre=True)

        draw_text(screen, "Name:", font, INK, 210, 68)
        draw_rounded_rect(screen, WHITE, name_box, radius=8)
        pygame.draw.rect(screen, OUTLINE, name_box, 2, border_radius=8)
        draw_text(screen, name or "Type here...", font,
                  DARK_GREY if not name else BLACK, name_box.x + 10, name_box.y + 6)

        draw_rounded_rect(screen, WHITE, avatar_rect, radius=12)
        pygame.draw.rect(screen, OUTLINE, avatar_rect, 2, border_radius=12)
        if gender:
            draw_avatar(screen, avatar_rect, gender, hair_colour,
                       HAIRSTYLES[hairstyle_index], SKIN_TONES[skin_index],
                       FACIAL_HAIR_STYLES[facial_hair_index] if gender == "Male" else "None")
        else:
            draw_text(screen, "Pick a gender", small_font, DARK_GREY,
                      avatar_rect.centerx, avatar_rect.centery, centre=True)

        mouse_pos = pygame.mouse.get_pos()

        for label, rect in (("Male", male_rect), ("Female", female_rect)):
            selected = gender == label
            hovered = rect.collidepoint(mouse_pos)
            fill_colour = GREEN if selected else (ACCENT if hovered else WHITE)
            draw_rounded_rect(screen, fill_colour, rect, radius=16)
            pygame.draw.rect(screen, OUTLINE, rect, 2, border_radius=16)
            draw_text(screen, label, small_font, INK, rect.centerx, rect.centery, centre=True)

        draw_text(screen, "Skin Tone", small_font, DARK_GREY, SCREEN_WIDTH // 2, skin_y - 18, centre=True)
        for i, tone in enumerate(SKIN_TONES):
            sx = skin_start_x + i * skin_gap
            pygame.draw.circle(screen, tone, (sx, skin_y), skin_radius)
            border_colour = ACCENT if i == skin_index else BLACK
            pygame.draw.circle(screen, border_colour, (sx, skin_y), skin_radius, 3)

        draw_text(screen, "Hair Colour", small_font, DARK_GREY, SCREEN_WIDTH // 2, wheel_rect.top - 14, centre=True)
        screen.blit(wheel_surface, wheel_rect)
        marker_x = wheel_rect.x + int(wheel_marker[0])
        marker_y = wheel_rect.y + int(wheel_marker[1])
        pygame.draw.circle(screen, WHITE, (marker_x, marker_y), 6, 2)
        pygame.draw.circle(screen, BLACK, (marker_x, marker_y), 6, 1)

        draw_text(screen, "Hairstyle", small_font, DARK_GREY, SCREEN_WIDTH // 2, style_row1_y - 16, centre=True)
        for i, style in enumerate(HAIRSTYLES):
            rect = style_rect(i)
            selected = i == hairstyle_index
            hovered = rect.collidepoint(mouse_pos)
            fill_colour = ACCENT if selected else (LIGHT_GREY if not hovered else (235, 235, 240))
            draw_rounded_rect(screen, fill_colour, rect, radius=8)
            pygame.draw.rect(screen, OUTLINE, rect, 2, border_radius=8)
            draw_text(screen, style, small_font, INK, rect.centerx, rect.centery, centre=True)

        if gender == "Male":
            draw_text(screen, "Facial Hair", small_font, DARK_GREY, SCREEN_WIDTH // 2, facial_y - 16, centre=True)
            for i, style in enumerate(FACIAL_HAIR_STYLES):
                bx = facial_start_x + i * (facial_button_width + facial_gap)
                rect = pygame.Rect(bx, facial_y, facial_button_width, facial_height)
                selected = i == facial_hair_index
                hovered = rect.collidepoint(mouse_pos)
                fill_colour = ACCENT if selected else (LIGHT_GREY if not hovered else (235, 235, 240))
                draw_rounded_rect(screen, fill_colour, rect, radius=8)
                pygame.draw.rect(screen, OUTLINE, rect, 2, border_radius=8)
                draw_text(screen, style, small_font, INK, rect.centerx, rect.centery, centre=True)

        draw_text(screen, "Attracted to", small_font, DARK_GREY, SCREEN_WIDTH // 2, orient_y - 16, centre=True)
        for i, (label, _v) in enumerate(ORIENTS):
            rect = pygame.Rect(orient_start_x + i * (orient_w + 14), orient_y, orient_w, 26)
            selected = i == orient_index
            fill_colour = ACCENT if selected else (LIGHT_GREY if not rect.collidepoint(mouse_pos) else (235, 235, 240))
            draw_rounded_rect(screen, fill_colour, rect, radius=8)
            pygame.draw.rect(screen, OUTLINE, rect, 2, border_radius=8)
            draw_text(screen, label, small_font, INK, rect.centerx, rect.centery, centre=True)

        enabled = bool(name.strip() and gender)
        continue_hovered = continue_rect.collidepoint(mouse_pos)
        fill_colour = (ACCENT if continue_hovered else GREEN) if enabled else LIGHT_GREY
        draw_rounded_rect(screen, fill_colour, continue_rect, radius=12)
        pygame.draw.rect(screen, OUTLINE, continue_rect, 2, border_radius=12)
        draw_text(screen, "Continue", font, INK, continue_rect.centerx, continue_rect.centery, centre=True)

        draw_text(screen, "Press ESC to return to the menu.",
                  small_font, DARK_GREY, SCREEN_WIDTH // 2, 690, centre=True)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)
