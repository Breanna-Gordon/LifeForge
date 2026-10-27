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

# Each interaction can be used a limited number of times per person per
# year (not just once) — this still stops infinite stat-farming on a
# single person, but lets you actually talk to someone more than once.
MAX_USES_PER_PERSON_ACTION = 2
GIFT_COST = 15
PARTNER_MIN_AGE = 16
MARRY_MIN_AGE = 18
PROPOSAL_COST = 50
MAX_CHILDREN = 4
CHILD_COST = 12

CLASHES = {("hot-tempered", "hot-tempered"): -20, ("jealous", "jealous"): -10, ("jealous", "outgoing"): -12,
           ("hot-tempered", "shy"): -12, ("hot-tempered", "jealous"): -10}
COMPLEMENTS = {("outgoing", "shy"): 8, ("introverted", "kind"): 8, ("ambitious", "loyal"): 8,
               ("funny", "shy"): 6, ("kind", "hot-tempered"): 6, ("outgoing", "funny"): 6}

def compatibility(a_traits, b_traits):
    """0-100 match between two people's personalities. Shared traits help,
    some pairs clash, and kind or loyal partners are easier to get along with."""
    score = 50
    score += 12 * len(set(a_traits) & set(b_traits))
    for x in a_traits:
        for y in b_traits:
            score += CLASHES.get((x, y), CLASHES.get((y, x), 0))
            score += COMPLEMENTS.get((x, y), COMPLEMENTS.get((y, x), 0))
    if "kind" in a_traits or "kind" in b_traits: score += 4
    if "loyal" in a_traits or "loyal" in b_traits: score += 4
    return max(5, min(98, score))

def children_of(people):
    return [c for c in people if c.get("is_child")]

def make_child(parent_traits):
    gender = random.choice(["Male", "Female"])
    child = make_person("Son" if gender == "Male" else "Daughter", "family", gender, closeness=70)
    child["age"] = 0
    child["is_child"] = True
    child["trust"] = 65
    inherited = random.choice(parent_traits) if parent_traits else random.choice(TRAITS)
    child["traits"] = list({inherited, random.choice(TRAITS)})
    return child

TRAITS = ["kind", "hot-tempered", "outgoing", "introverted", "loyal", "shy", "funny", "ambitious", "jealous"]
TRUST_FX = {"Talk": 2, "Hang Out": 3, "Argue": -6, "Gift": 1}
ROMANCE_FX = {"Talk": 3, "Hang Out": 6, "Argue": -8, "Gift": 6}

INTERACTIONS = {
    "Talk":     {"closeness": 4,  "mental": 1},
    "Hang Out": {"closeness": 7,  "social": 2, "physical": 1},
    "Argue":    {"closeness": -9, "mental": -2},
    "Gift":     {"closeness": 11, "social": 1},  # money cost handled separately
}

def random_name(gender):
    return random.choice(NAME_POOL_MALE if gender == "Male" else NAME_POOL_FEMALE)

