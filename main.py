import asyncio
import pygame
import random

from character import character_selection_screen, load_image, draw_avatar
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, LIGHT_GREY,
    DARK_GREY, GREEN, RED, ACCENT, STAGE_COLORS, STAT_COLORS, STAT_ORDER, VITAL_STATS, STAT_LABELS,
    font, small_font, title_font, draw_text, draw_rounded_rect,
    lerp, make_vertical_gradient
)
from choices import choice_events, special_events
from people import (ensure_profiles, advance_deaths, ask_for_money, draw_profile, handle_profile_click, is_attracted,
                    gender_word, remember, generate_family, draw_people_tab, handle_people_click, make_person, advance_relationships,
                    TRAITS, compatibility, make_child, children_of, PROPOSAL_COST, CHILD_COST)
from education import draw_education_tab, handle_education_click
from career import draw_career_tab, handle_career_click, advance_career_year
from events import pick_year_events, describe
from shop import draw_shop_tab, handle_shop_click, apply_passives
from journal import draw_journal_tab
from save import has_save, save_game, load_game, delete_save
from activities import draw_activities_tab, handle_activities_click, advance_activities_year

TABS = ["Life", "People", "Education", "Career", "Activities", "Shop", "Journal"]
SKIP_YEARS = 5
MILESTONE_AGES = (7, 13, 16, 18, 21, 30, 65)
CONTENT_RECT = pygame.Rect(200, 320, 675, 320)
ACTIONS_PER_YEAR = 5

# Every life gets a random aspiration. Reach it and you get a Mental boost
# and a bonus to your final life score.
ASPIRATIONS = {
    "Wealthy":      ("have $500 or more",              lambda s, c, f, p, pe: s["money"] >= 500),
    "Family-minded": ("raise two or more children",    lambda s, c, f, p, pe: len([x for x in pe if x.get("is_child")]) >= 2),
    "Scholar":      ("reach Academic 80",              lambda s, c, f, p, pe: s["stats"]["academic"] >= 80),
    "Athlete":      ("reach Athletic 80",              lambda s, c, f, p, pe: s["stats"]["athletic"] >= 80),
    "Social butterfly": ("have 4 friends and Social 70", lambda s, c, f, p, pe: len(f) >= 4 and s["stats"]["social"] >= 70),
    "Soulmate":     ("get married",                    lambda s, c, f, p, pe: bool(p and p.get("married"))),
    "Performer":    ("master a music or dance skill (level 4)", lambda s, c, f, p, pe: any(s.get("skills", {}).get(k, 0) >= 4 for k in ("singing", "music", "dance"))),
}

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

def apply_consequence(state, consequence):
    """Applies an option's effects (stats and money). A "gamble" option picks
    one of its outcomes at random. Returns what actually happened."""
    if "gamble" in consequence:
        consequence = random.choice(consequence["gamble"])
    stats = state["stats"]
    for key, value in consequence.items():
        if key == "person":
            who, fx = value
            for k, v in fx.items():
                who[k] = max(0, min(100, who[k] + v))
            who["contacted"] = True
            continue
        if key == "money":
            state["money"] = max(0, state["money"] + value)
        else:
            stats[key] = max(0, min(100, stats[key] + value))
    return consequence

def log(state, text):
    state["journal"].append((state["age"], text))

def apply_yearly_decline(stats, age):
    for stat in ("mental", "social", "wealth", "academic"):
        stats[stat] = max(0, stats[stat] - 1)
    if age >= 25:
        stats["physical"] = max(0, stats["physical"] - 1)
    if age >= 35:
        stats["looks"] = max(0, stats["looks"] - 1)
    if age >= 28:
        stats["athletic"] = max(0, stats["athletic"] - (2 if age >= 50 else 1))
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

def render_player_stats(screen, stats, displayed_stats, icons):
    bar_width = 180
    bar_height = 20
    spacing = 34
    stats_x = SCREEN_WIDTH - bar_width - 30
    stats_y = 64

    for idx, stat in enumerate(STAT_ORDER):
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

        draw_text(screen, f"{STAT_LABELS[stat]}: {stats[stat]}", small_font, BLACK, stats_x + 5, y + 1)

def draw_side_panel_toggle(screen, mouse_pos):
    rect = pygame.Rect(20, 14, 70, 36)
    hovered = rect.collidepoint(mouse_pos)
    fill = ACCENT if hovered else WHITE
    draw_rounded_rect(screen, fill, rect, radius=8)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=8)
    draw_text(screen, "Menu", small_font, BLACK, rect.centerx, rect.centery, centre=True)
    return rect

