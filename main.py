import asyncio
import pygame
from constants import OUTLINE, INK, MUTED, draw_card, draw_pill, draw_shadow
import random

from character import character_selection_screen, load_image, draw_avatar
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, LIGHT_GREY,
    DARK_GREY, GREEN, RED, ACCENT, STAGE_COLORS, STAT_COLORS, STAT_ORDER, VITAL_STATS, STAT_LABELS,
    font, small_font, title_font, draw_text, draw_rounded_rect,
    lerp, make_vertical_gradient
)
from choices import choice_events, special_events
from people import (near_age, make_prospect, generate_invites, accept_invite, decline_invite, date_chance, handle_decision_click,
                    ensure_profiles, advance_deaths, ask_for_money, draw_profile, handle_profile_click, is_attracted,
                    gender_word, remember, generate_family, draw_people_tab, handle_people_click, make_person, advance_relationships,
                    TRAITS, compatibility, make_child, children_of, PROPOSAL_COST, CHILD_COST)
from education import draw_education_tab, handle_education_click
from career import draw_career_tab, handle_career_click, advance_career_year
from events import pick_year_events, describe
from shop import draw_shop_tab, handle_shop_click, apply_passives
from journal import draw_journal_tab
import lifestyle
import achievements
from people import FEMALE_HAIR, MALE_HAIR, HAIR_COLOURS
from life import yearly_costs, health_year, report_card, invest_year, retirement_year
from save import has_save, save_game, load_game, delete_save
from activities import draw_activities_tab, handle_activities_click, advance_activities_year

