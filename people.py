import random
import pygame
from constants import (
    WHITE, BLACK, LIGHT_GREY, DARK_GREY, GREEN, ACCENT,
    font, small_font, draw_text, draw_rounded_rect
)

NAME_POOL_MALE = ["James", "Daniel", "Michael", "David", "Ethan", "Noah",
                  "Lucas", "Henry", "Jack", "Oliver", "Leo", "Samuel"]
NAME_POOL_FEMALE = ["Emma", "Olivia", "Sophia", "Ava", "Mia", "Grace",
                    "Chloe", "Lily", "Ella", "Zoe", "Ruby", "Freya"]

CATEGORY_COLOURS = {
    "family": (90, 140, 230),
    "friend": (76, 175, 120),
    "partner": (220, 90, 140),
}

INTERACTIONS = {
    "Talk":     {"closeness": 4,  "mental": 1},
    "Hang Out": {"closeness": 7,  "social": 2, "physical": 1},
    "Argue":    {"closeness": -9, "mental": -2},
    "Gift":     {"closeness": 11, "wealth": -5, "social": 1},
}

def random_name(gender):
    return random.choice(NAME_POOL_MALE if gender == "Male" else NAME_POOL_FEMALE)

def make_person(relation, category, gender=None, closeness=60):
    gender = gender or random.choice(["Male", "Female"])
    return {
        "name": random_name(gender),
        "relation": relation,
        "category": category,
        "closeness": closeness,
    }

def generate_family():
    """A starting cast of relatives — parents, grandparents on both sides,
    and a random number of siblings (some full, some half or step)."""
    family = [
        make_person("Mother", "family", "Female", closeness=68),
        make_person("Father", "family", "Male", closeness=68),
    ]
    for side in ("Paternal", "Maternal"):
        family.append(make_person(f"{side} Grandfather", "family", "Male", closeness=55))
        family.append(make_person(f"{side} Grandmother", "family", "Female", closeness=55))

    sibling_count = random.randint(0, 3)
    for _ in range(sibling_count):
        sib_type = random.choices(
            ["Sibling", "Half-Sibling", "Step-Sibling"], weights=[70, 20, 10]
        )[0]
        family.append(make_person(sib_type, "family", closeness=60))

    return family

def apply_interaction(person, action, stats):
    """Returns True if the interaction happened, False if it couldn't
    (e.g. not enough wealth to give a gift)."""
    effects = INTERACTIONS[action]
    if action == "Gift" and stats["wealth"] < 5:
        return False

    person["closeness"] = max(0, min(100, person["closeness"] + effects["closeness"]))
    for stat, value in effects.items():
        if stat == "closeness":
            continue
        stats[stat] = max(0, min(100, stats[stat] + value))
    return True

def all_people(people, friends, partner):
    combined = []
    if partner:
        combined.append(partner)
    combined.extend(people)
    combined.extend(friends)
    return combined