def draw_side_panel(screen, active_tab, mouse_pos):
    panel_rect = pygame.Rect(20, 56, 180, len(TABS) * 46 + 14)
    draw_rounded_rect(screen, WHITE, panel_rect, radius=10)
    pygame.draw.rect(screen, BLACK, panel_rect, 2, border_radius=10)

    tab_rects = {}
    y = panel_rect.y + 10
    for tab in TABS:
        rect = pygame.Rect(panel_rect.x + 10, y, panel_rect.width - 20, 40)
        selected = tab == active_tab
        hovered = rect.collidepoint(mouse_pos)
        fill = ACCENT if selected else (LIGHT_GREY if not hovered else (235, 235, 240))
        draw_rounded_rect(screen, fill, rect, radius=8)
        pygame.draw.rect(screen, BLACK, rect, 2, border_radius=8)
        draw_text(screen, tab, font, BLACK, rect.centerx, rect.centery, centre=True)
        tab_rects[tab] = rect
        y += 46

    return tab_rects

def draw_money_and_actions(screen, state, mouse_pos):
    money_rect = pygame.Rect(100, 14, 110, 36)
    draw_rounded_rect(screen, WHITE, money_rect, radius=18)
    pygame.draw.rect(screen, BLACK, money_rect, 2, border_radius=18)
    coin_centre = (money_rect.x + 20, money_rect.centery)
    pygame.draw.circle(screen, (230, 180, 60), coin_centre, 12)
    pygame.draw.circle(screen, BLACK, coin_centre, 12, 2)
    draw_text(screen, "$", small_font, BLACK, coin_centre[0], coin_centre[1], centre=True)
    draw_text(screen, str(state["money"]), font, BLACK, money_rect.x + 38, money_rect.y + 7)

    actions_rect = pygame.Rect(SCREEN_WIDTH - 150, 14, 130, 36)
    draw_rounded_rect(screen, WHITE, actions_rect, radius=18)
    pygame.draw.rect(screen, BLACK, actions_rect, 2, border_radius=18)
    draw_text(screen, f"Actions: {state['actions_remaining']}/{ACTIONS_PER_YEAR}",
              small_font, BLACK, actions_rect.centerx, actions_rect.centery, centre=True)

