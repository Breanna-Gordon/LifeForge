import asyncio
import pygame
import random

from character import character_selection_screen, load_image, draw_avatar
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, LIGHT_GREY,
    DARK_GREY, GREEN, RED, ACCENT, STAGE_COLORS, STAT_COLORS,
    font, small_font, title_font, draw_text, draw_rounded_rect,
    lerp, make_vertical_gradient
)
from choices import choice_events, special_events

def get_age_stage(age):
    if age < 7:
        return "Baby"
    if age < 13:
        return "Childhood"
    if age < 20:
        return "Teenage"
    if age < 30:
        return "Young Adult"
    if age < 65:
        return "Adult"
    return "Elderly"

def update_stats(stats, consequence):
    for stat, value in consequence.items():
        stats[stat] = max(0, min(100, stats[stat] + value))
    return stats

def apply_yearly_decline(stats, age):
    for stat in stats:
        stats[stat] = max(0, stats[stat] - 1)

    if age >= 50:
        stats["physical"] = max(0, stats["physical"] - 2)
    if age >= 65:
        stats["mental"] = max(0, stats["mental"] - 2)
    if age >= 70:
        stats["physical"] = max(0, stats["physical"] - 2)
    if age >= 80:
        stats["social"] = max(0, stats["social"] - 1)