def make_person(relation, category, gender=None, closeness=60):
    gender = gender or random.choice(["Male", "Female"])
    return {
        "name": random_name(gender),
        "relation": relation,
        "category": category,
        "closeness": closeness,          # the bond / friendship
        "trust": max(0, closeness - 5),
        "conflict": 0,
        "traits": random.sample(TRAITS, 2),
        "romance": 45 if category == "partner" else 0,
        "contacted": False,
        "years": 0,                      # years together (partners)
        "married": False,
        "compat": 50,
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

def trait_modifier(person, action):
    t = person["traits"]
    m = 1.0
    if action == "Argue":
        if "kind" in t: m *= 0.5
        if "hot-tempered" in t: m *= 1.5
    elif action == "Hang Out":
        if "outgoing" in t: m *= 1.3
        if "shy" in t or "introverted" in t: m *= 0.8
    elif action == "Talk":
        if "shy" in t: m *= 0.8
        if "funny" in t: m *= 1.2
    return m

def apply_interaction(person, action, state):
    """`state` is the shared per-run dict with "stats", "money" and
    "actions_remaining". Returns True if the interaction happened.
    Personality changes how strongly each person reacts."""
    if state["actions_remaining"] <= 0:
        return False

    effects = INTERACTIONS[action]
    if action == "Gift":
        if state["money"] < GIFT_COST:
            return False
        state["money"] -= GIFT_COST

    stats = state["stats"]
    t = person["traits"]
    m = trait_modifier(person, action)
    person["closeness"] = max(0, min(100, person["closeness"] + round(effects["closeness"] * m)))

    trust = TRUST_FX[action]
    if trust < 0 and "loyal" in t:
        trust //= 2
    person["trust"] = max(0, min(100, person["trust"] + trust))

    if action == "Argue":
        person["conflict"] = min(100, person["conflict"] + round(15 * (1.5 if "hot-tempered" in t else 1)))
    else:
        person["conflict"] = max(0, person["conflict"] - 3)

    if person["category"] == "partner":
        gain = ROMANCE_FX[action]
        if gain > 0:   # a good personality match makes romance grow faster
            gain = round(gain * (0.7 + 0.6 * person.get("compat", 50) / 100))
        person["romance"] = max(0, min(100, person["romance"] + gain))

    for stat, value in effects.items():
        if stat == "closeness":
            continue
        stats[stat] = max(0, min(100, stats[stat] + value))
    if action == "Talk" and "funny" in t:
        stats["mental"] = min(100, stats["mental"] + 1)
    if action == "Talk" and "ambitious" in t:
        stats["academic"] = min(100, stats["academic"] + 1)
    if action == "Hang Out" and "introverted" in state.get("player_traits", []):
        stats["mental"] = max(0, stats["mental"] - 1)

    person["contacted"] = True
    state["actions_remaining"] -= 1
    return True

def advance_relationships(people, friends, partner, log):
    """Year end: relationships you ignore fade, friends can drift away,
    partners can break up (or divorce), and children grow up.
    Returns the (possibly ended) partner."""
    for person in people + friends + ([partner] if partner else []):
        neglected = not person.get("contacted")
        if neglected:
            loss = {"family": 2, "friend": 5, "partner": 6}.get(person["category"], 3)
            if person.get("is_child") and person.get("age", 18) < 13:
                loss = 3
            if "loyal" in person["traits"]:
                loss = max(1, loss - 2)
            person["closeness"] = max(0, person["closeness"] - loss)
            person["trust"] = max(0, person["trust"] - 2)
            if person["category"] == "partner":
                person["romance"] = max(0, person["romance"] - 6)
        person["conflict"] = max(0, person["conflict"] - 5)
        person["contacted"] = False
        if person.get("is_child"):
            person["age"] += 1
            if person["age"] == 18:
                log(f"{person['name']} turned 18.")

    for f in list(friends):
        if f["closeness"] <= 8:
            friends.remove(f)
            log(f"You and {f['name']} drifted apart.")

    if partner:
        partner["years"] = partner.get("years", 0) + 1
        chance = 0.4
        if partner.get("compat", 50) < 40: chance += 0.15
        if partner.get("married"): chance *= 0.6
        if ((partner["closeness"] < 25 or partner["conflict"] >= 80 or partner["trust"] < 15)
                and random.random() < chance):
            log(f"{partner['name']} ended the {'marriage' if partner.get('married') else 'relationship'}.")
            return None
    return partner

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
        button_w = 76
        gap = 5
        start_x = row_rect.right - (button_w * 4 + gap * 3)
        buttons = {}
        for i, action in enumerate(("Talk", "Hang Out", "Argue", "Gift")):
            bx = start_x + i * (button_w + gap)
            buttons[action] = pygame.Rect(bx, row_rect.y + row_rect.height // 2 - 12, button_w, 24)
        rows.append((person, row_rect, buttons))
        y += row_h

    return rows, combined, scroll_offset

def draw_people_tab(screen, rect, people, friends, partner, scroll_offset,
                    mouse_pos, state, age, meet_label):
    actions_used = state["actions_used"]

    meet_rect = pygame.Rect(rect.x, rect.y, 190, 32)
    partner_rect = pygame.Rect(rect.x + 200, rect.y, 190, 32)
    baby_rect = pygame.Rect(rect.x + 400, rect.y, 190, 32)

    meet_done = actions_used.get("__meet__", 0) >= 1
    meet_hovered = meet_rect.collidepoint(mouse_pos)
    fill = LIGHT_GREY if (meet_done or state["actions_remaining"] <= 0) else (ACCENT if meet_hovered else WHITE)
    draw_rounded_rect(screen, fill, meet_rect, radius=8)
    pygame.draw.rect(screen, BLACK, meet_rect, 2, border_radius=8)
    draw_text(screen, meet_label, small_font, BLACK, meet_rect.centerx, meet_rect.centery, centre=True)

    def small_btn(r, label, disabled):
        hovered = r.collidepoint(mouse_pos)
        fill = LIGHT_GREY if disabled else (ACCENT if hovered else WHITE)
        draw_rounded_rect(screen, fill, r, radius=8)
        pygame.draw.rect(screen, BLACK, r, 2, border_radius=8)
        draw_text(screen, label, small_font, BLACK, r.centerx, r.centery, centre=True)

    no_budget = state["actions_remaining"] <= 0
    if partner is None:
        old_enough = age >= PARTNER_MIN_AGE
        label = "Look for a Partner" if old_enough else f"Partner (from age {PARTNER_MIN_AGE})"
        small_btn(partner_rect, label, actions_used.get("__partner__", 0) >= 1 or not old_enough or no_budget)
    elif not partner.get("married"):
        small_btn(partner_rect, f"Propose (${PROPOSAL_COST})", age < MARRY_MIN_AGE or no_budget
                  or actions_used.get("__propose__", 0) >= 1 or state["money"] < PROPOSAL_COST)
    else:
        small_btn(partner_rect, "Married", True)
    if partner is not None and age < 46 and len(children_of(people)) < MAX_CHILDREN:
        small_btn(baby_rect, "Try for a baby", age < MARRY_MIN_AGE or no_budget or actions_used.get("__baby__", 0) >= 1)

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
        rel = person["relation"] + (f", {person['age']}" if person.get("is_child") else "")
        traits = ", ".join(person["traits"])
        options = ([f"{rel}, {person.get('compat', 50)}% match: {traits}", f"{rel}, {person.get('compat', 50)}% match"]
                   if person["category"] == "partner" else [f"{rel}: {traits}"])
        sub = next((o for o in options + [rel] if small_font.size(o)[0] < 190), rel)
        draw_text(screen, sub, small_font, DARK_GREY, row_rect.x + 28, row_rect.y + 26)

        # top bar = bond, middle = trust (partner: bottom = romance); red dot = open conflict
        bx = row_rect.x + 222
        rows_ = [(person["closeness"], tag_colour), (person["trust"], (120, 120, 130))]
        if person["category"] == "partner":
            rows_.append((person["romance"], CATEGORY_COLOURS["partner"]))
        for n, (val, colr) in enumerate(rows_):
            bar_rect = pygame.Rect(bx, row_rect.y + 7 + n * 11, 80, 8)
            draw_rounded_rect(screen, LIGHT_GREY, bar_rect, radius=4)
            filled = int(bar_rect.width * val / 100)
            if filled > 0:
                draw_rounded_rect(screen, colr, (bar_rect.x, bar_rect.y, filled, bar_rect.height), radius=4)
        if person["conflict"] >= 40:
            pygame.draw.circle(screen, (215, 80, 80), (bx - 8, row_rect.centery), 5)

        person_key = id(person)
        for action, brect in buttons.items():
            uses = actions_used.get((person_key, action), 0)
            maxed = uses >= MAX_USES_PER_PERSON_ACTION
            no_budget = state["actions_remaining"] <= 0
            hovered = brect.collidepoint(mouse_pos)
            fill = LIGHT_GREY if (maxed or no_budget) else (ACCENT if hovered else WHITE)
            draw_rounded_rect(screen, fill, brect, radius=6)
            pygame.draw.rect(screen, BLACK, brect, 1, border_radius=6)
            label = action if uses == 0 else f"{action} ({uses}/{MAX_USES_PER_PERSON_ACTION})"
            draw_text(screen, label, small_font, BLACK, brect.centerx, brect.centery, centre=True)

    return scroll_offset

def handle_people_click(mx, my, rect, people, friends, partner, scroll_offset, state, age):
    """Returns "meet", "partner", "propose" or "baby" when one of the top
    buttons is used, or None otherwise."""
    actions_used = state["actions_used"]

    meet_rect = pygame.Rect(rect.x, rect.y, 190, 32)
    partner_rect = pygame.Rect(rect.x + 200, rect.y, 190, 32)
    baby_rect = pygame.Rect(rect.x + 400, rect.y, 190, 32)

    if state["actions_remaining"] <= 0:
        return None

    if meet_rect.collidepoint(mx, my) and actions_used.get("__meet__", 0) < 1:
        actions_used["__meet__"] = 1
        state["actions_remaining"] -= 1
        return "meet"

    if (partner is None and age >= PARTNER_MIN_AGE and partner_rect.collidepoint(mx, my)
            and actions_used.get("__partner__", 0) < 1):
        actions_used["__partner__"] = 1
        state["actions_remaining"] -= 1
        return "partner"

    if (partner is not None and not partner.get("married") and age >= MARRY_MIN_AGE
            and partner_rect.collidepoint(mx, my) and actions_used.get("__propose__", 0) < 1
            and state["money"] >= PROPOSAL_COST):
        actions_used["__propose__"] = 1
        state["actions_remaining"] -= 1
        return "propose"

    if (partner is not None and age >= MARRY_MIN_AGE and age < 46 and baby_rect.collidepoint(mx, my)
            and actions_used.get("__baby__", 0) < 1 and len(children_of(people)) < MAX_CHILDREN):
        actions_used["__baby__"] = 1
        state["actions_remaining"] -= 1
        return "baby"

    list_rect = pygame.Rect(rect.x, rect.y + 42, rect.width, rect.height - 42)
    rows, combined, _ = get_people_layout(list_rect, people, friends, partner, scroll_offset)

    for person, row_rect, buttons in rows:
        person_key = id(person)
        for action, brect in buttons.items():
            if not brect.collidepoint(mx, my):
                continue
            uses = actions_used.get((person_key, action), 0)
            if uses >= MAX_USES_PER_PERSON_ACTION:
                return None
            if apply_interaction(person, action, state):
                actions_used[(person_key, action)] = uses + 1
            return None

    return None