def get_people_layout(rect, people, friends, partner, scroll_offset):
    """Shared layout math for the People tab — used by both the drawing
    code and the click handler so they can never fall out of sync."""
    combined = all_people(people, friends, partner)
    row_h = 58
    visible_count = max(rect.height // row_h, 1)
    scroll_offset = max(0, min(scroll_offset, max(len(combined) - visible_count, 0)))
    visible = combined[scroll_offset: scroll_offset + visible_count]

    rows = []
    y = rect.y
    for person in visible:
        row_rect = pygame.Rect(rect.x, y, rect.width, row_h - 8)
        button_w = 82
        gap = 6
        start_x = row_rect.right - (button_w * 4 + gap * 3)
        buttons = {}
        for i, action in enumerate(("Talk", "Hang Out", "Argue", "Gift")):
            bx = start_x + i * (button_w + gap)
            buttons[action] = pygame.Rect(bx, row_rect.y + row_rect.height // 2 - 12, button_w, 24)
        rows.append((person, row_rect, buttons))
        y += row_h

    return rows, combined, scroll_offset

def draw_people_tab(screen, rect, people, friends, partner, scroll_offset,
                    mouse_pos, interacted_this_year, meet_label):
    meet_rect = pygame.Rect(rect.x, rect.y, 190, 32)
    partner_rect = pygame.Rect(rect.x + 200, rect.y, 190, 32)

    meet_hovered = meet_rect.collidepoint(mouse_pos)
    meet_done = "__meet__" in interacted_this_year
    fill = LIGHT_GREY if meet_done else (ACCENT if meet_hovered else WHITE)
    draw_rounded_rect(screen, fill, meet_rect, radius=8)
    pygame.draw.rect(screen, BLACK, meet_rect, 2, border_radius=8)
    draw_text(screen, meet_label, small_font, BLACK, meet_rect.centerx, meet_rect.centery, centre=True)

    if partner is None:
        partner_hovered = partner_rect.collidepoint(mouse_pos)
        partner_done = "__partner__" in interacted_this_year
        fill = LIGHT_GREY if partner_done else (ACCENT if partner_hovered else WHITE)
        draw_rounded_rect(screen, fill, partner_rect, radius=8)
        pygame.draw.rect(screen, BLACK, partner_rect, 2, border_radius=8)
        draw_text(screen, "Look for a Partner", small_font, BLACK,
                  partner_rect.centerx, partner_rect.centery, centre=True)

    list_rect = pygame.Rect(rect.x, rect.y + 42, rect.width, rect.height - 42)
    rows, combined, scroll_offset = get_people_layout(list_rect, people, friends, partner, scroll_offset)

    if not combined:
        draw_text(screen, "No relationships yet.", small_font, DARK_GREY,
                  list_rect.centerx, list_rect.centery, centre=True)

    for person, row_rect, buttons in rows:
        draw_rounded_rect(screen, WHITE, row_rect, radius=8)
        pygame.draw.rect(screen, BLACK, row_rect, 1, border_radius=8)

        tag_colour = CATEGORY_COLOURS.get(person["category"], LIGHT_GREY)
        pygame.draw.circle(screen, tag_colour, (row_rect.x + 16, row_rect.centery), 6)

        draw_text(screen, person["name"], small_font, BLACK, row_rect.x + 28, row_rect.y + 6)
        draw_text(screen, person["relation"], small_font, DARK_GREY, row_rect.x + 28, row_rect.y + 26)

        bar_rect = pygame.Rect(row_rect.x + 170, row_rect.centery - 6, 90, 12)
        draw_rounded_rect(screen, LIGHT_GREY, bar_rect, radius=6)
        filled = int(bar_rect.width * person["closeness"] / 100)
        if filled > 0:
            draw_rounded_rect(screen, tag_colour, (bar_rect.x, bar_rect.y, filled, bar_rect.height), radius=6)

        person_key = id(person)
        already_done = person_key in interacted_this_year
        for action, brect in buttons.items():
            hovered = brect.collidepoint(mouse_pos)
            fill = LIGHT_GREY if already_done else (ACCENT if hovered else WHITE)
            draw_rounded_rect(screen, fill, brect, radius=6)
            pygame.draw.rect(screen, BLACK, brect, 1, border_radius=6)
            draw_text(screen, action, small_font, BLACK, brect.centerx, brect.centery, centre=True)

    return scroll_offset

def handle_people_click(mx, my, rect, people, friends, partner, scroll_offset,
                        interacted_this_year, stats):
    """Returns "meet" if the Meet button was clicked, "partner" if the Look
    for a Partner button was clicked, or None otherwise. Interaction button
    clicks (Talk/Hang Out/Argue/Gift) are applied directly and also return
    None — the caller only needs to react to "meet" and "partner"."""
    meet_rect = pygame.Rect(rect.x, rect.y, 190, 32)
    partner_rect = pygame.Rect(rect.x + 200, rect.y, 190, 32)

    if meet_rect.collidepoint(mx, my) and "__meet__" not in interacted_this_year:
        interacted_this_year.add("__meet__")
        return "meet"

    if partner is None and partner_rect.collidepoint(mx, my) and "__partner__" not in interacted_this_year:
        interacted_this_year.add("__partner__")
        return "partner"

    list_rect = pygame.Rect(rect.x, rect.y + 42, rect.width, rect.height - 42)
    rows, combined, _ = get_people_layout(list_rect, people, friends, partner, scroll_offset)

    for person, row_rect, buttons in rows:
        person_key = id(person)
        if person_key in interacted_this_year:
            continue
        for action, brect in buttons.items():
            if brect.collidepoint(mx, my):
                if apply_interaction(person, action, stats):
                    interacted_this_year.add(person_key)
                return None

    return None