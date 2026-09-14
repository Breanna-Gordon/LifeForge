import asyncio
import colorsys
import math
import pygame
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

def draw_avatar(screen, rect, gender, hair_colour, hairstyle, skin_tone, facial_hair="None"):
    """Draws a simple procedural avatar within `rect` — no image files
    needed, so it can never silently fail to load in a browser build."""
    cx = rect.centerx
    cy = rect.y + int(rect.height * 0.4)
    head_radius = int(rect.width * 0.26)

    collar_colour = COLLAR_COLORS.get(gender, (130, 130, 140))
    shoulder_rect = pygame.Rect(0, 0, int(rect.width * 0.85), int(rect.height * 0.45))
    shoulder_rect.midtop = (cx, cy + head_radius - 8)
    pygame.draw.ellipse(screen, collar_colour, shoulder_rect)

    pygame.draw.circle(screen, skin_tone, (cx, cy), head_radius)
    pygame.draw.circle(screen, BLACK, (cx, cy), head_radius, 2)

    if gender == "Male":
        draw_facial_hair(screen, cx, cy, head_radius, hair_colour, facial_hair)

    eye_dx = head_radius // 3
    eye_y = cy - head_radius // 6
    pygame.draw.circle(screen, BLACK, (cx - eye_dx, eye_y), 3)
    pygame.draw.circle(screen, BLACK, (cx + eye_dx, eye_y), 3)

    smile_rect = pygame.Rect(0, 0, head_radius, head_radius // 2)
    smile_rect.center = (cx, cy + head_radius // 5)
    pygame.draw.arc(screen, BLACK, smile_rect, 3.5, 6.0, 2)

    draw_hair(screen, cx, cy, head_radius, hair_colour, hairstyle)

def draw_facial_hair(screen, cx, cy, r, colour, style):
    if style == "None":
        return

    jaw_rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)

    if style == "Stubble":
        pygame.draw.arc(screen, colour, jaw_rect, 3.3, 6.12, max(int(r * 0.12), 3))
    elif style == "Beard":
        pygame.draw.arc(screen, colour, jaw_rect, 3.3, 6.12, max(int(r * 0.4), 10))
    elif style == "Moustache":
        rect = pygame.Rect(0, 0, int(r * 0.7), int(r * 0.22))
        rect.center = (cx, cy + int(r * 0.28))
        pygame.draw.ellipse(screen, colour, rect)

def draw_hair_cap(screen, cx, cy, r, colour, coverage):
    """Draws a hair cap that hugs the head's own curvature rather than a
    separately-shaped ellipse, so it can't balloon into a helmet shape.
    `coverage` is how far down from the very top of the head it extends —
    0 is nothing, 1 would reach all the way to the head's centre."""
    cap_radius = int(r * 1.04)
    clip_rect = pygame.Rect(cx - cap_radius, cy - cap_radius,
                            cap_radius * 2, max(int(cap_radius * coverage), 1))
    old_clip = screen.get_clip()
    screen.set_clip(clip_rect)
    pygame.draw.circle(screen, colour, (cx, cy), cap_radius)
    screen.set_clip(old_clip)

def draw_hair(screen, cx, cy, r, colour, style):
    if style == "Bald":
        return

    if style == "Buzzcut":
        draw_hair_cap(screen, cx, cy, r, colour, coverage=0.14)

    elif style == "Short":
        draw_hair_cap(screen, cx, cy, r, colour, coverage=0.32)

    elif style == "Long":
        draw_hair_cap(screen, cx, cy, r, colour, coverage=0.32)
        side_w = max(int(r * 0.24), 8)
        left_rect = pygame.Rect(cx - r - side_w + 4, cy - int(r * 0.1), side_w, int(r * 1.6))
        right_rect = pygame.Rect(cx + r - 4, cy - int(r * 0.1), side_w, int(r * 1.6))
        pygame.draw.rect(screen, colour, left_rect, border_radius=side_w // 2)
        pygame.draw.rect(screen, colour, right_rect, border_radius=side_w // 2)

    elif style == "Ponytail":
        draw_hair_cap(screen, cx, cy, r, colour, coverage=0.32)
        tail_points = [
            (cx + int(r * 0.7), cy - int(r * 0.55)),
            (cx + int(r * 1.0), cy + int(r * 0.1)),
            (cx + int(r * 0.8), cy + int(r * 1.4)),
            (cx + int(r * 0.5), cy + int(r * 1.35)),
            (cx + int(r * 0.5), cy + int(r * 0.15)),
        ]
        pygame.draw.polygon(screen, colour, tail_points)

    elif style == "Spiky":
        spikes = 6
        for i in range(spikes):
            t = i / (spikes - 1)
            angle = math.pi * (0.15 + 0.7 * t)
            base_x = cx + int(r * 0.9 * math.cos(math.pi - angle))
            base_y = cy - int(r * 0.9 * math.sin(angle))
            tip_x = cx + int(r * 1.5 * math.cos(math.pi - angle))
            tip_y = cy - int(r * 1.5 * math.sin(angle))
            pygame.draw.polygon(screen, colour, [
                (base_x - 6, base_y), (base_x + 6, base_y), (tip_x, tip_y)
            ])

    elif style == "Mohawk":
        spikes = 5
        for i in range(spikes):
            t = i / (spikes - 1)
            x = cx - int(r * 0.5) + int(r * t)
            base_y = cy - int(r * 0.85)
            tip_y = base_y - int(r * 0.55)
            pygame.draw.polygon(screen, colour, [
                (x - 6, base_y), (x + 6, base_y), (x, tip_y)
            ])

    elif style == "Curly":
        bumps = 7
        for i in range(bumps):
            t = i / (bumps - 1)
            angle = math.pi * (0.1 + 0.8 * t)
            bx = cx + int(r * 0.95 * math.cos(math.pi - angle))
            by = cy - int(r * 0.95 * math.sin(angle))
            pygame.draw.circle(screen, colour, (bx, by), int(r * 0.28))

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
    clock = pygame.time.Clock()

    name_box = pygame.Rect(300, 60, 300, 34)
    avatar_rect = pygame.Rect(390, 102, 120, 120)

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

    continue_rect = pygame.Rect(325, 596, 250, 44)

    def style_rect(index):
        row = index // style_cols
        col = index % style_cols
        y = style_row1_y if row == 0 else style_row2_y
        x = style_start_x + col * (style_button_width + style_gap)
        return pygame.Rect(x, y, style_button_width, style_height)

    def current_selection():
        facial = FACIAL_HAIR_STYLES[facial_hair_index] if gender == "Male" else "None"
        return (gender, name.strip(), hair_colour,
                HAIRSTYLES[hairstyle_index], SKIN_TONES[skin_index], facial)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None, None, None, None, None, None
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

                if continue_rect.collidepoint(mx, my) and name.strip() and gender:
                    return current_selection()

        if background:
            screen.blit(background, (0, 0))
        else:
            screen.blit(fallback_bg, (0, 0))

        draw_text(screen, "Create Your Character", title_font, BLACK,
                  SCREEN_WIDTH // 2, 30, centre=True)

        draw_text(screen, "Name:", font, BLACK, 210, 68)
        draw_rounded_rect(screen, WHITE, name_box, radius=8)
        pygame.draw.rect(screen, BLACK, name_box, 2, border_radius=8)
        draw_text(screen, name or "Type here...", font,
                  DARK_GREY if not name else BLACK, name_box.x + 10, name_box.y + 6)

        draw_rounded_rect(screen, WHITE, avatar_rect, radius=12)
        pygame.draw.rect(screen, BLACK, avatar_rect, 2, border_radius=12)
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
            pygame.draw.rect(screen, BLACK, rect, 2, border_radius=16)
            draw_text(screen, label, small_font, BLACK, rect.centerx, rect.centery, centre=True)

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
            pygame.draw.rect(screen, BLACK, rect, 2, border_radius=8)
            draw_text(screen, style, small_font, BLACK, rect.centerx, rect.centery, centre=True)

        if gender == "Male":
            draw_text(screen, "Facial Hair", small_font, DARK_GREY, SCREEN_WIDTH // 2, facial_y - 16, centre=True)
            for i, style in enumerate(FACIAL_HAIR_STYLES):
                bx = facial_start_x + i * (facial_button_width + facial_gap)
                rect = pygame.Rect(bx, facial_y, facial_button_width, facial_height)
                selected = i == facial_hair_index
                hovered = rect.collidepoint(mouse_pos)
                fill_colour = ACCENT if selected else (LIGHT_GREY if not hovered else (235, 235, 240))
                draw_rounded_rect(screen, fill_colour, rect, radius=8)
                pygame.draw.rect(screen, BLACK, rect, 2, border_radius=8)
                draw_text(screen, style, small_font, BLACK, rect.centerx, rect.centery, centre=True)

        enabled = bool(name.strip() and gender)
        continue_hovered = continue_rect.collidepoint(mouse_pos)
        fill_colour = (ACCENT if continue_hovered else GREEN) if enabled else LIGHT_GREY
        draw_rounded_rect(screen, fill_colour, continue_rect, radius=12)
        pygame.draw.rect(screen, BLACK, continue_rect, 2, border_radius=12)
        draw_text(screen, "Continue", font, BLACK, continue_rect.centerx, continue_rect.centery, centre=True)

        draw_text(screen, "Press ESC to return to the menu.",
                  small_font, DARK_GREY, SCREEN_WIDTH // 2, 660, centre=True)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)