TABS = ["Life", "People", "Education", "Career", "Activities", "Shop", "Journal"]
SKIP_YEARS = 5
MILESTONE_AGES = (7, 13, 16, 18, 21, 30, 65)
CONTENT_RECT = pygame.Rect(200, 320, 675, 320)
ACTIONS_PER_YEAR = 12

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
    if state.get("age", 99) < 18 and consequence.get("money", 0) < 0:
        # children never pay: their family covers the cost
        consequence = dict(consequence)
        consequence["money"] = 0
        consequence["covered"] = 1
    stats = state["stats"]
    for key, value in consequence.items():
        if key == "person":
            who, fx = value
            for k, v in fx.items():
                who[k] = max(0, min(100, who[k] + v))
            who["contacted"] = True
            continue
        if key == "covered":
            continue
        if key == "new_enemy":
            fl = state.get("_friends")
            if fl is not None:
                rival = make_person("Rival", "enemy", None, 10, age=near_age(state["age"]))
                rival["conflict"] = 55
                fl.append(rival)
                log(state, f"{rival['name']} has become your rival.")
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
            draw_text(screen, line, selected_font, colour, rect.centerx, y + selected_font.get_height() // 2, centre=True)
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

def _trim(text, fnt, width):
    if fnt.size(text)[0] <= width:
        return text
    while len(text) > 1 and fnt.size(text + "...")[0] > width:
        text = text[:-1]
    return text + "..."

def render_player_stats(screen, stats, displayed_stats, icons, rect):
    """Seven stat rows inside a card: a coloured dot, the name, the value,
    and a smooth bar underneath."""
    draw_card(screen, rect, radius=16)
    row_h = (rect.height - 20) // len(STAT_ORDER)
    for idx, stat in enumerate(STAT_ORDER):
        y = rect.y + 12 + idx * row_h
        pygame.draw.circle(screen, STAT_COLORS[stat], (rect.x + 20, y + 8), 6)
        draw_text(screen, STAT_LABELS[stat], small_font, INK, rect.x + 34, y)
        val = str(int(round(stats[stat])))
        draw_text(screen, val, small_font, MUTED, rect.right - 14 - small_font.size(val)[0], y)
        bar = pygame.Rect(rect.x + 14, y + 17, rect.width - 28, 8)
        draw_rounded_rect(screen, (234, 231, 242), bar, radius=4)
        filled = int(bar.width * displayed_stats[stat] / 100)
        if filled > 0:
            draw_rounded_rect(screen, STAT_COLORS[stat], (bar.x, bar.y, max(filled, 8), bar.height), radius=4)

def draw_side_panel_toggle(screen, mouse_pos, badge=0):
    rect = pygame.Rect(16, 12, 78, 38)
    draw_pill(screen, rect, "Menu", small_font, mouse_pos)
    if badge:
        pygame.draw.circle(screen, (225, 70, 90), (rect.right - 4, rect.y + 4), 10)
        draw_text(screen, str(badge), small_font, WHITE, rect.right - 4, rect.y + 4, centre=True)
    return rect

def draw_side_panel(screen, active_tab, mouse_pos):
    panel_rect = pygame.Rect(16, 58, 184, len(TABS) * 46 + 16)
    draw_card(screen, panel_rect, radius=16)
    tab_rects = {}
    y = panel_rect.y + 10
    for tab in TABS:
        rect = pygame.Rect(panel_rect.x + 10, y, panel_rect.width - 20, 40)
        selected = tab == active_tab
        hovered = rect.collidepoint(mouse_pos)
        if selected:
            draw_rounded_rect(screen, ACCENT, rect, radius=12)
        elif hovered:
            draw_rounded_rect(screen, (255, 236, 218), rect, radius=12)
        draw_text(screen, tab, font, WHITE if selected else INK, rect.centerx, rect.centery, centre=True)
        tab_rects[tab] = rect
        y += 46
    return tab_rects

def draw_money_and_actions(screen, state, mouse_pos):
    top = pygame.Rect(0, 0, SCREEN_WIDTH, 62)
    money_rect = pygame.Rect(104, 12, 120, 38)
    draw_card(screen, money_rect, radius=19, shadow=False)
    coin_centre = (money_rect.x + 21, money_rect.centery)
    pygame.draw.circle(screen, (240, 190, 70), coin_centre, 12)
    pygame.draw.circle(screen, (200, 150, 40), coin_centre, 12, 2)
    draw_text(screen, "$", small_font, (120, 80, 10), coin_centre[0], coin_centre[1], centre=True)
    draw_text(screen, str(state["money"]), font, INK, money_rect.x + 40, money_rect.y + 10)
    owed = state.get("debt", 0)
    if owed:
        draw_text(screen, f"Debt ${owed}", small_font, RED, money_rect.right + 8, money_rect.y + 12)

    draw_text(screen, "LifeForge", title_font, INK, SCREEN_WIDTH // 2 + 20, 31, centre=True)

    actions_rect = pygame.Rect(SCREEN_WIDTH - 214, 12, 198, 38)
    draw_card(screen, actions_rect, radius=19, shadow=False)
    draw_text(screen, "Actions", small_font, MUTED, actions_rect.x + 14, actions_rect.y + 11)
    left, total = state["actions_remaining"], ACTIONS_PER_YEAR
    for k in range(total):
        cx = actions_rect.x + 84 + k * 8
        pygame.draw.circle(screen, ACCENT if k < left else (225, 221, 235), (cx, actions_rect.centery), 2 if k >= left else 3)
    draw_text(screen, str(left), small_font, INK, actions_rect.right - 20, actions_rect.y + 11, centre=False)

def draw_age_up_button(screen, mouse_pos, resolved):
    rect = pygame.Rect(SCREEN_WIDTH // 2 - 230, 652, 230, 40)
    skip_rect = pygame.Rect(SCREEN_WIDTH // 2 + 10, 652, 210, 40)
    draw_pill(screen, rect, "Age Up" if resolved else "Age Up (skip event)", font if resolved else small_font, mouse_pos, primary=True)
    draw_pill(screen, skip_rect, f"Skip {SKIP_YEARS} years", small_font, mouse_pos)
    return rect, skip_rect

def draw_hub_frame(screen, player_name, age, stage, stats, displayed_stats,
                   hair_colour, hairstyle, skin_tone, facial_hair, gender,
                   icons, background, fallback_bg, active_tab, panel_open, state, mouse_pos):
    if background:
        screen.blit(background, (0, 0))
    else:
        screen.blit(fallback_bg, (0, 0))

    stage_colour = STAGE_COLORS.get(stage, LIGHT_GREY)
    strong = tuple(max(0, int(c * 0.78)) for c in stage_colour)

    # left column: portrait, name, life snapshot
    portrait_rect = pygame.Rect(20, 70, 172, 190)
    draw_card(screen, portrait_rect, radius=18)
    back = pygame.Surface((portrait_rect.w - 12, portrait_rect.h - 12))
    back.blit(make_vertical_gradient(back.get_width(), back.get_height(), strong, stage_colour), (0, 0))
    mask = pygame.Surface(back.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=14)
    back = back.convert_alpha(); back.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    screen.blit(back, (portrait_rect.x + 6, portrait_rect.y + 6))
    draw_avatar(screen, pygame.Rect(portrait_rect.x + 6, portrait_rect.y + 6, portrait_rect.w - 12, portrait_rect.h - 12),
                gender, hair_colour, hairstyle, skin_tone, facial_hair, age, stats["mental"])

    name_card = pygame.Rect(20, 270, 172, 62)
    draw_card(screen, name_card, radius=14)
    draw_text(screen, _trim(player_name, font, 150), font, INK, name_card.centerx, name_card.y + 20, centre=True)
    draw_text(screen, f"Age {age}  |  {stage}", small_font, MUTED, name_card.centerx, name_card.y + 43, centre=True)

    snap = state.get("_snapshot", [])
    if snap:
        snap_rect = pygame.Rect(20, 344, 172, 296)
        draw_card(screen, snap_rect, radius=16)
        y = snap_rect.y + 12
        for label, value in snap[:7]:
            draw_text(screen, label, small_font, MUTED, snap_rect.x + 12, y)
            draw_text(screen, _trim(str(value), small_font, 148), small_font, INK, snap_rect.x + 12, y + 16)
            y += 40

    # centre: latest news
    news_rect = pygame.Rect(204, 70, 420, 232)
    draw_card(screen, news_rect, radius=16)
    draw_text(screen, "Latest", font, INK, news_rect.x + 16, news_rect.y + 12)
    journal = state.get("journal", [])[-7:]
    y = news_rect.y + 42
    if not journal:
        draw_text(screen, "Your story starts here.", small_font, MUTED, news_rect.x + 16, y)
    for a, t in reversed(journal):
        draw_text(screen, f"{a}", small_font, ACCENT, news_rect.x + 16, y)
        draw_text(screen, _trim(t, small_font, news_rect.w - 66), small_font, INK, news_rect.x + 46, y)
        y += 26

    render_player_stats(screen, stats, displayed_stats, icons, pygame.Rect(636, 70, 244, 232))

    # a card behind the active tab's content
    draw_card(screen, CONTENT_RECT.inflate(18, 16), radius=18, alpha=215)

    toggle_rect = draw_side_panel_toggle(screen, mouse_pos, state.get("_badge", 0))
    draw_money_and_actions(screen, state, mouse_pos)
    age_up_rect, skip_rect = draw_age_up_button(screen, mouse_pos, state["life_event_resolved"])

    tab_rects = {}
    if panel_open:
        tab_rects = draw_side_panel(screen, active_tab, mouse_pos)

    return {"toggle": toggle_rect, "tabs": tab_rects, "age_up": age_up_rect, "skip": skip_rect}

def draw_life_tab(screen, rect, choice_text, options, selected_option, mouse_pos, resolved, chosen_index,
                  result_text="", more_events=False, event_number=1, event_total=1):
    event_rect = pygame.Rect(rect.x, rect.y, rect.width, 92)
    draw_card(screen, event_rect, fill=(255, 250, 244), radius=14)
    pygame.draw.rect(screen, ACCENT, (event_rect.x, event_rect.y + 14, 5, event_rect.h - 28), border_radius=3)
    draw_wrapped_text(screen, choice_text, font, INK, event_rect.inflate(-40, 0).move(8, 0))
    if event_total > 1:
        draw_text(screen, f"Event {event_number} of {event_total}", small_font, MUTED, event_rect.right - 108, event_rect.y + 8)

    rects = get_option_rects(len(options), rect)
    for index, (option_text, orect) in enumerate(zip(options, rects)):
        is_chosen = resolved and index == chosen_index
        hovered = (not resolved) and (orect.collidepoint(mouse_pos) or selected_option == index)
        if resolved:
            fill_colour = ACCENT if is_chosen else (240, 238, 245)
        else:
            fill_colour = (255, 236, 218) if hovered else WHITE
        draw_rect = orect.move(0, -3) if hovered else orect
        draw_card(screen, draw_rect, fill=fill_colour, radius=14, shadow=not resolved or is_chosen)
        if hovered:
            pygame.draw.rect(screen, ACCENT, draw_rect, 2, border_radius=14)
        draw_wrapped_text(screen, option_text, small_font, WHITE if is_chosen else INK, draw_rect)

    next_rect = None
    if resolved:
        draw_text(screen, result_text, small_font, INK, rect.centerx, rect.y + 192, centre=True)
        if more_events:
            next_rect = pygame.Rect(rect.centerx - 90, rect.y + 218, 180, 38)
            draw_pill(screen, next_rect, "Next event", small_font, mouse_pos, primary=True)
        else:
            draw_text(screen, "Use the Menu to visit People, Education, Career or Shop, then Age Up.",
                      small_font, MUTED, rect.centerx, rect.y + 232, centre=True)
    return next_rect

def draw_life_graph(screen, history, rect):
    draw_rounded_rect(screen, WHITE, rect, radius=8)
    pygame.draw.rect(screen, OUTLINE, rect, 2, border_radius=8)

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
        draw_text(screen, stat_name.title(), small_font, INK, lx + 10, ly - 9)
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
        draw_text(screen, f"Your life ended at age {age}.", font, INK, SCREEN_WIDTH // 2, 98, centre=True)
        draw_text(screen, reason, font, INK, SCREEN_WIDTH // 2, 126, centre=True)
        draw_text(screen, f"Life Score: {life_score}", font, ACCENT, SCREEN_WIDTH // 2, 158, centre=True)

        draw_life_graph(screen, history, pygame.Rect(100, 190, 700, 170))

        y = 380
        for line in summary:
            draw_text(screen, line, small_font, INK, SCREEN_WIDTH // 2, y, centre=True)
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
        draw_text(screen, "How to Play", title_font, INK, SCREEN_WIDTH // 2, 50, centre=True)

        panel = pygame.Rect(60, 90, SCREEN_WIDTH - 120, 460)
        draw_rounded_rect(screen, WHITE, panel, radius=12)
        pygame.draw.rect(screen, OUTLINE, panel, 2, border_radius=12)

        y = 118
        for line in instructions:
            draw_text(screen, line, font, INK, 85, y)
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

        draw_text(screen, "LifeForge", title_font, INK, SCREEN_WIDTH // 2, 150, centre=True)
        draw_text(screen, "Every choice shapes the life you live.", small_font, DARK_GREY,
                  SCREEN_WIDTH // 2, 200, centre=True)

        mouse_pos = pygame.mouse.get_pos()
        for label, rect in buttons.items():
            hovered = rect.collidepoint(mouse_pos)
            fill_colour = ACCENT if hovered else WHITE
            draw_rect = rect.move(0, -3) if hovered else rect
            draw_rounded_rect(screen, fill_colour, draw_rect, radius=12)
            pygame.draw.rect(screen, OUTLINE, draw_rect, 2, border_radius=12)
            draw_text(screen, label, font, INK, draw_rect.centerx, draw_rect.centery, centre=True)

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
        draw_text(screen, f"{player_name}'s starting stats", title_font, INK, SCREEN_WIDTH // 2, 55, centre=True)
        draw_text(screen, "Everyone is born different. Re-roll until you like them.", small_font, DARK_GREY,
                  SCREEN_WIDTH // 2, 95, centre=True)
        draw_text(screen, "Personality: " + ", ".join(traits), font, INK, SCREEN_WIDTH // 2, 125, centre=True)
        portrait = pygame.Rect(90, 150, 220, 220)
        draw_rounded_rect(screen, WHITE, portrait, radius=12)
        pygame.draw.rect(screen, OUTLINE, portrait, 2, border_radius=12)
        draw_avatar(screen, portrait, gender, hair_colour, hairstyle, skin_tone, facial_hair)
        for idx, stat in enumerate(STAT_ORDER):
            y = 150 + idx * 52
            draw_text(screen, STAT_LABELS[stat], font, INK, 380, y)
            bar = pygame.Rect(530, y, 280, 26)
            draw_rounded_rect(screen, LIGHT_GREY, bar, radius=10)
            draw_rounded_rect(screen, STAT_COLORS[stat], (bar.x, bar.y, int(bar.width * stats[stat] / 100), bar.height), radius=10)
            pygame.draw.rect(screen, OUTLINE, bar, 2, border_radius=10)
            draw_text(screen, str(stats[stat]), small_font, INK, bar.x + 8, bar.y + 5)
        mouse = pygame.mouse.get_pos()
        for r, label in ((reroll, "Re-roll (R)"), (start, "Start life")):
            draw_rounded_rect(screen, ACCENT if r.collidepoint(mouse) else WHITE, r, radius=10)
            pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=10)
            draw_text(screen, label, font, INK, r.centerx, r.centery, centre=True)
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
        people = generate_family(skin_tone, hair_colour, {k: stats[k] for k in ('looks', 'social', 'academic', 'athletic', 'mental') if k in stats})
        friends = []
        partner = None
        career = {"education": "None", "enrolled": False, "uni_target": None, "uni_years_done": 0,
                 "college_name": None, "college_prestige": 0, "prestige": 0, "course": None,
                 "pending_course": None, "job": None, "browsing_jobs": False, "scroll": 0,
                 "side_job": None, "fame": 0, "experience": 0}
        family_wealth = random.choices(["Struggling", "Comfortable", "Wealthy"], weights=[30, 50, 20])[0]
        state = {
            "stats": stats,
            "family_wealth": family_wealth,
            "debt": 0,
            "savings": 0,
            "invest": 0,
            "home": None,
            "money": 40 + stats["wealth"] * 2 + {"Struggling": 0, "Comfortable": 15, "Wealthy": 60}[family_wealth],
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
        log(state, f"Born into a {family_wealth.lower()} family.")
        log(state, f"{player_name} was born. Personality: {', '.join(player_traits)}.")
        log(state, f"Aspiration: {state['aspiration']} ({ASPIRATIONS[state['aspiration']][0]}).")

    state.setdefault("family_wealth", "Comfortable")
    state.setdefault("debt", 0)
    state.setdefault("savings", 0)
    state.setdefault("invest", 0)
    state.setdefault("home", None)
    career.setdefault("hustle", None)
    for k, v in (("side_job", None), ("fame", 0), ("experience", 0)):
        career.setdefault(k, v)
    state.setdefault("gender", gender)
    state.setdefault("attracted", "Both")
    state.setdefault("skills", {})
    state.setdefault("aspiration", "Wealthy")
    state.setdefault("aspiration_done", False)
    lifestyle.ensure_state(state)
    ensure_profiles(people + friends + ([partner] if partner else []), resume["age"] if resume else 0)

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
        edu_line = career["education"] + (f" ({career['course']})" if career.get("course") else "")
        if career["enrolled"]:
            edu_line = f"Studying {career['uni_target']}"
        elif age < 18:
            edu_line = "In school"
        fame_v = career.get("fame", 0)
        snap = [("Education", edu_line if edu_line != "None" else "No degree"),
                ("Job", "In prison" if state.get("jail") else (career["job"]["title"] if career["job"] else ("Student" if age < 18 else "Unemployed"))),
                ("Partner", (partner["name"] + (", spouse" if partner.get("married") else "")) if partner else "Single"),
                ("Friends / enemies", f"{sum(1 for f in friends if f['category'] != 'enemy')} / {sum(1 for f in friends if f['category'] == 'enemy')}"),
                ("Home", state["home"]["name"] if state.get("home") else ("With parents" if age < 24 and state.get("parents_ok") else "Renting" if age >= 18 else "Family home")),
                ("Family wealth", state.get("family_wealth", "Comfortable")),
                ("Aspiration", state.get("aspiration", "")),
                ("Fame" if fame_v else "Savings", f"{fame_v} ({__import__('career').fame_tier(fame_v)})" if fame_v else f"${state.get('savings', 0)}")]
        snap = [s_ for s_ in snap if s_[0] != "Aspiration"]
        state["_snapshot"] = snap
        state["_friends"] = friends
        state["_has_partner"] = partner is not None
        state["_fame"] = career.get("fame", 0)
        state["parents_ok"] = any(p["relation"] in ("Mother", "Father") and p["closeness"] >= 35 for p in people)
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
                          if k not in ("actions_used", "bought_this_year") and not k.startswith("_")}
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

        inbox = []
        prospect = None
        if skip_left <= 0 and age >= 5:
            inbox = generate_invites(state, age, friends, partner, career.get("fame", 0), people)
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

                    if active_tab == "People" and prospect is not None:
                        pick = handle_decision_click(mx, my, CONTENT_RECT, ("Ask them out", "Pass"))
                        if pick == "Ask them out":
                            chance = date_chance(stats, prospect, career.get("fame", 0))
                            if random.random() < chance:
                                prospect["category"], prospect["relation"] = "partner", "Partner"
                                partner = prospect
                                state["_has_partner"] = True
                                log(state, f"Started dating {partner['name']} ({partner['compat']}% match).")
                            else:
                                log(state, f"Asked {prospect['name']} out and got turned down.")
                            prospect = None
                        elif pick == "Pass":
                            log(state, f"Decided {prospect['name']} wasn't for you.")
                            prospect = None
                        continue

                    if inbox and active_tab in ("Life", "People") and prospect is None:
                        pick = handle_decision_click(mx, my, CONTENT_RECT, ("Accept", "Decline"))
                        if pick:
                            inv = inbox.pop(0)
                            if pick == "Accept":
                                partner = accept_invite(inv, state, age, friends, partner, lambda t: log(state, t))
                            else:
                                decline_invite(inv, state, age, friends, lambda t: log(state, t))
                            state["_has_partner"] = partner is not None
                            continue
                        if not (last_regions["age_up"].collidepoint(mx, my) or last_regions["skip"].collidepoint(mx, my)):
                            continue

                    if active_tab == "People" and profile_person is not None:
                        outcome = handle_profile_click(mx, my, CONTENT_RECT, profile_person, state, age)
                        if outcome == "back":
                            profile_person = None
                        elif isinstance(outcome, tuple) and outcome[0] == "askout":
                            who = outcome[1]
                            state["actions_remaining"] -= 1
                            chance = min(0.95, date_chance(stats, who, career.get("fame", 0)) + (who["closeness"] - 40) / 150)
                            if partner is None and random.random() < chance and who in friends:
                                friends.remove(who)
                                who["category"], who["relation"], who["romance"] = "partner", "Partner", 45
                                who["compat"] = compatibility(state["player_traits"], who["traits"])
                                partner = who
                                state["_has_partner"] = True
                                log(state, f"{who['name']} said yes. You're dating now!")
                                profile_person = None
                            else:
                                who["closeness"] = max(0, who["closeness"] - 6)
                                profile_note = f"{who['name']} just wants to stay friends."
                                log(state, profile_note)
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
                            if len(friends) < 8:
                                new_friend = make_friend()
                                if random.random() < 0.12:
                                    new_friend["category"], new_friend["relation"] = "enemy", "Rival"
                                    new_friend["conflict"], new_friend["closeness"] = 50, 10
                                    log(state, f"You and {new_friend['name']} didn't get along at all.")
                                else:
                                    log(state, f"Made a new friend: {new_friend['name']}.")
                        elif result == "partner":
                            prospect = make_prospect(state, age, state["player_traits"])
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
                                kid = make_child(state["player_traits"] + partner["traits"], [stats, partner["stats"]])
                                kid["look"]["skin"] = list(random.choice([skin_tone, tuple(partner["look"]["skin"])]))
                                people.append(kid)
                                stats["mental"] = min(100, stats["mental"] + 2)
                                log(state, ("Adopted " if same_sex else "Welcomed ") + f"{'son' if kid['relation'] == 'Son' else 'daughter'} {kid['name']}.")
                            else:
                                log(state, "The adoption didn't go through this year." if same_sex else "Tried for a baby but no luck this year.")

                    elif active_tab in ("Education", "Career") and state.get("jail"):
                        log(state, "You can't do that while you're in prison.")

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
                                                lambda t: log(state, t), career)
                        req = state.pop("_hair_change", None)
                        if req == "colour":
                            hair_colour = random.choice(HAIR_COLOURS + [(215, 185, 110), (200, 60, 40), (230, 120, 170), (60, 100, 190)])
                        elif req == "style":
                            hairstyle = random.choice(FEMALE_HAIR if gender == "Female" else MALE_HAIR)
                        want = state.pop("_want_prospect", None)
                        if want:
                            prospect = make_prospect(state, age, state["player_traits"],
                                                     "Celebrity" if want == "celeb" else "Partner")
                            if want == "celeb":
                                prospect["job_title"] = random.choice(["Actor", "Singer", "Athlete", "Influencer"])
                                prospect["stats"]["looks"] = min(100, prospect["stats"]["looks"] + 15)
                                prospect["stats"]["social"] = min(100, prospect["stats"]["social"] + 10)
                            active_tab = "People"
                        if state.pop("_date_night", None) and partner:
                            partner["closeness"] = min(100, partner["closeness"] + 6)
                            partner["romance"] = min(100, partner["romance"] + 8)

                    elif active_tab == "Journal":
                        achievements.handle_toggle_click(mx, my, CONTENT_RECT, state)

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

            state["_badge"] = len(inbox) if active_tab not in ("Life", "People") else 0
            INVITE_HEAD = {"dance": "School dance", "date": "Date invite", "friend": "Friend request", "hangout": "Invitation"}
            if active_tab == "People" and prospect is not None:
                draw_profile(screen, CONTENT_RECT, prospect, mouse_pos, state, age, mode="prospect",
                             header="Possible partner", labels=("Ask them out", "Pass"),
                             note="Check their stats, then decide.")
            elif inbox and active_tab in ("Life", "People"):
                inv = inbox[0]
                draw_profile(screen, CONTENT_RECT, inv["person"], mouse_pos, state, age, mode="invite",
                             header=INVITE_HEAD[inv["kind"]], labels=("Accept", "Decline"), note=inv["why"])
                draw_text(screen, inv["text"], font, INK, CONTENT_RECT.x + 182, CONTENT_RECT.y + 196)
                draw_text(screen, f"Invitation 1 of {len(inbox)}", small_font, DARK_GREY, CONTENT_RECT.x + 182, CONTENT_RECT.y + 224)
            elif active_tab == "Life":
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
                last_tab_buttons = draw_activities_tab(screen, CONTENT_RECT, mouse_pos, state, age, career)
            elif active_tab == "Shop":
                last_tab_buttons = draw_shop_tab(screen, CONTENT_RECT, mouse_pos, state, age)
            elif active_tab == "Journal":
                jv = state.get("_jview", "log")
                achievements.draw_view_toggle(screen, CONTENT_RECT, mouse_pos, jv)
                if jv == "awards":
                    journal_scroll = achievements.draw_awards(screen, CONTENT_RECT, state, journal_scroll)
                elif jv == "stuff":
                    achievements.draw_belongings(screen, CONTENT_RECT, state)
                else:
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
        lifestyle.advance_lifestyle_year(state, career, age, lambda t: log(state, t))
        retirement_year(career, state, age)
        yearly_costs(state, career, age, state.get("parents_ok", False))
        health_year(state, age)
        report_card(state, age)
        invest_year(state)
        if career["education"] != before_edu:
            subject = f" in {career['course']}" if career.get("course") else ""
            log(state, f"Graduated with a {career['education']}{subject}.")
        achievements.check_achievements(state, career, friends, partner, people, lambda t: log(state, t))
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
                          + (60 if state.get("aspiration_done") else 0)
                          + state.get("savings", 0) // 10 - state.get("debt", 0) // 10)
            job = career["job"]["title"] if career["job"] else "none"
            edu = career["education"] + (f" ({career['course']})" if career.get("course") else "")
            summary = [f"Education: {edu}   Final job: {job}   Money: ${state['money']}",
                       f"Friends: {len(friends)}   Children: {len(children_of(people))}   Savings: ${state.get('savings', 0)}   Debt: ${state.get('debt', 0)}   "
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
