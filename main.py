import asyncio
import math
import pygame
from constants import fmt, fmt_short
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
import events as _events
import nightmode
import station
import stories
import publiclife
import idol
import celebrity
import pathways
import budget
import home
import gameover
import scenes
import lifeevents
import skipsummary
import kids
import titles
nightmode.install()
lifeevents.install(choice_events, _events.SITUATIONAL)
station.install()
stories.install()
import family
import scenarios
import appearance
from shop import draw_shop_tab, handle_shop_click, apply_passives
from shop import bank_auto as shop_bank_auto
import assets
import worldjobs
import love
import sports
from journal import draw_journal_tab
import lifestyle
import romance
import achievements
from people import FEMALE_HAIR, MALE_HAIR, HAIR_COLOURS, refresh_classmates
from life import yearly_costs, health_year, report_card, invest_year, retirement_year
from save import has_save, save_game, load_game, delete_save
from activities import draw_activities_tab, handle_activities_click, advance_activities_year

TABS = ["Life", "People", "Love", "Family", "Education", "Career", "Activities", "Lifestyle", "Shop", "Journal"]
TAB_LABEL = {"Education": "Learn", "Career": "Work", "Activities": "Play", "Shop": "Money"}
SKIP_YEARS = 5
MILESTONE_AGES = (7, 13, 16, 18, 21, 30, 65)
CONTENT_RECT = pygame.Rect(96, 112, 676, 560)
ACTIONS_PER_YEAR = 20