def draw_age_up_button(screen, mouse_pos, resolved):
    rect = pygame.Rect(SCREEN_WIDTH // 2 - 210, 650, 210, 40)
    skip_rect = pygame.Rect(SCREEN_WIDTH // 2 + 10, 650, 200, 40)
    for r, label, f in ((rect, "Age Up" if resolved else "Age Up (skip event)", font if resolved else small_font),
                        (skip_rect, f"Skip {SKIP_YEARS} years", small_font)):
        hovered = r.collidepoint(mouse_pos)
        fill = ACCENT if hovered else WHITE
        draw_rounded_rect(screen, fill, r, radius=10)
        pygame.draw.rect(screen, BLACK, r, 2, border_radius=10)
        draw_text(screen, label, f, BLACK, r.centerx, r.centery, centre=True)
    return rect, skip_rect

def draw_hub_frame(screen, player_name, age, stage, stats, displayed_stats,
                   hair_colour, hairstyle, skin_tone, facial_hair, gender,
                   icons, background, fallback_bg, active_tab, panel_open, state, mouse_pos):
    if background:
        screen.blit(background, (0, 0))
    else:
        screen.blit(fallback_bg, (0, 0))

    toggle_rect = draw_side_panel_toggle(screen, mouse_pos)
    draw_money_and_actions(screen, state, mouse_pos)

    portrait_rect = pygame.Rect(25, 64, 150, 150)
    draw_rounded_rect(screen, WHITE, portrait_rect, radius=12)
    pygame.draw.rect(screen, BLACK, portrait_rect, 2, border_radius=12)
    draw_avatar(screen, portrait_rect, gender, hair_colour, hairstyle, skin_tone, facial_hair, age, stats["mental"])

    draw_text(screen, f"Name: {player_name}", font, BLACK, 25, 224)
    draw_text(screen, f"Age: {age}", font, BLACK, 25, 254)

    stage_colour = STAGE_COLORS.get(stage, LIGHT_GREY)
    badge_rect = pygame.Rect(25, 286, 150, 32)
    draw_rounded_rect(screen, stage_colour, badge_rect, radius=16)
    pygame.draw.rect(screen, BLACK, badge_rect, 2, border_radius=16)
    draw_text(screen, stage, small_font, BLACK, badge_rect.centerx, badge_rect.centery, centre=True)

    render_player_stats(screen, stats, displayed_stats, icons)

    age_up_rect, skip_rect = draw_age_up_button(screen, mouse_pos, state["life_event_resolved"])

    tab_rects = {}
    if panel_open:
        tab_rects = draw_side_panel(screen, active_tab, mouse_pos)

    return {"toggle": toggle_rect, "tabs": tab_rects, "age_up": age_up_rect, "skip": skip_rect}

def draw_life_tab(screen, rect, choice_text, options, selected_option, mouse_pos, resolved, chosen_index,
                  result_text="", more_events=False, event_number=1, event_total=1):
    event_rect = pygame.Rect(rect.x, rect.y, rect.width, 90)
    draw_rounded_rect(screen, WHITE, event_rect, radius=10)
    pygame.draw.rect(screen, BLACK, event_rect, 2, border_radius=10)
    draw_wrapped_text(screen, choice_text, font, BLACK, event_rect)
    if event_total > 1:
        draw_text(screen, f"Event {event_number} of {event_total}", small_font, DARK_GREY, event_rect.right - 100, event_rect.y + 6)

    rects = get_option_rects(len(options), rect)
    for index, (option_text, orect) in enumerate(zip(options, rects)):
        is_chosen = resolved and index == chosen_index
        hovered = (not resolved) and (orect.collidepoint(mouse_pos) or selected_option == index)
        if resolved:
            fill_colour = ACCENT if is_chosen else LIGHT_GREY
        else:
            fill_colour = ACCENT if hovered else LIGHT_GREY
        draw_rect = orect.move(0, -4) if hovered else orect
        draw_rounded_rect(screen, fill_colour, draw_rect, radius=10)
        pygame.draw.rect(screen, BLACK, draw_rect, 2, border_radius=10)
        draw_wrapped_text(screen, option_text, small_font, BLACK, draw_rect)

    next_rect = None
    if resolved:
        draw_text(screen, result_text, small_font, BLACK, rect.centerx, rect.y + 190, centre=True)
        if more_events:
            next_rect = pygame.Rect(rect.centerx - 90, rect.y + 215, 180, 36)
            hovered = next_rect.collidepoint(mouse_pos)
            draw_rounded_rect(screen, ACCENT if hovered else WHITE, next_rect, radius=8)
            pygame.draw.rect(screen, BLACK, next_rect, 2, border_radius=8)
            draw_text(screen, "Next event", small_font, BLACK, next_rect.centerx, next_rect.centery, centre=True)
        else:
            draw_text(screen, "Use the Menu to visit People, Education, Career or Shop, then Age Up.",
                      small_font, DARK_GREY, rect.centerx, rect.y + 225, centre=True)
    return next_rect

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

async def game_over(screen, age, reason, history, life_score, summary):
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    return
            if event.type == pygame.MOUSEBUTTONDOWN:
                return

        screen.fill(WHITE)
        draw_text(screen, "Game Over", title_font, RED, SCREEN_WIDTH // 2, 50, centre=True)
        draw_text(screen, f"Your life ended at age {age}.", font, BLACK, SCREEN_WIDTH // 2, 98, centre=True)
        draw_text(screen, reason, font, BLACK, SCREEN_WIDTH // 2, 126, centre=True)
        draw_text(screen, f"Life Score: {life_score}", font, ACCENT, SCREEN_WIDTH // 2, 158, centre=True)

        draw_life_graph(screen, history, pygame.Rect(100, 190, 700, 170))

        y = 380
        for line in summary:
            draw_text(screen, line, small_font, BLACK, SCREEN_WIDTH // 2, y, centre=True)
            y += 24

        draw_text(screen, "Press ENTER or click to return to the menu.", small_font, DARK_GREY,
                  SCREEN_WIDTH // 2, 660, centre=True)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

async def instructions_screen(screen):
    clock = pygame.time.Clock()
    fallback_bg = make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, (215, 232, 255), (255, 255, 255))

    instructions = [
        "Create a character — name, gender, hair, skin tone, facial hair.",
        "Each year you get 5 actions to spend across People, Education",
        "and Career — talk to family, study, apply to college, get a job.",
        "Resolve the Life tab's random event, then hit Age Up whenever",
        "you're ready — you don't have to use every action first.",
        "Each year can bring one or two events. Tap Menu to switch tabs.",
        "Money is real cash: jobs and pocket money earn it, and you can",
        "spend it on gifts and in the Shop (treats, trips, a bike, a dog).",
        "Bars on each person: bond, trust (and romance). Red dot: conflict.",
        "Personality decides how well you match a partner. At 18+ you can",
        "propose and try for children, who cost money until they're 18."
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

        panel = pygame.Rect(60, 90, SCREEN_WIDTH - 120, 460)
        draw_rounded_rect(screen, WHITE, panel, radius=12)
        pygame.draw.rect(screen, BLACK, panel, 2, border_radius=12)

        y = 118
        for line in instructions:
            draw_text(screen, line, font, BLACK, 85, y)
            y += 36

        draw_text(screen, "Press ESC to return to the menu.", small_font, DARK_GREY,
                  SCREEN_WIDTH // 2, 660, centre=True)

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

    labels = (["Continue"] if has_save() else []) + ["Start", "Instructions", "Exit"]
    buttons = {label: pygame.Rect(x, 270 + i * 80, button_width, button_height) for i, label in enumerate(labels)}

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
                        if label == "Continue":
                            return "continue"
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

def roll_stats():
    return {"physical": random.randint(40, 80), "mental": random.randint(40, 80),
            "social": random.randint(35, 75), "academic": random.randint(35, 80),
            "looks": random.randint(30, 85), "athletic": random.randint(30, 80),
            "wealth": random.randint(40, 65)}

async def stats_roll_screen(screen, player_name, gender, hair_colour, hairstyle, skin_tone, facial_hair):
    """BitLife-style: you are born with random stats and can re-roll until
    you like them."""
    clock = pygame.time.Clock()
    fallback_bg = make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, (255, 235, 240), (255, 255, 255))
    stats = roll_stats()
    traits = random.sample(TRAITS, 2)
    reroll = pygame.Rect(SCREEN_WIDTH // 2 - 230, 600, 210, 50)
    start = pygame.Rect(SCREEN_WIDTH // 2 + 20, 600, 210, 50)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    stats = roll_stats()
                    traits = random.sample(TRAITS, 2)
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return stats, traits
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if reroll.collidepoint(event.pos):
                    stats = roll_stats()
                    traits = random.sample(TRAITS, 2)
                elif start.collidepoint(event.pos):
                    return stats, traits

        screen.blit(fallback_bg, (0, 0))
        draw_text(screen, f"{player_name}'s starting stats", title_font, BLACK, SCREEN_WIDTH // 2, 55, centre=True)
        draw_text(screen, "Everyone is born different. Re-roll until you like them.", small_font, DARK_GREY,
                  SCREEN_WIDTH // 2, 95, centre=True)
        draw_text(screen, "Personality: " + ", ".join(traits), font, BLACK, SCREEN_WIDTH // 2, 125, centre=True)
        portrait = pygame.Rect(90, 150, 220, 220)
        draw_rounded_rect(screen, WHITE, portrait, radius=12)
        pygame.draw.rect(screen, BLACK, portrait, 2, border_radius=12)
        draw_avatar(screen, portrait, gender, hair_colour, hairstyle, skin_tone, facial_hair)
        for idx, stat in enumerate(STAT_ORDER):
            y = 150 + idx * 52
            draw_text(screen, STAT_LABELS[stat], font, BLACK, 380, y)
            bar = pygame.Rect(530, y, 280, 26)
            draw_rounded_rect(screen, LIGHT_GREY, bar, radius=10)
            draw_rounded_rect(screen, STAT_COLORS[stat], (bar.x, bar.y, int(bar.width * stats[stat] / 100), bar.height), radius=10)
            pygame.draw.rect(screen, BLACK, bar, 2, border_radius=10)
            draw_text(screen, str(stats[stat]), small_font, BLACK, bar.x + 8, bar.y + 5)
        mouse = pygame.mouse.get_pos()
        for r, label in ((reroll, "Re-roll (R)"), (start, "Start life")):
            draw_rounded_rect(screen, ACCENT if r.collidepoint(mouse) else WHITE, r, radius=10)
            pygame.draw.rect(screen, BLACK, r, 2, border_radius=10)
            draw_text(screen, label, font, BLACK, r.centerx, r.centery, centre=True)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

async def run_game(screen, resume=None):
    if resume:
        gender, player_name = resume["gender"], resume["name"]
        hair_colour, hairstyle = tuple(resume["hair_colour"]), resume["hairstyle"]
        skin_tone, facial_hair = tuple(resume["skin_tone"]), resume["facial_hair"]
        stats = resume["stats"]
    else:
        gender, player_name, hair_colour, hairstyle, skin_tone, facial_hair, orientation = await character_selection_screen(screen)
        if gender is None:
            return
        stats, player_traits = await stats_roll_screen(screen, player_name, gender, hair_colour, hairstyle, skin_tone, facial_hair)

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

    displayed_stats = dict(stats)
    stats_history = resume["history"] if resume else [dict(stats)]
    last_event_text = resume["last_event_text"] if resume else {}
    recent_events = resume["recent_events"] if resume else []

    if resume:
        people, friends, partner = resume["people"], resume["friends"], resume["partner"]
        career = resume["career"]
        state = resume["state"]
        state["stats"] = stats
        state["owned"] = set(state["owned"])
        state["bought_this_year"] = set()
        state["actions_used"] = {}
    else:
        people = generate_family(skin_tone, hair_colour)
        friends = []
        partner = None
        career = {"education": "None", "enrolled": False, "uni_target": None, "uni_years_done": 0,
                 "college_name": None, "college_prestige": 0, "prestige": 0, "course": None,
                 "pending_course": None, "job": None, "browsing_jobs": False, "scroll": 0}
        state = {
            "stats": stats,
            "money": 40 + stats["wealth"] * 2,
            "age": 0,
            "actions_remaining": ACTIONS_PER_YEAR,
            "actions_used": {},
            "life_event_resolved": False,
            "journal": [],
            "owned": set(),
            "bought_this_year": set(),
            "activities": {},
            "scholarship": False,
            "player_traits": player_traits,
            "gender": gender,
            "attracted": orientation,
            "skills": {},
            "aspiration": random.choice(list(ASPIRATIONS)),
            "aspiration_done": False,
        }
        log(state, f"{player_name} was born. Personality: {', '.join(player_traits)}.")
        log(state, f"Aspiration: {state['aspiration']} ({ASPIRATIONS[state['aspiration']][0]}).")

    state.setdefault("gender", gender)
    state.setdefault("attracted", "Both")
    state.setdefault("skills", {})
    state.setdefault("aspiration", "Wealthy")
    state.setdefault("aspiration_done", False)
    ensure_profiles(people + friends + ([partner] if partner else []), resume["age"] if resume else 0)

    def near_age(age_now):
        if age_now < 18:
            return max(3, age_now + random.randint(-1, 1))
        return max(18, age_now + random.randint(-8, 8))

    def make_friend():
        p = make_person("Friend", "friend", age=near_age(state["age"]))
        friends.append(p)
        return p

    active_tab = "Life"
    people_scroll = 0
    profile_person = None
    profile_note = ""
    journal_scroll = 0
    panel_open = False
    last_regions = {"toggle": pygame.Rect(0, 0, 0, 0), "tabs": {}, "age_up": pygame.Rect(0, 0, 0, 0),
                    "skip": pygame.Rect(0, 0, 0, 0)}
    last_tab_buttons = {}
    next_rect = None
    skip_left = 0

    age = resume["age"] if resume else 0
    clock = pygame.time.Clock()

    while True:
        stage = get_age_stage(age)
        state["age"] = age
        ctx = {"career": career, "partner": partner, "friends": friends, "people": people,
               "money": state["money"], "stats": stats}
        year_events = pick_year_events(
            age, ctx, choice_events[stage]["choices"], special_events.get(stage, {}),
            last_event_text.get(stage), recent=recent_events)
        last_event_text[stage] = year_events[0][0]
        recent_events.extend(t for t, _ in year_events)
        del recent_events[:-12]

        # save at the start of every year so you can continue later
        snapshot_state = {k: (sorted(v) if k == "owned" else v) for k, v in state.items()
                          if k not in ("actions_used", "bought_this_year")}
        save_game({"gender": gender, "name": player_name, "hair_colour": list(hair_colour),
                   "hairstyle": hairstyle, "skin_tone": list(skin_tone), "facial_hair": facial_hair,
                   "stats": stats, "history": stats_history, "last_event_text": last_event_text,
                   "recent_events": recent_events, "people": people, "friends": friends,
                   "partner": partner, "career": career, "state": snapshot_state, "age": age})

        event_index = 0
        choice_text, option_data = year_events[0]
        options = list(option_data.keys())
        selected_option = None
        chosen_index = None
        result_text = ""
        next_rect = None

        state["actions_remaining"] = ACTIONS_PER_YEAR
        state["actions_used"] = {}
        state["bought_this_year"] = set()
        state["life_event_resolved"] = False

        if skip_left > 0:
            # skipping ahead: events resolve on their own
            for text, data in year_events:
                pick = random.choice(list(data.keys()))
                apply_consequence(state, data[pick])
                log(state, f"{text} You chose: {pick}.")
            waiting = False
        else:
            waiting = True

        while waiting:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if profile_person is not None:
                            profile_person = None
                            continue
                        return
                    if event.key == pygame.K_SPACE and profile_person is None:
                        waiting = False

                if event.type == pygame.MOUSEWHEEL:
                    if active_tab == "Journal":
                        journal_scroll -= event.y
                    elif active_tab == "People" and profile_person is None:
                        people_scroll = max(0, people_scroll - event.y)
                    elif active_tab == "Career":
                        career["scroll"] = max(0, career.get("scroll", 0) - event.y)

                if event.type == pygame.MOUSEMOTION and active_tab == "Life" and chosen_index is None:
                    selected_option = None
                    for index, orect in enumerate(get_option_rects(len(options), CONTENT_RECT)):
                        if orect.collidepoint(event.pos):
                            selected_option = index

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos

                    if last_regions["toggle"].collidepoint(mx, my):
                        panel_open = not panel_open
                        continue

                    if panel_open:
                        clicked_tab = None
                        for tab_name, trect in last_regions["tabs"].items():
                            if trect.collidepoint(mx, my):
                                clicked_tab = tab_name
                                break
                        if clicked_tab:
                            active_tab = clicked_tab
                        panel_open = False
                        continue

                    if active_tab == "People" and profile_person is not None:
                        outcome = handle_profile_click(mx, my, CONTENT_RECT, profile_person, state, age)
                        if outcome == "back":
                            profile_person = None
                        elif outcome:
                            profile_note = outcome
                            log(state, outcome)
                        continue

                    if last_regions["age_up"].collidepoint(mx, my):
                        waiting = False
                        continue
                    if last_regions["skip"].collidepoint(mx, my):
                        skip_left = SKIP_YEARS - 1
                        log(state, f"Skipped ahead {SKIP_YEARS} years.")
                        waiting = False
                        continue

                    if active_tab == "Life":
                        if chosen_index is None:
                            for index, orect in enumerate(get_option_rects(len(options), CONTENT_RECT)):
                                if orect.collidepoint(mx, my):
                                    outcome = apply_consequence(state, option_data[options[index]])
                                    chosen_index = index
                                    result_text = describe(outcome)
                                    log(state, f"{choice_text} You chose: {options[index]}.")
                                    state["life_event_resolved"] = event_index == len(year_events) - 1
                                    break
                        elif next_rect and next_rect.collidepoint(mx, my) and event_index < len(year_events) - 1:
                            event_index += 1
                            choice_text, option_data = year_events[event_index]
                            options = list(option_data.keys())
                            chosen_index = None
                            selected_option = None
                            result_text = ""

                    elif active_tab == "People":
                        result = handle_people_click(mx, my, CONTENT_RECT, people, friends, partner,
                                                     people_scroll, state, age)
                        if isinstance(result, tuple):
                            if result[0] == "profile":
                                profile_person, profile_note = result[1], ""
                            elif result[0] == "ask":
                                msg = ask_for_money(result[1], state, age)
                                log(state, msg)
                                profile_note = msg
                            result = None
                        if result == "meet":
                            if len(friends) < 6:
                                new_friend = make_friend()
                                log(state, f"Made a new friend: {new_friend['name']}.")
                        elif result == "partner":
                            want = state.get("attracted", "Both")
                            cg = "Male" if want == "Men" else "Female" if want == "Women" else random.choice(["Male", "Female"])
                            cage = max(16 if age < 18 else 18, near_age(age))
                            cand = make_person("Partner", "partner", cg, closeness=50, age=cage)
                            cand["compat"] = compatibility(state["player_traits"], cand["traits"])
                            chance = 0.2 + 0.5 * (stats["looks"] + stats["social"]) / 200 + (cand["compat"] - 50) / 200
                            if not is_attracted(cand["attracted"], gender):
                                log(state, f"Asked {cand['name']} out, but they weren't interested.")
                            elif random.random() < max(0.05, min(0.95, chance)):
                                partner = cand
                                log(state, f"Started dating {partner['name']} ({partner['compat']}% match).")
                            else:
                                log(state, "Asked someone out and got turned down.")
                        elif result == "propose" and partner:
                            score = (partner["closeness"] + partner["trust"] + partner["romance"]) / 3
                            chance = max(0.05, min(0.95, (score - 40) / 50 + 0.15 + (partner.get("compat", 50) - 50) / 200))
                            state["money"] = max(0, state["money"] - PROPOSAL_COST)
                            if random.random() < chance:
                                partner["married"] = True
                                partner["relation"] = "Spouse"
                                stats["social"] = min(100, stats["social"] + 4)
                                stats["mental"] = min(100, stats["mental"] + 3)
                                log(state, f"Married {partner['name']}!")
                            else:
                                partner["closeness"] = max(0, partner["closeness"] - 10)
                                log(state, f"Proposed to {partner['name']}, who wasn't ready.")
                        elif result == "baby" and partner:
                            same_sex = partner.get("gender") == gender
                            if random.random() < (0.5 if partner.get("married") else 0.35) * (0.85 if same_sex else 1):
                                kid = make_child(state["player_traits"] + partner["traits"])
                                kid["look"]["skin"] = list(random.choice([skin_tone, tuple(partner["look"]["skin"])]))
                                people.append(kid)
                                stats["mental"] = min(100, stats["mental"] + 2)
                                log(state, ("Adopted " if same_sex else "Welcomed ") + f"{'son' if kid['relation'] == 'Son' else 'daughter'} {kid['name']}.")
                            else:
                                log(state, "The adoption didn't go through this year." if same_sex else "Tried for a baby but no luck this year.")

                    elif active_tab == "Education":
                        before = career["enrolled"]
                        handle_education_click(mx, my, last_tab_buttons, age, state, career)
                        if career["enrolled"] and not before:
                            what = f"a {career['uni_target']}" + (f" in {career['course']}" if career["course"] else "")
                            log(state, f"Started {what} at {career['college_name']}.")
                        elif before and not career["enrolled"]:
                            log(state, "Left university.")

                    elif active_tab == "Career":
                        before_job = career["job"]["title"] if career["job"] else None
                        handle_career_click(mx, my, last_tab_buttons, career, state)
                        after_job = career["job"]["title"] if career["job"] else None
                        if after_job != before_job:
                            log(state, f"Started working as a {after_job}." if after_job else f"Left the job as a {before_job}.")

                    elif active_tab == "Activities":
                        handle_activities_click(mx, my, last_tab_buttons, state, age, friends, make_friend,
                                                lambda t: log(state, t))

                    elif active_tab == "Shop":
                        handle_shop_click(mx, my, last_tab_buttons, state, age, lambda t: log(state, t))

            for stat in displayed_stats:
                displayed_stats[stat] = lerp(displayed_stats[stat], stats[stat], 0.15)

            last_regions = draw_hub_frame(
                screen, player_name, age, stage, stats, displayed_stats,
                hair_colour, hairstyle, skin_tone, facial_hair, gender,
                icons, background, stage_backgrounds[stage],
                active_tab, panel_open, state, mouse_pos
            )

            if active_tab == "Life":
                next_rect = draw_life_tab(screen, CONTENT_RECT, choice_text, options, selected_option,
                                          mouse_pos, chosen_index is not None, chosen_index,
                                          result_text, event_index < len(year_events) - 1,
                                          event_index + 1, len(year_events))
            elif active_tab == "People":
                if career["job"]:
                    meet_label = "Meet a Coworker"
                elif age < 18:
                    meet_label = "Meet Someone at School"
                else:
                    meet_label = "Meet Someone New"
                if profile_person is not None:
                    draw_profile(screen, CONTENT_RECT, profile_person, mouse_pos, state, age)
                    if profile_note:
                        draw_text(screen, profile_note, small_font, DARK_GREY, CONTENT_RECT.x + 190, CONTENT_RECT.bottom - 62)
                else:
                    people_scroll = draw_people_tab(screen, CONTENT_RECT, people, friends, partner,
                                                    people_scroll, mouse_pos, state, age, meet_label)
            elif active_tab == "Education":
                last_tab_buttons = draw_education_tab(screen, CONTENT_RECT, mouse_pos, age, state, career)
            elif active_tab == "Career":
                last_tab_buttons = draw_career_tab(screen, CONTENT_RECT, mouse_pos, career, state)
            elif active_tab == "Activities":
                last_tab_buttons = draw_activities_tab(screen, CONTENT_RECT, mouse_pos, state, age)
            elif active_tab == "Shop":
                last_tab_buttons = draw_shop_tab(screen, CONTENT_RECT, mouse_pos, state, age)
            elif active_tab == "Journal":
                journal_scroll = draw_journal_tab(screen, CONTENT_RECT, state["journal"], journal_scroll)

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)

        # ---- year end ----
        before_edu = career["education"]
        apply_yearly_decline(stats, age)
        apply_passives(state)
        advance_activities_year(state, lambda t: log(state, t))
        was_married = bool(partner and partner.get("married"))
        partner = advance_relationships(people, friends, partner, lambda t: log(state, t))
        if was_married and partner is None:
            lost = state["money"] // 4
            state["money"] -= lost
            log(state, f"The divorce cost you ${lost}.")
        if partner and partner.get("married"):
            state["money"] += 15            # a second income at home
        young_kids = [c for c in children_of(people) if c["age"] < 18]
        if young_kids:
            bill = CHILD_COST * len(young_kids)
            if state["money"] >= bill:
                state["money"] -= bill
            else:
                state["money"] = 0
                stats["mental"] = max(0, stats["mental"] - 1)
                log(state, "Money was tight raising your children.")
        partner = advance_deaths(people, friends, partner, state, lambda t: log(state, t))
        if profile_person is not None and profile_person not in people + friends + ([partner] if partner else []):
            profile_person = None
        advance_career_year(career, state, age)
        if career["education"] != before_edu:
            subject = f" in {career['course']}" if career.get("course") else ""
            log(state, f"Graduated with a {career['education']}{subject}.")
        # Wealth reflects your actual savings, so you can't "go broke" with cash in hand
        stats["wealth"] = max(stats["wealth"], min(100, state["money"] // 8))
        stats_history.append(dict(stats))
        if not state.get("aspiration_done") and ASPIRATIONS[state["aspiration"]][1](state, career, friends, partner, people):
            state["aspiration_done"] = True
            stats["mental"] = min(100, stats["mental"] + 3)
            log(state, f"Aspiration achieved: {state['aspiration']}!")

        reason = None
        failed_stat = next((s for s in VITAL_STATS if stats[s] <= 0), None)
        if failed_stat:
            reason = f"{STAT_LABELS[failed_stat]} reached 0."
        elif age >= 75:
            # natural end of life: odds rise each year, lower with poor health
            chance = (age - 74) * 0.03 + (0.04 if stats["physical"] < 30 else 0)
            if age >= 100 or random.random() < chance:
                reason = "You passed away peacefully."

        if reason:
            life_score = (age * 5 + sum(stats.values()) + state["money"] // 10 + 10 * len(children_of(people))
                          + (60 if state.get("aspiration_done") else 0))
            job = career["job"]["title"] if career["job"] else "none"
            edu = career["education"] + (f" ({career['course']})" if career.get("course") else "")
            summary = [f"Education: {edu}   Final job: {job}   Money: ${state['money']}",
                       f"Friends: {len(friends)}   Children: {len(children_of(people))}   "
                       + (f"Spouse: {partner['name']}" if partner and partner.get("married")
                          else f"Partner: {partner['name'] if partner else 'none'}"),
                       f"Aspiration ({state['aspiration']}: {ASPIRATIONS[state['aspiration']][0]}): "
                       + ("achieved!" if state.get("aspiration_done") else "not achieved")]
            delete_save()
            await game_over(screen, age, reason, stats_history, life_score, summary)
            return

        age += 1

        if skip_left > 0:
            skip_left -= 1
            # stop skipping at big moments, or when something is going badly
            if (age in MILESTONE_AGES or any(stats[s] < 20 for s in VITAL_STATS)
                    or age >= 75):
                skip_left = 0
                log(state, f"Stopped skipping at age {age}.")
            await asyncio.sleep(0)

async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("LifeForge")

    while True:
        action = await menu_screen(screen)
        if action == "start":
            await run_game(screen)
        elif action == "continue":
            data = load_game()
            if data:
                await run_game(screen, resume=data)

if __name__ == "__main__":
    asyncio.run(main())