def wrap_text(text, selected_font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = word if not current else current + " " + word
        if selected_font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines

def draw_wrapped_text(screen, text, selected_font, colour, rect,
                      line_spacing=5, centre=True):
    lines = wrap_text(text, selected_font, rect.width - 20)
    line_height = selected_font.get_height() + line_spacing
    total_height = len(lines) * line_height
    y = rect.centery - total_height // 2

    for line in lines:
        if centre:
            draw_text(screen, line, selected_font, colour,
                      rect.centerx, y, centre=True)
        else:
            draw_text(screen, line, selected_font, colour,
                      rect.x + 10, y)
        y += line_height

def get_option_rects(count):
    """Shared layout math for choice buttons — used to be copy-pasted in
    three different places; now there's exactly one version of it."""
    option_width = 310
    option_height = 65
    gap = 25
    total_width = option_width * count + gap * (count - 1)
    start_x = (SCREEN_WIDTH - total_width) // 2
    y = 435

    rects = []
    for i in range(count):
        x = start_x + i * (option_width + gap)
        rects.append(pygame.Rect(x, y, option_width, option_height))
    return rects

def render_player_stats(screen, stats, displayed_stats, icons):
    bar_width = 180
    bar_height = 22
    spacing = 48
    stats_x = SCREEN_WIDTH - bar_width - 30
    stats_y = 25

    for idx, stat in enumerate(["physical", "wealth", "mental", "social"]):
        y = stats_y + idx * spacing

        icon = icons.get(stat)
        if icon:
            icon = pygame.transform.scale(icon, (30, 30))
            screen.blit(icon, (stats_x - 40, y - 4))
        else:
            # No icon image found — fall back to a coloured dot so the
            # stat row never looks broken or empty.
            pygame.draw.circle(screen, STAT_COLORS[stat], (stats_x - 25, y + 11), 12)

        draw_rounded_rect(screen, LIGHT_GREY, (stats_x, y, bar_width, bar_height), radius=8)
        filled_width = int(bar_width * displayed_stats[stat] / 100)
        if filled_width > 0:
            draw_rounded_rect(screen, STAT_COLORS[stat], (stats_x, y, filled_width, bar_height), radius=8)
        pygame.draw.rect(screen, BLACK, (stats_x, y, bar_width, bar_height), 2, border_radius=8)

        draw_text(screen, f"{stat.title()}: {stats[stat]}",
                  small_font, BLACK, stats_x + 5, y + 2)

def draw_game_screen(screen, player_name, gender, age, stage, stats, displayed_stats,
                     choice_text, options, selected_option,
                     hair_colour, hairstyle, skin_tone, facial_hair,
                     icons, background, fallback_bg):
    if background:
        screen.blit(background, (0, 0))
    else:
        screen.blit(fallback_bg, (0, 0))

    portrait_rect = pygame.Rect(25, 20, 150, 150)
    draw_rounded_rect(screen, WHITE, portrait_rect, radius=12)
    pygame.draw.rect(screen, BLACK, portrait_rect, 2, border_radius=12)
    draw_avatar(screen, portrait_rect, gender, hair_colour, hairstyle, skin_tone, facial_hair)

    draw_text(screen, f"Name: {player_name}", font, BLACK, 25, 180)
    draw_text(screen, f"Age: {age}", font, BLACK, 25, 210)

    stage_colour = STAGE_COLORS.get(stage, LIGHT_GREY)
    badge_rect = pygame.Rect(25, 242, 150, 32)
    draw_rounded_rect(screen, stage_colour, badge_rect, radius=16)
    pygame.draw.rect(screen, BLACK, badge_rect, 2, border_radius=16)
    draw_text(screen, stage, small_font, BLACK, badge_rect.centerx, badge_rect.centery, centre=True)

    render_player_stats(screen, stats, displayed_stats, icons)

    event_rect = pygame.Rect(120, 335, 660, 90)
    draw_rounded_rect(screen, WHITE, event_rect, radius=10)
    pygame.draw.rect(screen, BLACK, event_rect, 2, border_radius=10)
    draw_wrapped_text(screen, choice_text, font, BLACK, event_rect)

    rects = get_option_rects(len(options))
    mouse_pos = pygame.mouse.get_pos()

    for index, (option_text, rect) in enumerate(zip(options, rects)):
        hovered = rect.collidepoint(mouse_pos) or selected_option == index
        fill_colour = ACCENT if hovered else LIGHT_GREY
        draw_rect = rect.move(0, -4) if hovered else rect
        draw_rounded_rect(screen, fill_colour, draw_rect, radius=10)
        pygame.draw.rect(screen, BLACK, draw_rect, 2, border_radius=10)
        draw_wrapped_text(screen, option_text, small_font, BLACK, draw_rect)

    draw_text(screen, "Click an option to continue. Press ESC to quit.",
              small_font, DARK_GREY, SCREEN_WIDTH // 2, 570, centre=True)

def draw_life_graph(screen, history, rect):
    draw_rounded_rect(screen, WHITE, rect, radius=8)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=8)

    if len(history) < 2:
        draw_text(screen, "Not enough data for a graph.", small_font, DARK_GREY,
                  rect.centerx, rect.centery, centre=True)
        return

    span = len(history) - 1
    for stat_name, colour in STAT_COLORS.items():
        points = []
        for i, snapshot in enumerate(history):
            x = rect.x + int(i / span * (rect.width - 20)) + 10
            y = rect.bottom - 10 - int(snapshot[stat_name] / 100 * (rect.height - 20))
            points.append((x, y))
        pygame.draw.lines(screen, colour, False, points, 3)

    lx = rect.x + 14
    ly = rect.y + 12
    for stat_name, colour in STAT_COLORS.items():
        pygame.draw.circle(screen, colour, (lx, ly), 5)
        draw_text(screen, stat_name.title(), small_font, BLACK, lx + 10, ly - 9)
        lx += 115

async def game_over(screen, age, failed_stat, history, life_score):
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    return

        screen.fill(WHITE)
        draw_text(screen, "Game Over", title_font, RED,
                  SCREEN_WIDTH // 2, 55, centre=True)
        draw_text(screen, f"Your life ended at age {age}.",
                  font, BLACK, SCREEN_WIDTH // 2, 105, centre=True)
        draw_text(screen, f"{failed_stat.title()} reached 0.",
                  font, BLACK, SCREEN_WIDTH // 2, 135, centre=True)
        draw_text(screen, f"Life Score: {life_score}",
                  font, ACCENT, SCREEN_WIDTH // 2, 170, centre=True)

        draw_life_graph(screen, history, pygame.Rect(100, 205, 700, 150))

        draw_text(screen, "Press ENTER to return to the menu.",
                  small_font, DARK_GREY, SCREEN_WIDTH // 2, 385, centre=True)
        draw_text(screen, "Press ESC to return to the menu.",
                  small_font, DARK_GREY, SCREEN_WIDTH // 2, 410, centre=True)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

async def instructions_screen(screen):
    clock = pygame.time.Clock()
    fallback_bg = make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT,
                                          (215, 232, 255), (255, 255, 255))

    instructions = [
        "Create a character — enter a name, pick a gender, and customise",
        "your avatar's hair colour and hairstyle.",
        "Each year of your life presents a random event.",
        "Click one of the available choices to decide what happens.",
        "Your choices change your physical, wealth, mental and social stats.",
        "Stats also decline naturally as you get older.",
        "Rare wildcard events can shake things up for better or worse.",
        "If any stat reaches 0, the game ends — try to last a lifetime."
    ]

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        screen.blit(fallback_bg, (0, 0))
        draw_text(screen, "How to Play", title_font, BLACK,
                  SCREEN_WIDTH // 2, 60, centre=True)

        panel = pygame.Rect(60, 100, SCREEN_WIDTH - 120, 400)
        draw_rounded_rect(screen, WHITE, panel, radius=12)
        pygame.draw.rect(screen, BLACK, panel, 2, border_radius=12)

        y = 130
        for line in instructions:
            draw_text(screen, line, font, BLACK, 85, y)
            y += 48

        draw_text(screen, "Press ESC to return to the menu.",
                  small_font, DARK_GREY, SCREEN_WIDTH // 2, 555, centre=True)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

async def menu_screen(screen):
    background = load_image("images/menu_background.jpg",
                             (SCREEN_WIDTH, SCREEN_HEIGHT))
    fallback_bg = make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT,
                                          (255, 214, 179), (255, 255, 255))
    clock = pygame.time.Clock()

    button_width = 300
    button_height = 65
    x = (SCREEN_WIDTH - button_width) // 2

    buttons = {
        "Start": pygame.Rect(x, 260, button_width, button_height),
        "Instructions": pygame.Rect(x, 345, button_width, button_height),
        "Exit": pygame.Rect(x, 430, button_width, button_height)
    }

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for label, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if label == "Start":
                            return "start"
                        if label == "Instructions":
                            await instructions_screen(screen)
                        if label == "Exit":
                            pygame.quit()
                            raise SystemExit

        if background:
            screen.blit(background, (0, 0))
        else:
            screen.blit(fallback_bg, (0, 0))

        draw_text(screen, "LifeForge", title_font, BLACK,
                  SCREEN_WIDTH // 2, 110, centre=True)
        draw_text(screen, "Every choice shapes the life you live.",
                  small_font, DARK_GREY, SCREEN_WIDTH // 2, 160, centre=True)

        mouse_pos = pygame.mouse.get_pos()
        for label, rect in buttons.items():
            hovered = rect.collidepoint(mouse_pos)
            fill_colour = ACCENT if hovered else WHITE
            draw_rect = rect.move(0, -3) if hovered else rect
            draw_rounded_rect(screen, fill_colour, draw_rect, radius=12)
            pygame.draw.rect(screen, BLACK, draw_rect, 2, border_radius=12)
            draw_text(screen, label, font, BLACK,
                      draw_rect.centerx, draw_rect.centery, centre=True)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

async def run_game(screen):
    gender, player_name, hair_colour, hairstyle, skin_tone, facial_hair = await character_selection_screen(screen)

    if gender is None:
        return

    icons = {
        "physical": load_image("images/physical_icon.png"),
        "wealth": load_image("images/wealth_icon.png"),
        "mental": load_image("images/mental_icon.png"),
        "social": load_image("images/social_icon.png")
    }

    background = load_image("images/background.png",
                             (SCREEN_WIDTH, SCREEN_HEIGHT))

    # Precompute one soft-tinted gradient per life stage, used only when no
    # custom background image is present.
    stage_backgrounds = {
        stage_name: make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, colour, WHITE)
        for stage_name, colour in STAGE_COLORS.items()
    }

    stats = {
        "physical": 50,
        "wealth": 50,
        "mental": 50,
        "social": 50
    }
    displayed_stats = dict(stats)
    stats_history = [dict(stats)]
    last_event_text = {}

    age = 0
    clock = pygame.time.Clock()

    while True:
        stage = get_age_stage(age)
        normal_pool = choice_events[stage]["choices"]
        wildcard_pool = special_events.get(stage, {})

        use_wildcard = bool(wildcard_pool) and random.random() < 0.15
        active_pool = wildcard_pool if use_wildcard else normal_pool

        candidates = list(active_pool.items())
        previous_event = last_event_text.get(stage)
        if len(candidates) > 1 and previous_event is not None:
            filtered = [c for c in candidates if c[0] != previous_event]
            if filtered:
                candidates = filtered

        choice_text, option_data = random.choice(candidates)
        last_event_text[stage] = choice_text
        options = list(option_data.keys())
        selected_option = None

        waiting = True

        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

                if event.type == pygame.MOUSEMOTION:
                    selected_option = None
                    for index, rect in enumerate(get_option_rects(len(options))):
                        if rect.collidepoint(event.pos):
                            selected_option = index

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for index, rect in enumerate(get_option_rects(len(options))):
                        if rect.collidepoint(event.pos):
                            stats = update_stats(stats, option_data[options[index]])
                            waiting = False
                            break

            for stat in displayed_stats:
                displayed_stats[stat] = lerp(displayed_stats[stat], stats[stat], 0.15)

            draw_game_screen(
                screen, player_name, gender, age, stage, stats, displayed_stats,
                choice_text, options, selected_option,
                hair_colour, hairstyle, skin_tone, facial_hair,
                icons, background, stage_backgrounds[stage]
            )
            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)

        apply_yearly_decline(stats, age)
        stats_history.append(dict(stats))

        failed_stat = next((stat for stat, value in stats.items() if value <= 0), None)
        if failed_stat:
            life_score = age * 5 + sum(stats.values())
            await game_over(screen, age, failed_stat, stats_history, life_score)
            return

        age += 1

async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("LifeForge")

    while True:
        action = await menu_screen(screen)
        if action == "start":
            await run_game(screen)

if __name__ == "__main__":
    asyncio.run(main())