# Every life gets a random aspiration. Reach it and you get a Mental boost
# and a bonus to your final life score.
ASPIRATIONS = {
    "Wealthy":      ("have $100,000 or more",          lambda s, c, f, p, pe: s["money"] >= 100000),
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
    if state.get("age", 99) >= 18 and consequence.get("money"):
        # event amounts are written on a small scale; adults feel them in
        # proportion to what they earn
        consequence = dict(consequence)
        consequence["money"] = int(consequence["money"] * max(2, state.get("_income", 0) // 2000))
    stats = state["stats"]
    if consequence.get("act"):
        consequence = dict(consequence)
        note = lifeevents.run_act(state, consequence["act"])
        if note:
            consequence["note"] = note
            log(state, note)
    for key, value in consequence.items():
        if key in ("act", "note"):
            continue
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
    if state.get("_evt_text") is not None:
        txt = state.pop("_evt_text")
        d = describe(consequence)
        home.feed_add(state, txt, "" if d == "No change" else d)
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
    option_height = 64
    gap = 20
    total_width = option_width * count + gap * (count - 1)
    start_x = rect.centerx - total_width // 2
    y = rect.y + 172
    return [pygame.Rect(start_x + i * (option_width + gap), y, option_width, option_height)
            for i in range(count)]

def _trim(text, fnt, width):
    if fnt.size(text)[0] <= width:
        return text
    while len(text) > 1 and fnt.size(text + "...")[0] > width:
        text = text[:-1]
    return text + "..."

def render_player_stats(screen, stats, displayed_stats, icons, rect, card=True):
    """Seven stat rows: name, value and a thin bar underneath. With card=False
    they sit straight on the background."""
    if card:
        draw_card(screen, rect, radius=16)
    row_h = (rect.height - 10) // len(STAT_ORDER)
    for idx, stat in enumerate(STAT_ORDER):
        y = rect.y + 4 + idx * row_h
        draw_text(screen, STAT_LABELS[stat], font, INK, rect.x + 4, y)
        val = str(int(round(stats[stat])))
        draw_text(screen, val, font, INK, rect.right - 4 - font.size(val)[0], y)
        bar = pygame.Rect(rect.x + 4, y + 22, rect.width - 8, 8)
        draw_rounded_rect(screen, (222, 205, 196), bar, radius=4)
        filled = int(bar.width * displayed_stats[stat] / 100)
        if filled > 0:
            draw_rounded_rect(screen, STAT_COLORS[stat], (bar.x, bar.y, max(filled, 8), bar.height), radius=4)

_scene_cache = {}

def scene_background(stage_colour):
    """A calm evening backdrop drawn once: gradient sky, low sun, skyline."""
    key = tuple(stage_colour)
    surf = _scene_cache.get(key)
    if surf is not None:
        return surf
    W, H = SCREEN_WIDTH, SCREEN_HEIGHT
    top = tuple(int(lerp(c, 246, 0.7)) for c in stage_colour)
    surf = make_vertical_gradient(W, H, top, (232, 196, 178)).convert_alpha()
    sun = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.circle(sun, (242, 155, 99, 110), (545, 150), 58)
    sky = pygame.Surface((W, H), pygame.SRCALPHA)
    for x, w, h in ((470, 56, 120), (526, 64, 160), (590, 46, 100), (636, 74, 190), (710, 52, 130), (762, 70, 170), (832, 68, 110)):
        pygame.draw.rect(sky, (170, 126, 150, 70), (x, 330 - h, w, h))
        for wy in range(330 - h + 14, 320, 26):
            for wx in range(x + 10, x + w - 10, 18):
                if (wx * 7 + wy * 3) % 5 == 0:
                    pygame.draw.rect(sky, (255, 233, 168, 150), (wx, wy, 5, 7))
    surf.blit(sun, (0, 0)); surf.blit(sky, (0, 0))
    _scene_cache[key] = surf
    return surf

RAIL_W = 78

_tiny = pygame.font.Font(None, 18)

HUB_BG = ((246, 243, 251), (232, 228, 244))
NAV_BG = ((40, 54, 102), (22, 28, 62))
NAV_TXT = (196, 204, 232)
CHIP = (241, 237, 250)
_hub_bg = {}

def hub_background():
    """Light lavender page with a navy navigation rail, drawn once."""
    surf = _hub_bg.get("bg")
    if surf is None:
        surf = make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, *HUB_BG).convert_alpha()
        surf.blit(make_vertical_gradient(RAIL_W, SCREEN_HEIGHT, *NAV_BG), (0, 0))
        _hub_bg["bg"] = surf
    return surf

def _chip(screen, x, y, text, fnt=None, fg=INK, bg=CHIP, pad=10):
    fnt = fnt or small_font
    w = fnt.size(text)[0] + pad * 2
    r = pygame.Rect(x, y, w, 26)
    draw_rounded_rect(screen, bg, r, radius=13)
    draw_text(screen, text, fnt, fg, r.x + pad, r.centery - fnt.get_height() // 2)
    return r

def draw_key_stats(screen, stats, displayed_stats, x0, y0, w=58, gap=8):
    """The seven stats as compact labelled bars."""
    for i, stat in enumerate(STAT_ORDER):
        x = x0 + i * (w + gap)
        draw_text(screen, STAT_LABELS[stat], _tiny, MUTED, x, y0)
        val = str(int(round(stats[stat])))
        draw_text(screen, val, font, INK, x, y0 + 14)
        bar = pygame.Rect(x, y0 + 40, w, 7)
        draw_rounded_rect(screen, (230, 226, 240), bar, radius=4)
        filled = int(bar.w * displayed_stats[stat] / 100)
        if filled > 0:
            draw_rounded_rect(screen, STAT_COLORS[stat], (bar.x, bar.y, max(filled, 7), bar.h), radius=4)

def draw_hub_frame(screen, player_name, age, stage, stats, displayed_stats,
                   hair_colour, hairstyle, skin_tone, facial_hair, gender,
                   icons, background, fallback_bg, active_tab, panel_open, state, mouse_pos):
    stage_colour = STAGE_COLORS.get(stage, LIGHT_GREY)
    screen.blit(hub_background(), (0, 0))

    # header card: who you are, money and actions, then your key stats
    head = pygame.Rect(RAIL_W + 10, 8, SCREEN_WIDTH - RAIL_W - 18, 88)
    draw_card(screen, head, radius=16)
    name_font = title_font if title_font.size(player_name)[0] <= 300 else font
    draw_text(screen, _trim(player_name, name_font, 300), name_font, INK, head.x + 16, head.y + (6 if name_font is title_font else 16))
    x = head.x + 16
    x = _chip(screen, x, head.y + 52, f"Age {age} · {stage}").right + 6
    coin_r = _chip(screen, x, head.y + 52, "     " + fmt_short(state["money"]), fg=(150, 104, 20), bg=(255, 241, 206))
    pygame.draw.circle(screen, (240, 190, 70), (coin_r.x + 16, coin_r.centery), 7)
    pygame.draw.circle(screen, (200, 150, 40), (coin_r.x + 16, coin_r.centery), 7, 2)
    x = coin_r.right + 6
    owed = state.get("debt", 0)
    if owed:
        x = _chip(screen, x, head.y + 52, f"Debt {fmt_short(owed)}", fg=(190, 60, 60), bg=(253, 228, 228)).right + 6
    left = state["actions_remaining"]
    _chip(screen, x, head.y + 52, f"{left} actions", fg=(160, 80, 20) if left else MUTED, bg=(255, 232, 210) if left else CHIP)
    draw_key_stats(screen, stats, displayed_stats, head.right - 7 * 66 - 6, head.y + 18)

    # content: the tabs draw into CONTENT_RECT on a white card
    draw_card(screen, CONTENT_RECT.inflate(16, 14), radius=18)

    # right column: portrait (click to edit your look), then a facts card
    colx = CONTENT_RECT.right + 14
    pw, ph = SCREEN_WIDTH - colx - 8, 150
    portrait_rect = pygame.Rect(colx, 105, pw, ph)
    draw_card(screen, portrait_rect, radius=16)
    halo = pygame.Surface((pw, ph), pygame.SRCALPHA)
    pygame.draw.circle(halo, (*lerp_col(stage_colour, (255, 255, 255), 0.55), 255), (pw // 2, ph // 2 + 4), min(pw, ph) // 2 - 6)
    screen.blit(halo, portrait_rect.topleft)
    surf = pygame.Surface((pw, ph - 4), pygame.SRCALPHA)
    draw_avatar(surf, pygame.Rect(0, 0, pw, ph - 4), gender, hair_colour, hairstyle, skin_tone, facial_hair, age, stats["mental"], state.get("feat"))
    screen.blit(surf, (portrait_rect.x, portrait_rect.y + 2))
    if portrait_rect.collidepoint(mouse_pos):
        draw_text(screen, "Edit look", _tiny, MUTED, portrait_rect.centerx, portrait_rect.bottom - 10, centre=True)
    facts = pygame.Rect(colx, portrait_rect.bottom + 8, pw, 318)
    draw_card(screen, facts, radius=16)
    y = facts.y + 10
    for label, value in state.get("_snapshot", [])[:7]:
        lab = str(label).upper().replace("FRIENDS / ENEMIES", "FRIENDS").replace("FAMILY WEALTH", "WEALTH")
        draw_text(screen, _trim(lab, _tiny, pw - 16), _tiny, MUTED, facts.x + 9, y)
        draw_text(screen, _trim(str(value), small_font, pw - 16), small_font, INK, facts.x + 9, y + 13)
        y += 43

    age_up_rect, skip_rect = draw_age_up_button(screen, mouse_pos, state["life_event_resolved"])
    tab_rects = draw_nav(screen, active_tab, mouse_pos, state.get("_badge", 0))
    return {"toggle": pygame.Rect(0, 0, 0, 0), "tabs": tab_rects, "age_up": age_up_rect, "skip": skip_rect,
            "portrait": portrait_rect}

def lerp_col(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def draw_side_panel_toggle(screen, mouse_pos, badge=0):
    rect = pygame.Rect(16, 12, 78, 38)
    hovered = rect.collidepoint(mouse_pos)
    col = ACCENT if hovered else INK
    for k in range(3):
        pygame.draw.line(screen, col, (24, 24 + k * 6), (40, 24 + k * 6), 2)
    draw_text(screen, "Menu", small_font, col, 48, 24)
    if badge:
        pygame.draw.circle(screen, (225, 70, 90), (rect.right - 4, rect.y + 4), 10)
        draw_text(screen, str(badge), small_font, WHITE, rect.right - 4, rect.y + 4, centre=True)
    return rect

TAB_INFO = {
    "Life":       ("Your year", (255, 149, 66)),
    "People":     ("Family, friends, love", (236, 130, 178)),
    "Education":  ("School, uni, courses", (79, 123, 224)),
    "Career":     ("Jobs, pay, promotions", (62, 156, 134)),
    "Activities": ("Clubs, trips, hobbies", (143, 91, 214)),
    "Shop":       ("Bank, homes, cars, gear", (217, 160, 43)),
    "Journal":    ("Your story so far", (120, 112, 140)),
    "Love":       ("Matches, apps, social media", (232, 90, 120)),
    "Family":     ("Tree, heirs, inheritance", (90, 150, 110)),
    "Lifestyle":  ("Gigs, health, leisure, crime", (225, 110, 70)),
}

def _tab_icon(screen, tab, cx, cy, col):
    W = (255, 255, 255)
    pygame.draw.circle(screen, col, (cx, cy), 18)
    if tab == "Life":
        pygame.draw.circle(screen, W, (cx, cy), 7)
        for k in range(8):
            v = pygame.math.Vector2(1, 0).rotate(k * 45)
            pygame.draw.line(screen, W, (cx + v.x * 10, cy + v.y * 10), (cx + v.x * 13, cy + v.y * 13), 2)
    elif tab == "People":
        pygame.draw.circle(screen, W, (cx - 5, cy - 4), 4); pygame.draw.circle(screen, W, (cx + 6, cy - 3), 3)
        pygame.draw.ellipse(screen, W, (cx - 11, cy + 2, 12, 9)); pygame.draw.ellipse(screen, W, (cx + 1, cy + 3, 11, 8))
    elif tab == "Education":
        pygame.draw.polygon(screen, W, [(cx - 12, cy - 2), (cx, cy - 9), (cx + 12, cy - 2), (cx, cy + 5)])
        pygame.draw.rect(screen, W, (cx - 6, cy + 2, 12, 7), border_radius=2)
    elif tab == "Career":
        pygame.draw.rect(screen, W, (cx - 10, cy - 5, 20, 14), border_radius=3)
        pygame.draw.rect(screen, W, (cx - 4, cy - 9, 8, 5), 2, border_radius=2)
    elif tab == "Activities":
        pts = []
        for k in range(10):
            r = 11 if k % 2 == 0 else 5
            v = pygame.math.Vector2(0, -r).rotate(k * 36)
            pts.append((cx + v.x, cy + v.y + 1))
        pygame.draw.polygon(screen, W, pts)
    elif tab == "Family":
        pygame.draw.circle(screen, W, (cx, cy - 6), 4)
        pygame.draw.line(screen, W, (cx, cy - 2), (cx, cy + 2), 2)
        pygame.draw.line(screen, W, (cx - 8, cy + 2), (cx + 8, cy + 2), 2)
        pygame.draw.circle(screen, W, (cx - 8, cy + 7), 3); pygame.draw.circle(screen, W, (cx + 8, cy + 7), 3)
    elif tab == "Lifestyle":
        pygame.draw.polygon(screen, W, [(cx - 10, cy + 3), (cx, cy - 9), (cx + 10, cy + 3)])
        pygame.draw.rect(screen, W, (cx - 7, cy + 2, 14, 8))
    elif tab == "Love":
        pygame.draw.circle(screen, W, (cx - 4, cy - 3), 5); pygame.draw.circle(screen, W, (cx + 4, cy - 3), 5)
        pygame.draw.polygon(screen, W, [(cx - 9, cy), (cx + 9, cy), (cx, cy + 10)])
    elif tab == "Shop":
        pygame.draw.rect(screen, W, (cx - 9, cy - 3, 18, 13), border_radius=3)
        pygame.draw.arc(screen, W, (cx - 6, cy - 11, 12, 14), 0, 3.14159, 2)
    else:
        pygame.draw.rect(screen, W, (cx - 8, cy - 10, 16, 20), border_radius=3)
        for k in range(3):
            pygame.draw.line(screen, col, (cx - 4, cy - 5 + k * 5), (cx + 4, cy - 5 + k * 5), 2)

def draw_side_panel(screen, active_tab, mouse_pos, badge=0):
    scrim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    scrim.fill((40, 30, 50, 70))
    screen.blit(scrim, (0, 0))
    row_h = 58
    panel_rect = pygame.Rect(10, 58, 262, len(TABS) * row_h + 20)
    draw_shadow(screen, panel_rect, 18, 12, 60)
    pygame.draw.rect(screen, (255, 248, 240), panel_rect, border_radius=18)
    tab_rects = {}
    y = panel_rect.y + 10
    for tab in TABS:
        rect = pygame.Rect(panel_rect.x + 8, y, panel_rect.width - 16, row_h - 6)
        selected = tab == active_tab
        hovered = rect.collidepoint(mouse_pos)
        sub, col = TAB_INFO.get(tab, ("", ACCENT))
        if selected:
            pygame.draw.rect(screen, (255, 232, 210), rect, border_radius=14)
            pygame.draw.rect(screen, ACCENT, (rect.x, rect.y + 10, 4, rect.h - 20), border_radius=2)
        elif hovered:
            pygame.draw.rect(screen, (255, 240, 228), rect, border_radius=14)
        _tab_icon(screen, tab, rect.x + 30, rect.centery, col)
        draw_text(screen, tab, font, INK, rect.x + 58, rect.y + 9)
        draw_text(screen, sub, small_font, MUTED, rect.x + 58, rect.y + 29)
        if tab == "People" and badge:
            pygame.draw.circle(screen, (225, 70, 90), (rect.right - 20, rect.centery), 11)
            draw_text(screen, str(badge), small_font, WHITE, rect.right - 20, rect.centery, centre=True)
        tab_rects[tab] = rect
        y += row_h
    return tab_rects

def draw_nav(screen, active_tab, mouse_pos, badge=0):
    """The menu: a navy rail down the left, always on screen."""
    rects = {}
    h = 63
    y = 10
    for tab in TABS:
        r = pygame.Rect(0, y, RAIL_W, h - 2)
        sub, col = TAB_INFO.get(tab, ("", ACCENT))
        selected = tab == active_tab
        hovered = r.collidepoint(mouse_pos)
        cx, cy = RAIL_W // 2 + 2, r.y + 24
        if selected or hovered:
            hl = pygame.Surface((RAIL_W - 10, h - 6), pygame.SRCALPHA)
            pygame.draw.rect(hl, (255, 255, 255, 46 if selected else 20), hl.get_rect(), border_radius=12)
            screen.blit(hl, (5, r.y + 2))
        if selected:
            pygame.draw.rect(screen, ACCENT, (0, r.y + 10, 4, r.h - 20), border_radius=2)
        _tab_icon(screen, tab, cx, cy, col)
        draw_text(screen, TAB_LABEL.get(tab, tab), small_font, WHITE if selected else NAV_TXT, cx, r.y + 49, centre=True)
        if tab == "People" and badge:
            pygame.draw.circle(screen, (225, 70, 90), (cx + 16, cy - 14), 9)
            draw_text(screen, str(badge), small_font, WHITE, cx + 16, cy - 14, centre=True)
        rects[tab] = r
        y += h
    return rects

def draw_money_and_actions(screen, state, mouse_pos):
    top = pygame.Rect(0, 0, SCREEN_WIDTH, 62)
    money_rect = pygame.Rect(16, 12, 120, 38)
    coin_centre = (money_rect.x + 21, money_rect.centery)
    pygame.draw.circle(screen, (240, 190, 70), coin_centre, 12)
    pygame.draw.circle(screen, (200, 150, 40), coin_centre, 12, 2)
    draw_text(screen, "$", small_font, (120, 80, 10), coin_centre[0], coin_centre[1], centre=True)
    draw_text(screen, fmt_short(state["money"]), font, INK, money_rect.x + 40, money_rect.y + 10)
    owed = state.get("debt", 0)
    if owed:
        draw_text(screen, f"Debt ${fmt(fmt_short(owed))}", small_font, RED, money_rect.right + 8, money_rect.y + 12)

    draw_text(screen, "LifeForge", title_font, INK, SCREEN_WIDTH // 2 + 20, 31, centre=True)

    actions_rect = pygame.Rect(SCREEN_WIDTH - 214, 12, 198, 38)
    draw_text(screen, "Actions", small_font, MUTED, actions_rect.x + 14, actions_rect.y + 11)
    left, total = state["actions_remaining"], ACTIONS_PER_YEAR
    for k in range(total):
        cx = actions_rect.x + 76 + k * 5
        pygame.draw.circle(screen, ACCENT if k < left else (214, 190, 180), (cx, actions_rect.centery), 2)
    draw_text(screen, str(left), small_font, INK, actions_rect.right - 20, actions_rect.y + 11, centre=False)

def draw_age_up_button(screen, mouse_pos, resolved):
    colx = CONTENT_RECT.right + 14
    w = SCREEN_WIDTH - colx - 6
    rect = pygame.Rect(colx, 590, w, 44)
    skip_rect = pygame.Rect(colx, 642, w, 34)
    draw_pill(screen, rect, "Age Up" if resolved else "Age Up (skip)", font if resolved else small_font, mouse_pos, primary=True)
    draw_pill(screen, skip_rect, f"Skip {SKIP_YEARS} yrs", small_font, mouse_pos)
    return rect, skip_rect

def draw_latest(screen, rect, state):
    y = rect.y + 292
    draw_text(screen, "LATEST", small_font, MUTED, rect.x + 8, y)
    journal = state.get("journal", [])[-7:]
    y += 24
    if not journal:
        draw_text(screen, "Your story starts here.", font, MUTED, rect.x + 8, y)
    for a, t in reversed(journal):
        draw_text(screen, f"{a}", font, ACCENT, rect.x + 8, y)
        draw_text(screen, _trim(t, font, rect.width - 70), font, INK, rect.x + 52, y)
        y += 30

def draw_life_tab(screen, rect, choice_text, options, selected_option, mouse_pos, resolved, chosen_index,
                  result_text="", more_events=False, event_number=1, event_total=1, age=0, chip_rows=None):
    event_rect = pygame.Rect(rect.x, rect.y, rect.width, 160)
    draw_card(screen, event_rect, fill=(255, 250, 244), radius=16)
    scene_rect = pygame.Rect(event_rect.x + 10, event_rect.y + 10, 200, 140)
    scenes.draw_scene(screen, scene_rect, scenes.classify(choice_text))
    kick = f"AGE {age}" + (f"  ·  EVENT {event_number} OF {event_total}" if event_total > 1 else "")
    draw_text(screen, kick, small_font, ACCENT, event_rect.x + 226, event_rect.y + 16)
    draw_wrapped_text(screen, choice_text, font, INK, pygame.Rect(event_rect.x + 216, event_rect.y + 36, event_rect.width - 236, 112), centre=False)

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
        draw_wrapped_text(screen, option_text, small_font, WHITE if is_chosen else INK, draw_rect.inflate(0, -20).move(0, -7))
        row = (chip_rows or [])[index] if chip_rows and index < len(chip_rows) else []
        if row and not resolved:
            total = sum(home._TINY.size(t)[0] for t, _ in row) + 10 * (len(row) - 1)
            cx = draw_rect.centerx - total // 2
            for t, col in row:
                draw_text(screen, t, home._TINY, col, cx, draw_rect.bottom - 20)
                cx += home._TINY.size(t)[0] + 10

    next_rect = None
    if resolved:
        draw_text(screen, result_text, small_font, INK, rect.centerx, rect.y + 246, centre=True)
        if more_events:
            next_rect = pygame.Rect(rect.centerx - 90, rect.y + 258, 180, 30)
            draw_pill(screen, next_rect, "Next event", small_font, mouse_pos, primary=True)
    else:
        draw_text(screen, "Choose what you do, or visit the menu on the left and Age Up when ready.", home._TINY, MUTED, rect.centerx, rect.y + 252, centre=True)
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

async def game_over(screen, age, reason, history, life_score, summary, ctx=None):
    if ctx:
        return await gameover.show(screen, ctx)
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
        "Create a character: name, gender, and a full look editor (hair, eyes,",
        "lips, brows, clothes). Click your portrait any time to change it.",
        "You get 20 actions a year across the tabs. Age Up when you're ready.",
        "People and Love: family, friends, dating apps, talking stages, social media.",
        "Career, Education, Activities and Lifestyle: jobs, school, clubs, sports.",
        "Shop tab: Shop, Assets, Business (studios, startups, construction) and Bank.",
        "Parents' jobs decide your pocket money and what they give when asked.",
        "Family tab: your tree, grandchildren and who you name as heir.",
        "When your life ends you can play on as a child, partner or grandchild,",
        "keeping the property and businesses (after 10% estate tax).",
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

_menu_bg = {}

def menu_backdrop():
    """Navy night sky over a city skyline, drawn once."""
    surf = _menu_bg.get("bg")
    if surf is not None:
        return surf
    W, H = SCREEN_WIDTH, SCREEN_HEIGHT
    surf = make_vertical_gradient(W, H, (52, 60, 118), (20, 22, 52)).convert_alpha()
    rnd = random.Random(7)
    for _ in range(90):
        x, y = rnd.randint(0, W), rnd.randint(0, 380)
        pygame.draw.circle(surf, (255, 255, 255, rnd.choice([60, 120, 200])), (x, y), rnd.choice([1, 1, 2]))
    glow = pygame.Surface((W, H), pygame.SRCALPHA)
    for r_, a_ in ((80, 10), (62, 16), (48, 24)):
        pygame.draw.circle(glow, (255, 214, 170, a_), (760, 120), r_)
        surf.blit(glow, (0, 0)); glow.fill((0, 0, 0, 0))
    pygame.draw.circle(glow, (255, 236, 210, 255), (760, 120), 34)
    surf.blit(glow, (0, 0))
    x = 0
    while x < W:
        w, h = rnd.randint(40, 90), rnd.randint(90, 260)
        pygame.draw.rect(surf, (30, 30, 70), (x, H - h, w, h))
        for wy in range(H - h + 12, H - 8, 22):
            for wx in range(x + 8, x + w - 8, 14):
                if rnd.random() < 0.28:
                    pygame.draw.rect(surf, (255, 206, 130), (wx, wy, 4, 6))
        x += w + rnd.randint(0, 8)
    shade = pygame.Surface((W, H), pygame.SRCALPHA)
    for i in range(420):     # darken the left side so the menu reads clearly
        pygame.draw.line(shade, (16, 18, 46, int(200 * (1 - i / 420))), (i, 0), (i, H))
    surf.blit(shade, (0, 0))
    _menu_bg["bg"] = surf
    return surf

_MENU_CAST = [("Female", (66, 44, 34), "Wavy", 2, {"top": "Overalls", "outfit": 3, "earrings": "Hoops"}),
              ("Male", (40, 46, 66), "Quiff", 5, {"top": "Hoodie", "outfit": 9}),
              ("Female", (30, 26, 28), "Curly", 6, {"top": "Blazer", "outfit": 1})]

async def menu_screen(screen):
    from constants import SKIN_TONES
    clock = pygame.time.Clock()
    labels = (["Continue"] if has_save() else []) + ["New life", "How to play", "Exit"]
    buttons = {label: pygame.Rect(64, 300 + i * 66, 300, 54) for i, label in enumerate(labels)}
    actions = {"Continue": "continue", "New life": "start"}

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for label, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if label in actions:
                            return actions[label]
                        if label == "How to play":
                            await instructions_screen(screen)
                        if label == "Exit":
                            pygame.quit()
                            raise SystemExit

        screen.blit(menu_backdrop(), (0, 0))
        draw_text(screen, "LifeForge", title_font, WHITE, 64, 150)
        draw_text(screen, "Your story. Your choices.", font, (255, 196, 160), 66, 200)
        draw_text(screen, "Big dreams, small choices, real consequences.", small_font, (190, 196, 230), 66, 232)

        mouse_pos = pygame.mouse.get_pos()
        for n, (label, rect) in enumerate(buttons.items()):
            hovered = rect.collidepoint(mouse_pos)
            primary = n == 0
            r = rect.move(4, 0) if hovered else rect
            if primary:
                draw_rounded_rect(screen, (255, 168, 100) if hovered else (246, 120, 100), r, radius=14)
            else:
                pane = pygame.Surface(r.size, pygame.SRCALPHA)
                pygame.draw.rect(pane, (255, 255, 255, 48 if hovered else 26), pane.get_rect(), border_radius=14)
                screen.blit(pane, r.topleft)
            draw_text(screen, label, font, WHITE, r.x + 24, r.centery - font.get_height() // 2)

        # a few faces from the world, on cards
        for i, (g, hc, st, sk, ft) in enumerate(_MENU_CAST):
            card = pygame.Rect(470 + i * 138, 250 + (24 if i == 1 else 0), 126, 168)
            draw_card(screen, card, radius=16)
            draw_avatar(screen, card.inflate(-8, -8), g, hc, st, SKIN_TONES[sk], "None", 24, 80, ft)
        draw_text(screen, "Royals, idols, tycoons, or just you.", small_font, (210, 214, 240), 470, 470)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

def roll_stats():
    return {"physical": random.randint(40, 80), "mental": random.randint(40, 80),
            "social": random.randint(35, 75), "academic": random.randint(35, 80),
            "looks": random.randint(30, 85), "athletic": random.randint(30, 80),
            "wealth": random.randint(40, 65)}

async def stats_roll_screen(screen, player_name, gender, hair_colour, hairstyle, skin_tone, facial_hair, feat=None, preset=None):
    """BitLife-style: you are born with random stats and can re-roll until
    you like them."""
    clock = pygame.time.Clock()
    fallback_bg = make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, (255, 235, 240), (255, 255, 255))
    stats = dict(preset) if preset else roll_stats()
    traits = random.sample(TRAITS, 2)
    reroll = pygame.Rect(SCREEN_WIDTH // 2 - 230, 600, 210, 50)
    start = pygame.Rect(SCREEN_WIDTH // 2 + 20, 600, 210, 50)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and not preset:
                    stats = roll_stats()
                    traits = random.sample(TRAITS, 2)
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return stats, traits
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if reroll.collidepoint(event.pos) and not preset:
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
        draw_avatar(screen, portrait, gender, hair_colour, hairstyle, skin_tone, facial_hair, None, 60, feat)
        for idx, stat in enumerate(STAT_ORDER):
            y = 150 + idx * 52
            draw_text(screen, STAT_LABELS[stat], font, INK, 380, y)
            bar = pygame.Rect(530, y, 280, 26)
            draw_rounded_rect(screen, LIGHT_GREY, bar, radius=10)
            draw_rounded_rect(screen, STAT_COLORS[stat], (bar.x, bar.y, int(bar.width * stats[stat] / 100), bar.height), radius=10)
            pygame.draw.rect(screen, OUTLINE, bar, 2, border_radius=10)
            draw_text(screen, str(stats[stat]), small_font, INK, bar.x + 8, bar.y + 5)
        mouse = pygame.mouse.get_pos()
        for r, label in (((reroll, "Re-roll (R)"),) if not preset else ()) + ((start, "Start life"),):
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
        feat = resume["state"].get("feat") or {}
    else:
        sel = await character_selection_screen(screen)
        gender, player_name, hair_colour, hairstyle, skin_tone, facial_hair, orientation = sel[:7]
        feat = sel[7] if len(sel) > 7 else {}
        if gender is None:
            return
        scenario = await scenarios.scenario_screen(screen)
        preset = scenario["stats"]() if scenario.get("stats") else None
        stats, player_traits = await stats_roll_screen(screen, player_name, gender, hair_colour, hairstyle, skin_tone, facial_hair, feat, preset)

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
        state["actions_remaining"] = max(state.get("actions_remaining", 0), ACTIONS_PER_YEAR)
    else:
        people = generate_family(skin_tone, hair_colour, {k: stats[k] for k in ('looks', 'social', 'academic', 'athletic', 'mental') if k in stats}, scenario)
        celebrity.seed(people)
        friends = []
        partner = None
        career = {"education": "None", "enrolled": False, "uni_target": None, "uni_years_done": 0,
                 "college_name": None, "college_prestige": 0, "prestige": 0, "course": None,
                 "pending_course": None, "job": None, "browsing_jobs": False, "scroll": 0,
                 "side_job": None, "fame": 0, "experience": 0}
        family_wealth = worldjobs.update_family_wealth({}, people)
        state = {
            "stats": stats,
            "family_wealth": family_wealth,
            "debt": 0,
            "savings": 0,
            "invest": 0,
            "home": None,
            "money": 40 + stats["wealth"] * 2 + worldjobs.tier_value(family_wealth, {"Struggling": 0, "Comfortable": 15, "Wealthy": 60}),
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
            "feat": feat,
            "gender": gender,
            "attracted": orientation,
            "skills": {},
            "aspiration": random.choice(list(ASPIRATIONS)),
            "aspiration_done": False,
        }
        state["scenario"] = scenario["id"]
        station.setup(state, scenario["id"])
        log(state, scenario["intro"] or f"Born into a {family_wealth.lower()} family.")
        if scenario.get("title"):
            titles.grant(state, scenario["title"], log=lambda t: log(state, t))
        if scenario.get("heir_to"):
            pars = [p for p in people if p["relation"] in ("Mother", "Father")]
            if pars:
                holder = random.choice(pars)
                if scenario["heir_to"] == "king":
                    state["heir_to"] = {"kind": "king", "holder_name": holder["name"]}
                else:
                    state["heir_to"] = {"kind": "peer", "rank": random.randint(0, 3), "place": random.choice(titles.PLACES),
                                        "holder_name": holder["name"]}
                    log(state, f"Your {holder['relation'].lower()}, {holder['name']}, holds a title you will inherit.")
        if scenario["id"] == "royal2":
            log(state, "Your older sibling is first in line to the throne.")
        elif scenario["id"] == "royal1":
            log(state, "You are first in line to the throne.")
        _par = {p["relation"]: p for p in worldjobs.parents_of(people)}
        if len(_par) == 2:
            log(state, f"Your mother is a {_par['Mother']['job_title'].lower()} and your father is a {_par['Father']['job_title'].lower()}.")
        celebrity.setup(state, career, people, lambda t: log(state, t))
        log(state, f"{player_name} was born. Personality: {', '.join(player_traits)}.")
        log(state, f"Aspiration: {state['aspiration']} ({ASPIRATIONS[state['aspiration']][0]}).")

    state.setdefault("family_wealth", "Comfortable")
    state.setdefault("debt", 0)
    state.setdefault("savings", 0)
    state.setdefault("invest", 0)
    state.setdefault("home", None)
    assets.ensure(state)
    love.ensure(state)
    career.setdefault("hustle", None)
    for k, v in (("side_job", None), ("fame", 0), ("experience", 0)):
        career.setdefault(k, v)
    state.setdefault("gender", gender)
    state.setdefault("attracted", "Both")
    state.setdefault("skills", {})
    state.setdefault("aspiration", "Wealthy")
    state.setdefault("aspiration_done", False)
    lifestyle.ensure_state(state)
    if resume and state.get("econ_v", 1) < 2:
        # older saves used a much smaller money scale: bring them up
        state["money"] = int(state["money"] * 30)
        for k in ("savings", "debt", "invest"):
            state[k] = int(state.get(k, 0) * 50)
        if state.get("home"):
            state["home"]["value"] = int(state["home"]["value"] * 500)
        if state.get("pension"):
            state["pension"] *= 1000
        if career.get("job"):
            career["job"]["pay"] *= 1000
        if career.get("side_job"):
            career["side_job"]["pay"] *= 400
        if career.get("hustle"):
            career["hustle"]["pay"] *= 1000
    state["econ_v"] = 2
    ensure_profiles(people + friends + ([partner] if partner else []), resume["age"] if resume else 0)

    def make_friend():
        p = make_person("Friend", "friend", age=near_age(state["age"]))
        if career.get("job") and state["age"] >= 18 and random.random() < 0.75:
            # a colleague: a job from the same line of work, with stats to match
            p["age"] = max(19, p["age"])
            worldjobs.assign_job(p, worldjobs.coworker_job(career["job"].get("base") or career["job"]["title"]))
            p["relation"] = "Coworker"
        friends.append(p)
        return p

    active_tab = "Life"
    people_scroll = 0
    profile_person = None
    profile_note = ""
    journal_scroll = 0
    panel_open = False
    life_regions = {}
    last_regions = {"toggle": pygame.Rect(0, 0, 0, 0), "tabs": {}, "age_up": pygame.Rect(0, 0, 0, 0),
                    "skip": pygame.Rect(0, 0, 0, 0)}
    last_tab_buttons = {}
    next_rect = None
    skip_left = 0
    skip_info = None

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
                ("Job", "In prison" if state.get("jail") else (station.job_label(state, age) or idol.job_label(state) or (career["job"]["title"] if career["job"] else ("Student" if age < 18 else "Unemployed")))),
                ("Partner", (partner["name"] + (", spouse" if partner.get("married") else ", situationship" if partner.get("status") == "situationship" else "")) if partner else "Single"),
                ("Friends / enemies", f"{sum(1 for f in friends if f['category'] != 'enemy')} / {sum(1 for f in friends if f['category'] == 'enemy')}"),
                ("Home", state["home"]["name"] if state.get("home") else station.home_label(state) or ("With parents" if age < 24 and state.get("parents_ok") else budget.rental(state)[1] if age >= 18 else "Family home")),
                ("Family wealth", state.get("family_wealth", "Comfortable")),
                ("Aspiration", state.get("aspiration", "")),
                ("Fame" if fame_v else "Savings", f"{fame_v} ({__import__('career').fame_tier(fame_v)})" if fame_v else f"${fmt(state.get('savings', 0))}")]
        snap = [s_ for s_ in snap if s_[0] != "Aspiration"]
        snap[1:1] = station.snapshot_rows(state) + idol.snapshot_rows(state) + publiclife.snapshot_rows(state)
        if state.get("title"):
            snap.insert(0, ("Title", titles.label(state, gender)))
        state["_snapshot"] = snap
        state["_friends"] = friends
        state["_people"] = people
        state["_partner"] = partner
        state["_skin"] = skin_tone
        state["_has_partner"] = partner is not None
        state["_in_school"] = (5 <= age < 18) or bool(career.get("enrolled"))
        refresh_classmates(state, age, state["_in_school"], friends)
        state["_casual"] = bool(partner and partner.get("status") == "situationship")
        state["_fame"] = career.get("fame", 0)
        state["_income"] = ((career["job"]["pay"] if career["job"] else 0) + (career["side_job"]["pay"] if career.get("side_job") else 0)
                            + (career["hustle"]["pay"] // 2 if career.get("hustle") else 0))
        state["parents_ok"] = any(p["relation"] in ("Mother", "Father") and p["closeness"] >= 35 for p in people)
        state["_career"] = career
        ctx = {"title": state.get("title"), "career": career, "partner": partner, "friends": friends, "people": people,
               "money": state["money"], "stats": stats}
        year_events = pick_year_events(
            age, ctx, choice_events[stage]["choices"], special_events.get(stage, {}),
            last_event_text.get(stage), recent=recent_events)
        last_event_text[stage] = year_events[0][0]
        recent_events.extend(t for t, _ in year_events)
        del recent_events[:-12]
        _beat = stories.story_event(state, ctx, age)
        if _beat:
            year_events = year_events[:1] + [_beat]

        # save at the start of every year so you can continue later
        snapshot_state = {k: (sorted(v) if k == "owned" else v) for k, v in state.items()
                          if k not in ("actions_used", "bought_this_year") and not k.startswith("_")}
        save_game({"gender": gender, "name": player_name, "hair_colour": list(hair_colour),
                   "hairstyle": hairstyle, "skin_tone": list(skin_tone), "facial_hair": facial_hair,
                   "stats": stats, "history": stats_history, "last_event_text": last_event_text,
                   "recent_events": recent_events, "people": people, "friends": friends,
                   "partner": partner, "career": career, "state": snapshot_state, "age": age})

        if skip_info is not None and skip_left <= 0:
            after_snap = skipsummary.snapshot(state, career, people, friends, partner, stats)
            await skipsummary.show(screen, skip_info, after_snap, skipsummary.highlights(state, skip_info))
            skip_info = None

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
            inbox = (state.pop("_pending_inv", None) or []) + generate_invites(state, age, friends, partner, career.get("fame", 0), people)
            inbox = inbox[:4]
        if skip_left > 0:
            # skipping ahead: events resolve on their own
            for text, data in year_events:
                pick = lifeevents.autopilot_pick(data)
                state["_evt_text"] = text
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
                    elif active_tab == "Family":
                        state["_fam_scroll"] = max(0, state.get("_fam_scroll", 0) - event.y * 40)

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

                    if last_regions.get("portrait", pygame.Rect(0, 0, 0, 0)).collidepoint(mx, my):
                        look = {"hair": hair_colour, "style": hairstyle, "skin": skin_tone, "facial": facial_hair,
                                "feat": dict(state.get("feat") or {})}
                        look = await appearance.appearance_window(screen, look, gender, age, player_name)
                        hair_colour, hairstyle = tuple(look["hair"]), look["style"]
                        skin_tone, facial_hair = tuple(look["skin"]), look["facial"]
                        state["feat"] = look["feat"]
                        continue

                    clicked_tab = None
                    for tab_name, trect in last_regions["tabs"].items():
                        if trect.collidepoint(mx, my):
                            clicked_tab = tab_name
                            break
                    if clicked_tab:
                        active_tab = clicked_tab
                        continue

                    if active_tab in ("People", "Love") and prospect is not None:
                        secret = bool(state.get("_secret"))
                        labels = ("Start a secret fling", "Pass") if secret else ("Ask them out", "Keep it casual", "Pass")
                        pick = handle_decision_click(mx, my, CONTENT_RECT, labels)
                        if pick in ("Ask them out", "Keep it casual", "Start a secret fling"):
                            casual = pick == "Keep it casual"
                            chance = date_chance(stats, prospect, career.get("fame", 0)) + (0.2 if casual else 0)
                            if random.random() < min(0.95, chance):
                                if secret:
                                    state["fling"] = prospect
                                    state["cheat_count"] = state.get("cheat_count", 0) + 1
                                    state["cheat_years"] = 0
                                    stats["mental"] = min(100, stats["mental"] + 2)
                                    log(state, f"You started seeing {prospect['name']} behind your partner's back.")
                                else:
                                    love.add_match(state, prospect, casual)
                                    log(state, f"You and {prospect['name']} are {'seeing each other' if casual else 'talking'} ({prospect['compat']}% match). Find them in Love.")
                            else:
                                log(state, f"Asked {prospect['name']} out and got turned down.")
                            prospect = None
                            state["_secret"] = False
                        elif pick == "Pass":
                            log(state, f"Decided {prospect['name']} wasn't for you.")
                            prospect = None
                            state["_secret"] = False
                        continue

                    if inbox and active_tab in ("Life", "People") and prospect is None:
                        pick = handle_decision_click(mx, my, CONTENT_RECT, romance.LABELS[inbox[0]["kind"]])
                        if pick:
                            inv = inbox.pop(0)
                            if inv["kind"] == "surprisebaby":
                                partner = kids.resolve_surprise(inv, pick, state, people, friends, stats, skin_tone, partner,
                                                                lambda t: log(state, t))
                            elif inv["kind"] in ("cheated", "official", "temptation", "ringchoice", "weddingchoice", "proposed", "prenup", "prenupask"):
                                partner = romance.resolve_card(inv, pick, partner, friends, state, lambda t: log(state, t))
                                if inv.pop("_retry", False):
                                    inbox.insert(0, inv)
                            elif pick == "Decline":
                                decline_invite(inv, state, age, friends, lambda t: log(state, t))
                            else:
                                partner = accept_invite(inv, state, age, friends, partner, lambda t: log(state, t),
                                                        casual=(pick == "Keep it casual"))
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
                            if partner is None and random.random() < chance and (who in friends or who in state.get("classmates", [])):
                                (friends if who in friends else state["classmates"]).remove(who)
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
                        elif isinstance(outcome, tuple) and outcome[0] == "befriend" and state["actions_remaining"] > 0:
                            who = outcome[1]
                            state["actions_remaining"] -= 1
                            chance = 0.35 + who["closeness"] / 150 + stats["social"] / 400
                            if random.random() < min(0.9, chance):
                                state["classmates"].remove(who)
                                who["category"], who["relation"] = "friend", "Friend"
                                who["closeness"] = max(who["closeness"], 40)
                                friends.append(who)
                                log(state, f"{who['name']} is now your friend.")
                                profile_person = None
                            else:
                                who["closeness"] = max(0, who["closeness"] - 3)
                                profile_note = f"{who['name']} isn't ready to be friends yet."
                                log(state, profile_note)
                        elif isinstance(outcome, tuple) and outcome[0] == "merge" and state["actions_remaining"] > 0:
                            state["actions_remaining"] -= 1
                            romance.try_merge(outcome[1], state, lambda t: log(state, t))
                        elif isinstance(outcome, tuple) and outcome[0] == "breakup":
                            romance.break_up(outcome[1], friends, state, lambda t: log(state, t))
                            partner = None
                            state["_has_partner"] = False
                            profile_person = None
                        elif isinstance(outcome, tuple) and outcome[0] == "official" and state["actions_remaining"] > 0:
                            state["actions_remaining"] -= 1
                            romance.make_official(outcome[1], state, lambda t: log(state, t))
                        elif isinstance(outcome, tuple) and outcome[0] == "getback" and state["actions_remaining"] > 0:
                            who = outcome[1]
                            state["actions_remaining"] -= 1
                            if romance.get_back_together(who, state, lambda t: log(state, t)):
                                friends.remove(who)
                                partner = who
                                state["_has_partner"] = True
                                profile_person = None
                        elif outcome and isinstance(outcome, str):
                            profile_note = outcome
                            log(state, outcome)
                        continue

                    if last_regions["age_up"].collidepoint(mx, my):
                        waiting = False
                        continue
                    if last_regions["skip"].collidepoint(mx, my):
                        skip_left = SKIP_YEARS
                        skip_info = skipsummary.snapshot(state, career, people, friends, partner, stats)
                        log(state, f"Skipped ahead {SKIP_YEARS} years.")
                        waiting = False
                        continue

                    if active_tab == "Life":
                        lr = life_regions
                        if lr.get("surrender") and lr["surrender"].collidepoint(mx, my):
                            state["_surrender_ask"] = True
                            continue
                        if lr.get("sur_no") and lr["sur_no"].collidepoint(mx, my):
                            state["_surrender_ask"] = False
                            continue
                        if lr.get("sur_yes") and lr["sur_yes"].collidepoint(mx, my):
                            state["_surrender_ask"] = False
                            state["_surrender"] = True
                            waiting = False
                            continue
                        hit_person = next((p for p, r in lr.get("people", []) if r.collidepoint(mx, my)), None)
                        if hit_person is not None and not (chosen_index is None and any(o.collidepoint(mx, my) for o in get_option_rects(len(options), CONTENT_RECT))):
                            profile_person = hit_person
                            active_tab = "People"
                            continue
                        if chosen_index is None:
                            for index, orect in enumerate(get_option_rects(len(options), CONTENT_RECT)):
                                if orect.collidepoint(mx, my):
                                    state["_evt_text"] = choice_text
                                    outcome = apply_consequence(state, option_data[options[index]])
                                    chosen_index = index
                                    result_text = describe(outcome) + "  ·  " + home.feeling(outcome)
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
                            if result[0] == "tab":
                                people_scroll = 0
                            elif result[0] == "profile":
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
                        elif result == "classmate":
                            cl = state.get("classmates", [])
                            if cl:
                                c = random.choice(cl)
                                c["closeness"] = min(100, c["closeness"] + 10)
                                c["trust"] = min(100, c["trust"] + 3)
                                c["contacted"] = True
                                stats["social"] = min(100, stats["social"] + 1)
                                log(state, f"Got talking to {c['name']} from class.")
                        elif result == "propose" and partner:
                            inbox.insert(0, {"kind": "ringchoice", "person": partner,
                                             "text": f"Choose a ring for {partner['name']}.",
                                             "why": "A better ring improves your odds."})
                        elif result == "wedding" and partner:
                            inbox.insert(0, {"kind": "weddingchoice", "person": partner,
                                             "text": f"Plan your wedding with {partner['name']}.",
                                             "why": "Bigger weddings cost more but mean more."})
                        elif result == "baby" and partner:
                            same_sex = partner.get("gender") == gender
                            if same_sex:
                                # no natural pregnancy: send them to the adoption / IVF options, refund the action
                                state["actions_remaining"] += 1
                                state["actions_used"]["__baby__"] = 0
                                state["_fam_view"] = "grow"
                                active_tab = "Family"
                                log(state, "You looked into adoption, IVF and surrogacy.")
                            elif random.random() < kids.natural_chance(state, partner, age):
                                kid = kids.add_child(state, people, stats, partner, skin_tone, "born")
                                log(state, f"Welcomed {'son' if kid['relation'] == 'Son' else 'daughter'} {kid['name']}.")
                            else:
                                log(state, "Tried for a baby but no luck this year."
                                    + (" IVF or adoption (Family tab) could help." if age >= 35 else ""))

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

                    elif active_tab == "Love":
                        out = love.handle_love_click(mx, my, last_tab_buttons, state, age, career, partner, friends, lambda t: log(state, t))
                        if out and out[0] == "prospect":
                            prospect = out[1]
                            state["_secret"] = False
                        elif out and out[0] == "dm":
                            prospect = make_prospect(state, age, state["player_traits"], "Admirer")
                            log(state, f"{prospect['name']} slid into your DMs.")
                        elif out and out[0] == "official":
                            who = out[1]
                            if partner is not None:
                                romance.break_up(partner, friends, state, lambda t: log(state, t))
                            state["love"].remove(who)
                            who["category"], who["relation"] = "partner", "Partner"
                            who["romance"] = max(55, who.get("spark", 50))
                            who["closeness"] = max(who.get("closeness", 50), 55)
                            who.pop("stage", None)
                            partner = who
                            state["_has_partner"] = True
                            log(state, f"You and {who['name']} made it official!")

                    elif active_tab in ("Activities", "Lifestyle"):
                        state["_tab"] = active_tab
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
                            state["_secret"] = want == "secret"
                            if want == "plus":
                                prospect["stats"]["looks"] = min(100, prospect["stats"]["looks"] + 10)
                                prospect["stats"]["social"] = min(100, prospect["stats"]["social"] + 8)
                                prospect["compat"] = min(100, prospect["compat"] + 12)
                            if want == "celeb":
                                worldjobs.assign_job(prospect, worldjobs.BY_TITLE[random.choice(["Actor", "Singer", "Footballer", "Influencer", "Model"])])
                                prospect["stats"]["looks"] = min(100, prospect["stats"]["looks"] + 15)
                                prospect["stats"]["social"] = min(100, prospect["stats"]["social"] + 10)
                            active_tab = "People"
                        if state.pop("_date_night", None) and partner:
                            partner["closeness"] = min(100, partner["closeness"] + 6)
                            partner["romance"] = min(100, partner["romance"] + 8)

                    elif active_tab == "Journal":
                        achievements.handle_toggle_click(mx, my, CONTENT_RECT, state)

                    elif active_tab == "Family":
                        fam_out = family.handle_family_click(mx, my, last_tab_buttons, state)
                        if isinstance(fam_out, tuple) and fam_out[0] == "grow":
                            kids.perform(fam_out[1], state, people, partner, stats, skin_tone, age, lambda t: log(state, t))
                        if state.get("_surrender"):
                            waiting = False

                    elif active_tab == "Shop":
                        handle_shop_click(mx, my, last_tab_buttons, state, age, lambda t: log(state, t))

            for stat in displayed_stats:
                displayed_stats[stat] = lerp(displayed_stats[stat], stats[stat], 0.15)

            last_regions = draw_hub_frame(
                screen, titles.styled_name(state, player_name, gender), age, stage, stats, displayed_stats,
                hair_colour, hairstyle, skin_tone, facial_hair, gender,
                icons, background, stage_backgrounds[stage],
                active_tab, panel_open, state, mouse_pos
            )

            state["_badge"] = len(inbox) if active_tab not in ("Life", "People") else 0
            INVITE_HEAD = romance.HEADS
            if active_tab in ("People", "Love") and prospect is not None:
                draw_profile(screen, CONTENT_RECT, prospect, mouse_pos, state, age, mode="prospect",
                             header="Possible partner",
                             labels=("Start a secret fling", "Pass") if state.get("_secret") else ("Ask them out", "Keep it casual", "Pass"),
                             note="Check their stats, then decide.")
            elif inbox and active_tab in ("Life", "People"):
                inv = inbox[0]
                draw_profile(screen, CONTENT_RECT, inv["person"], mouse_pos, state, age, mode="invite",
                             header=INVITE_HEAD[inv["kind"]], labels=romance.LABELS[inv["kind"]], note=inv["why"])
                draw_text(screen, inv["text"], font, INK, CONTENT_RECT.x + 182, CONTENT_RECT.y + 196)
                draw_text(screen, f"Invitation 1 of {len(inbox)}", small_font, DARK_GREY, CONTENT_RECT.x + 182, CONTENT_RECT.y + 224)
            elif active_tab == "Life":
                next_rect = draw_life_tab(screen, CONTENT_RECT, choice_text, options, selected_option,
                                          mouse_pos, chosen_index is not None, chosen_index,
                                          result_text, event_index < len(year_events) - 1,
                                          event_index + 1, len(year_events), age,
                                          [home.chips(state, option_data[o]) for o in options])
                life_regions = home.draw_glance(screen, CONTENT_RECT, state, career, people, friends, partner, mouse_pos,
                                                ASPIRATIONS, CONTENT_RECT.y + 292)
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
            elif active_tab == "Family":
                last_tab_buttons = family.draw_family_tab(screen, CONTENT_RECT, mouse_pos, state, people, partner,
                                                          (gender, hair_colour, hairstyle, skin_tone, facial_hair), player_name, age)
            elif active_tab == "Education":
                last_tab_buttons = draw_education_tab(screen, CONTENT_RECT, mouse_pos, age, state, career)
            elif active_tab == "Career":
                last_tab_buttons = draw_career_tab(screen, CONTENT_RECT, mouse_pos, career, state)
            elif active_tab == "Love":
                last_tab_buttons = love.draw_love_tab(screen, CONTENT_RECT, mouse_pos, state, age, career, partner)
            elif active_tab in ("Activities", "Lifestyle"):
                state["_tab"] = active_tab
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
        if skip_left > 0:
            lifeevents.autopilot_year(state, career, people, friends, partner, lambda t: log(state, t))
        worldjobs.update_family_wealth(state, people)
        _pm = worldjobs.pocket_money(state, worldjobs.parents_of(people), worldjobs.grandparents_of(people)) if age < 18 else (0, 0)
        state["_pocket"] = _pm
        before_edu = career["education"]
        apply_yearly_decline(stats, age)
        apply_passives(state)
        advance_activities_year(state, lambda t: log(state, t), career)
        sports.sports_year(state, career, lambda t: log(state, t))
        pathways.year(state, career, age, lambda t: log(state, t))
        was_married = bool(partner and partner.get("married"))
        was_merged = bool(partner and partner.get("merged"))
        partner = advance_relationships(people, friends, partner, lambda t: log(state, t))
        partner = love.love_year(state, age, partner, friends, career, lambda t: log(state, t))
        state["_has_partner"] = partner is not None
        if was_married and partner is None:
            lost = int(state["money"] * (0.5 if was_merged else 0.25))
            state["money"] -= lost
            log(state, f"The divorce cost you ${fmt(lost)}.")
        partner, cards = romance.romance_year(
            state, age, partner, friends, lambda t: log(state, t),
            lambda: make_prospect(state, age, state["player_traits"], "Admirer"), career.get("fame", 0))
        cards = list(cards) + kids.surprise_year(state, age, partner, friends, people, career, lambda t: log(state, t))
        state["_pending_inv"] = cards
        state["_has_partner"] = partner is not None
        if partner and partner.get("married"):
            state["money"] += romance.household_income(partner)   # a second income at home
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
        titles.check_succession(state, people, lambda t: log(state, t))
        station.year(state, career, people, lambda t: log(state, t))
        idol.year(state, career, age, lambda t: log(state, t))
        publiclife.year(state, career, age, lambda t: log(state, t))
        titles.year(state, career, lambda t: log(state, t))
        family.new_sibling(people, age, lambda t: log(state, t),
                           chance=0.25 if state.get("scenario") in ("royal1", "noble") else 0.14)
        family.family_year(people, lambda t: log(state, t))
        family.heirloom_year(state)
        if profile_person is not None and profile_person not in people + friends + state.get("classmates", []) + ([partner] if partner else []):
            profile_person = None
        advance_career_year(career, state, age)
        celebrity.year(state, career, people)
        lifestyle.advance_lifestyle_year(state, career, age, lambda t: log(state, t))
        retirement_year(career, state, age)
        yearly_costs(state, career, age, state.get("parents_ok", False))
        health_year(state, age)
        report_card(state, age)
        assets.assets_year(state, age, lambda t: log(state, t))
        shop_bank_auto(state, lambda t: log(state, t))
        invest_year(state)
        if career["education"] != before_edu:
            subject = f" in {career['course']}" if career.get("course") else ""
            log(state, f"Graduated with a {career['education']}{subject}.")
        achievements.check_achievements(state, career, friends, partner, people, lambda t: log(state, t))
        # Wealth reflects your actual savings, so you can't "go broke" with cash in hand
        stats["wealth"] = max(stats["wealth"], min(100, state["money"] // 500))
        stats_history.append(dict(stats))
        if not state.get("aspiration_done") and ASPIRATIONS[state["aspiration"]][1](state, career, friends, partner, people):
            state["aspiration_done"] = True
            stats["mental"] = min(100, stats["mental"] + 3)
            log(state, f"Aspiration achieved: {state['aspiration']}!")

        reason = None
        failed_stat = next((s for s in VITAL_STATS if stats[s] <= 0), None)
        if state.get("_surrender"):
            reason = "You gave up this life."
        elif failed_stat:
            reason = f"{STAT_LABELS[failed_stat]} reached 0."
        elif age >= 75:
            # natural end of life: odds rise each year, lower with poor health
            chance = (age - 74) * 0.03 + (0.04 if stats["physical"] < 30 else 0)
            if age >= 100 or random.random() < chance:
                reason = "You passed away peacefully."

        if reason:
            life_score = (age * 5 + sum(stats.values()) + state["money"] // 1000 + 10 * len(children_of(people))
                          + (60 if state.get("aspiration_done") else 0)
                          + state.get("savings", 0) // 1000 - state.get("debt", 0) // 1000)
            job = career["job"]["title"] if career["job"] else "none"
            edu = career["education"] + (f" ({career['course']})" if career.get("course") else "")
            summary = [f"Education: {edu}   Final job: {job}   Money: ${fmt(state['money'])}",
                       f"Friends: {len(friends)}   Children: {len(children_of(people))}   Savings: ${fmt(state.get('savings', 0))}   Debt: ${fmt(state.get('debt', 0))}   "
                       + (f"Spouse: {partner['name']}" if partner and partner.get("married")
                          else f"Partner: {partner['name'] if partner else 'none'}"),
                       f"Aspiration ({state['aspiration']}: {ASPIRATIONS[state['aspiration']][0]}): "
                       + ("achieved!" if state.get("aspiration_done") else "not achieved")]
            delete_save()
            snap_state = {k: (sorted(v) if k == "owned" else v) for k, v in state.items()
                          if k not in ("actions_used", "bought_this_year") and not k.startswith("_")}
            final = {"gender": gender, "name": player_name, "hair_colour": list(hair_colour), "hairstyle": hairstyle,
                     "skin_tone": list(skin_tone), "facial_hair": facial_hair, "stats": stats, "history": stats_history,
                     "people": people, "friends": friends, "partner": partner, "career": career,
                     "state": snap_state, "age": age}
            options = family.heirs(people, partner)
            if state.get("generation", 1) > 1:
                summary.append(f"Generation {state['generation']} of the family.")
            go_ctx = {"name": player_name, "gender": gender, "age": age, "reason": reason, "life_score": life_score,
                      "look": {"hair": hair_colour, "style": hairstyle, "skin": skin_tone, "facial": facial_hair, "feat": state.get("feat")},
                      "state": snap_state, "career": career, "people": people, "friends": friends, "partner": partner, "stats": stats}
            await game_over(screen, age, reason, stats_history, life_score, summary, go_ctx)
            if options:
                nxt = await family.succession_flow(screen, final, options, age, player_name, "surrender" if state.get("_surrender") else "")
                if nxt:
                    save_game(nxt)
                    return nxt
            return None

        age += 1

        if skip_left > 0:
            skip_left -= 1
            # stop skipping at big moments, or when something is going badly
            big = any(c.get("kind") in ("proposed", "cheated", "temptation", "surprisebaby")
                      for c in (state.get("_pending_inv") or []))
            if big or any(stats[s] < 20 for s in VITAL_STATS) or age >= 80:
                skip_left = 0
                log(state, f"Stopped skipping at age {age}.")
            await asyncio.sleep(0)

async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("LifeForge")

    while True:
        action = await menu_screen(screen)
        nxt = None
        if action == "start":
            nxt = await run_game(screen)
        elif action == "continue":
            data = load_game()
            if data:
                nxt = await run_game(screen, resume=data)
        while nxt:
            nxt = await run_game(screen, resume=nxt)

if __name__ == "__main__":
    asyncio.run(main())
