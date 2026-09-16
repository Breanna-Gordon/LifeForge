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
from people import generate_family, draw_people_tab, handle_people_click, make_person
from career import draw_career_tab, handle_career_click, advance_career_year

TABS = ["Life", "People", "Career"]
CONTENT_RECT = pygame.Rect(200, 320, 675, 330)

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

def draw_wrapped_text(screen, text, selected_font, colour, rect, line_spacing=5, centre=True):
    lines = wrap_text(text, selected_font, rect.width - 20)
    line_height = selected_font.get_height() + line_spacing
    total_height = len(lines) * line_height
    y = rect.centery - total_height // 2
    for line in lines:
        if centre:
            draw_text(screen, line, selected_font, colour, rect.centerx, y, centre=True)
        else:
            draw_text(screen, line, selected_font, colour, rect.x + 10, y)
        y += line_height

def get_option_rects(count, rect):
    option_width = min(300, (rect.width - 20 * (count - 1)) // count)
    option_height = 60
    gap = 20
    total_width = option_width * count + gap * (count - 1)
    start_x = rect.centerx - total_width // 2
    y = rect.y + 110
    return [pygame.Rect(start_x + i * (option_width + gap), y, option_width, option_height)
            for i in range(count)]

def draw_tab_bar(screen, active_tab, mouse_pos):
    button_w = 140
    gap = 16
    total_w = len(TABS) * button_w + (len(TABS) - 1) * gap
    start_x = (SCREEN_WIDTH - total_w) // 2
    y = 14
    rects = {}
    for i, tab in enumerate(TABS):
        rect = pygame.Rect(start_x + i * (button_w + gap), y, button_w, 36)
        selected = tab == active_tab
        hovered = rect.collidepoint(mouse_pos)
        fill = ACCENT if selected else (LIGHT_GREY if not hovered else (235, 235, 240))
        draw_rounded_rect(screen, fill, rect, radius=10)
        pygame.draw.rect(screen, BLACK, rect, 2, border_radius=10)
        draw_text(screen, tab, font, BLACK, rect.centerx, rect.centery, centre=True)
        rects[tab] = rect
    return rects

def render_player_stats(screen, stats, displayed_stats, icons):
    bar_width = 180
    bar_height = 20
    spacing = 42
    stats_x = SCREEN_WIDTH - bar_width - 30
    stats_y = 64

    for idx, stat in enumerate(["physical", "wealth", "mental", "social", "academic"]):
        y = stats_y + idx * spacing
        icon = icons.get(stat)
        if icon:
            icon = pygame.transform.scale(icon, (28, 28))
            screen.blit(icon, (stats_x - 38, y - 4))
        else:
            pygame.draw.circle(screen, STAT_COLORS[stat], (stats_x - 24, y + 10), 11)

        draw_rounded_rect(screen, LIGHT_GREY, (stats_x, y, bar_width, bar_height), radius=8)
        filled_width = int(bar_width * displayed_stats[stat] / 100)
        if filled_width > 0:
            draw_rounded_rect(screen, STAT_COLORS[stat], (stats_x, y, filled_width, bar_height), radius=8)
        pygame.draw.rect(screen, BLACK, (stats_x, y, bar_width, bar_height), 2, border_radius=8)

        draw_text(screen, f"{stat.title()}: {stats[stat]}", small_font, BLACK, stats_x + 5, y + 1)

def draw_hub_frame(screen, player_name, age, stage, stats, displayed_stats,
                   hair_colour, hairstyle, skin_tone, facial_hair, gender,
                   icons, background, fallback_bg, active_tab, mouse_pos):
    if background:
        screen.blit(background, (0, 0))
    else:
        screen.blit(fallback_bg, (0, 0))

    tab_rects = draw_tab_bar(screen, active_tab, mouse_pos)

    portrait_rect = pygame.Rect(25, 64, 150, 150)
    draw_rounded_rect(screen, WHITE, portrait_rect, radius=12)
    pygame.draw.rect(screen, BLACK, portrait_rect, 2, border_radius=12)
    draw_avatar(screen, portrait_rect, gender, hair_colour, hairstyle, skin_tone, facial_hair)

    draw_text(screen, f"Name: {player_name}", font, BLACK, 25, 224)
    draw_text(screen, f"Age: {age}", font, BLACK, 25, 254)

    stage_colour = STAGE_COLORS.get(stage, LIGHT_GREY)
    badge_rect = pygame.Rect(25, 286, 150, 32)
    draw_rounded_rect(screen, stage_colour, badge_rect, radius=16)
    pygame.draw.rect(screen, BLACK, badge_rect, 2, border_radius=16)
    draw_text(screen, stage, small_font, BLACK, badge_rect.centerx, badge_rect.centery, centre=True)

    render_player_stats(screen, stats, displayed_stats, icons)

    return tab_rects

def draw_life_tab(screen, rect, choice_text, options, selected_option, mouse_pos):
    event_rect = pygame.Rect(rect.x, rect.y, rect.width, 90)
    draw_rounded_rect(screen, WHITE, event_rect, radius=10)
    pygame.draw.rect(screen, BLACK, event_rect, 2, border_radius=10)
    draw_wrapped_text(screen, choice_text, font, BLACK, event_rect)

    rects = get_option_rects(len(options), rect)
    for index, (option_text, orect) in enumerate(zip(options, rects)):
        hovered = orect.collidepoint(mouse_pos) or selected_option == index
        fill_colour = ACCENT if hovered else LIGHT_GREY
        draw_rect = orect.move(0, -4) if hovered else orect
        draw_rounded_rect(screen, fill_colour, draw_rect, radius=10)
        pygame.draw.rect(screen, BLACK, draw_rect, 2, border_radius=10)
        draw_wrapped_text(screen, option_text, small_font, BLACK, draw_rect)

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
        if lx > rect.right - 100:
            lx = rect.x + 14
            ly += 20

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
        draw_text(screen, "Game Over", title_font, RED, SCREEN_WIDTH // 2, 55, centre=True)
        draw_text(screen, f"Your life ended at age {age}.", font, BLACK, SCREEN_WIDTH // 2, 105, centre=True)
        draw_text(screen, f"{failed_stat.title()} reached 0.", font, BLACK, SCREEN_WIDTH // 2, 135, centre=True)
        draw_text(screen, f"Life Score: {life_score}", font, ACCENT, SCREEN_WIDTH // 2, 170, centre=True)

        draw_life_graph(screen, history, pygame.Rect(100, 205, 700, 170))

        draw_text(screen, "Press ENTER to return to the menu.", small_font, DARK_GREY,
                  SCREEN_WIDTH // 2, 410, centre=True)
        draw_text(screen, "Press ESC to return to the menu.", small_font, DARK_GREY,
                  SCREEN_WIDTH // 2, 435, centre=True)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

async def instructions_screen(screen):
    clock = pygame.time.Clock()
    fallback_bg = make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, (215, 232, 255), (255, 255, 255))

    instructions = [
        "Create a character — name, gender, hair, skin tone, facial hair.",
        "Each year, resolve the random event on the Life tab to move on.",
        "The People tab holds your family, friends, and partner — talk,",
        "hang out, argue, or gift them to change how close you are.",
        "The Career tab handles school, university, and jobs — study to",
        "raise your Academic stat, then apply to university or work.",
        "Stats decline naturally with age — keep them above 0 to survive.",
        "Rare wildcard events can shake things up for better or worse."
    ]

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        screen.blit(fallback_bg, (0, 0))
        draw_text(screen, "How to Play", title_font, BLACK, SCREEN_WIDTH // 2, 50, centre=True)

        panel = pygame.Rect(60, 90, SCREEN_WIDTH - 120, 440)
        draw_rounded_rect(screen, WHITE, panel, radius=12)
        pygame.draw.rect(screen, BLACK, panel, 2, border_radius=12)

        y = 118
        for line in instructions:
            draw_text(screen, line, font, BLACK, 85, y)
            y += 42

        draw_text(screen, "Press ESC to return to the menu.", small_font, DARK_GREY,
                  SCREEN_WIDTH // 2, 640, centre=True)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

async def menu_screen(screen):
    background = load_image("images/menu_background.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT))
    fallback_bg = make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, (255, 214, 179), (255, 255, 255))
    clock = pygame.time.Clock()

    button_width = 300
    button_height = 65
    x = (SCREEN_WIDTH - button_width) // 2

    buttons = {
        "Start": pygame.Rect(x, 300, button_width, button_height),
        "Instructions": pygame.Rect(x, 385, button_width, button_height),
        "Exit": pygame.Rect(x, 470, button_width, button_height)
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

        draw_text(screen, "LifeForge", title_font, BLACK, SCREEN_WIDTH // 2, 150, centre=True)
        draw_text(screen, "Every choice shapes the life you live.", small_font, DARK_GREY,
                  SCREEN_WIDTH // 2, 200, centre=True)

        mouse_pos = pygame.mouse.get_pos()
        for label, rect in buttons.items():
            hovered = rect.collidepoint(mouse_pos)
            fill_colour = ACCENT if hovered else WHITE
            draw_rect = rect.move(0, -3) if hovered else rect
            draw_rounded_rect(screen, fill_colour, draw_rect, radius=12)
            pygame.draw.rect(screen, BLACK, draw_rect, 2, border_radius=12)
            draw_text(screen, label, font, BLACK, draw_rect.centerx, draw_rect.centery, centre=True)

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
        "social": load_image("images/social_icon.png"),
    }
    background = load_image("images/background.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
    stage_backgrounds = {
        stage_name: make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, colour, WHITE)
        for stage_name, colour in STAGE_COLORS.items()
    }

    stats = {"physical": 50, "wealth": 50, "mental": 50, "social": 50, "academic": 50}
    displayed_stats = dict(stats)
    stats_history = [dict(stats)]
    last_event_text = {}

    people = generate_family()
    friends = []
    partner = None
    career = {"education": "None", "enrolled": False, "uni_target": None,
             "uni_years_done": 0, "job": None, "browsing_jobs": False}

    active_tab = "Life"
    people_scroll = 0
    last_tab_rects = {}
    last_career_buttons = {}

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

        interacted_this_year = set()
        waiting = True

        while waiting:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

                if event.type == pygame.MOUSEMOTION and active_tab == "Life":
                    selected_option = None
                    for index, orect in enumerate(get_option_rects(len(options), CONTENT_RECT)):
                        if orect.collidepoint(event.pos):
                            selected_option = index

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos

                    tab_hit = False
                    for tab_name, trect in last_tab_rects.items():
                        if trect.collidepoint(mx, my):
                            active_tab = tab_name
                            tab_hit = True
                            break

                    if not tab_hit:
                        if active_tab == "Life":
                            for index, orect in enumerate(get_option_rects(len(options), CONTENT_RECT)):
                                if orect.collidepoint(mx, my):
                                    stats = update_stats(stats, option_data[options[index]])
                                    waiting = False
                                    break

                        elif active_tab == "People":
                            result = handle_people_click(mx, my, CONTENT_RECT, people, friends, partner,
                                                         people_scroll, interacted_this_year, stats)
                            if result == "meet":
                                if len(friends) < 6:
                                    friends.append(make_person("Friend", "friend"))
                            elif result == "partner":
                                partner = make_person("Partner", "partner", closeness=50)

                        elif active_tab == "Career":
                            handle_career_click(mx, my, last_career_buttons, age, stats, career, interacted_this_year)

            for stat in displayed_stats:
                displayed_stats[stat] = lerp(displayed_stats[stat], stats[stat], 0.15)

            last_tab_rects = draw_hub_frame(
                screen, player_name, age, stage, stats, displayed_stats,
                hair_colour, hairstyle, skin_tone, facial_hair, gender,
                icons, background, stage_backgrounds[stage], active_tab, mouse_pos
            )

            if active_tab == "Life":
                draw_life_tab(screen, CONTENT_RECT, choice_text, options, selected_option, mouse_pos)
            elif active_tab == "People":
                if career["job"]:
                    meet_label = "Meet a Coworker"
                elif age < 18:
                    meet_label = "Meet Someone at School"
                else:
                    meet_label = "Meet Someone New"
                people_scroll = draw_people_tab(screen, CONTENT_RECT, people, friends, partner,
                                                people_scroll, mouse_pos, interacted_this_year, meet_label)
            elif active_tab == "Career":
                last_career_buttons = draw_career_tab(screen, CONTENT_RECT, mouse_pos, age, stats,
                                                       career, interacted_this_year)

            draw_text(screen, "Resolve this year's event on the Life tab to continue. Press ESC to quit.",
                      small_font, DARK_GREY, SCREEN_WIDTH // 2, 665, centre=True)

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)

        apply_yearly_decline(stats, age)
        advance_career_year(career, stats)
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