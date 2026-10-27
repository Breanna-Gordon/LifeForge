import random
import pygame
from constants import (
    WHITE, BLACK, LIGHT_GREY, DARK_GREY, GREEN, ACCENT, SKIN_TONES,
    font, small_font, draw_text, draw_rounded_rect
)
from avatar import draw_avatar

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
    child["attracted"] = random_attraction(gender)
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

FEMALE_HAIR = ["Long", "Long", "Long", "Ponytail", "Curly"]
MALE_HAIR = ["Short", "Short", "Buzzcut", "Spiky", "Curly", "Bald", "Mohawk"]
HAIR_COLOURS = [(35, 28, 24), (60, 40, 30), (110, 70, 35), (190, 140, 60), (150, 50, 30), (20, 20, 20), (90, 60, 45)]
JOB_TITLES = ["nurse", "teacher", "electrician", "accountant", "chef", "designer", "mechanic", "shop manager",
              "engineer", "journalist", "paramedic", "postal worker", "librarian", "builder", "dentist", "driver"]

def gender_word(g):
    return "Men" if g == "Male" else "Women"

def is_attracted(attracted, gender):
    """attracted is "Men", "Women" or "Both"; gender is "Male" / "Female"."""
    return attracted == "Both" or attracted == gender_word(gender)

def random_attraction(gender):
    roll = random.random()
    straight = "Women" if gender == "Male" else "Men"
    gay = "Men" if gender == "Male" else "Women"
    return straight if roll < 0.86 else (gay if roll < 0.93 else "Both")

def random_look(gender, age=30, skin=None, hair=None):
    pool = FEMALE_HAIR if gender == "Female" else MALE_HAIR
    if age >= 50 and gender == "Male":
        pool = ["Short", "Short", "Buzzcut", "Bald"]
    elif age >= 40:
        pool = [h for h in pool if h not in ("Mohawk", "Spiky")]
    style = random.choice(pool)
    facial = "None"
    if gender == "Male" and age >= 20:
        facial = random.choice(["None", "None", "Stubble", "Beard", "Moustache"])
    return {"hair": list(hair or random.choice(HAIR_COLOURS)), "style": style,
            "skin": list(skin or random.choice(SKIN_TONES)), "facial": facial}

def occupation(p):
    a = p.get("age", 30)
    if a < 5: return "Too young for school"
    if a < 18: return "Student"
    if a >= 66: return "Retired"
    return p.get("job_title", "office worker").capitalize()

def make_person(relation, category, gender=None, closeness=60, age=30, skin=None, hair=None):
    gender = gender or random.choice(["Male", "Female"])
    return {
        "name": random_name(gender),
        "gender": gender,
        "age": age,
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
        "attracted": random_attraction(gender),
        "look": random_look(gender, age, skin, hair),
        "job_title": random.choice(JOB_TITLES),
        "history": [],
    }

def remember(person, age, text):
    """Keeps a short list of shared memories shown on the person's profile."""
    h = person.setdefault("history", [])
    h.append([age, text])
    del h[:-6]

def ensure_profiles(everyone, player_age):
    """Fills in the profile details for anyone from an older save."""
    for p in everyone:
        if "gender" not in p:
            p["gender"] = "Female" if p["name"] in NAME_POOL_FEMALE else "Male"
        if "age" not in p:
            base = {"Mother": 28, "Father": 31}.get(p["relation"], 55 if "Grand" in p["relation"] else player_age + 2)
            p["age"] = base + (player_age if p["relation"] in ("Mother", "Father") or "Grand" in p["relation"] else 0)
        p.setdefault("attracted", random_attraction(p["gender"]))
        p.setdefault("look", random_look(p["gender"], p["age"]))
        p.setdefault("job_title", random.choice(JOB_TITLES))
        p.setdefault("history", [])

def generate_family(skin=None, hair=None):
    """A starting cast of relatives with ages and a family resemblance:
    parents, grandparents on both sides, and a random number of siblings."""
    def kin(rel, g, close, age):
        near = skin if (skin and random.random() < 0.7) else None
        p = make_person(rel, "family", g, closeness=close, age=age, skin=near)
        if rel in ("Mother", "Father", "Sibling") and hair and random.random() < 0.5:
            p["look"]["hair"] = list(hair)
        return p
    mum, dad = random.randint(24, 36), random.randint(25, 40)
    family = [kin("Mother", "Female", 68, mum), kin("Father", "Male", 68, dad)]
    for side in ("Paternal", "Maternal"):
        family.append(kin(f"{side} Grandfather", "Male", 55, (dad if side == "Paternal" else mum) + random.randint(24, 32)))
        family.append(kin(f"{side} Grandmother", "Female", 55, (dad if side == "Paternal" else mum) + random.randint(22, 30)))
    for _ in range(random.randint(0, 3)):
        sib_type = random.choices(["Sibling", "Half-Sibling", "Step-Sibling"], weights=[70, 20, 10])[0]
        family.append(kin(sib_type, random.choice(["Male", "Female"]), 60, random.randint(1, 9)))
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
    remember(person, state.get("age", 0), {"Talk": "Had a good chat.", "Hang Out": "Spent time together.",
                                           "Argue": "Had an argument.", "Gift": "You gave them a gift."}[action])
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
        person["age"] = person.get("age", 30) + 1
        if person.get("is_child") and person["age"] == 18:
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

    meet_rect = pygame.Rect(rect.x, rect.y, 162, 32)
    partner_rect = pygame.Rect(rect.x + 170, rect.y, 162, 32)
    baby_rect = pygame.Rect(rect.x + 340, rect.y, 162, 32)
    ask_rect = pygame.Rect(rect.x + 510, rect.y, 162, 32)

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
        same = partner.get("gender") == state.get("gender")
        small_btn(baby_rect, "Adopt a child" if same else "Try for a baby",
                  age < MARRY_MIN_AGE or no_budget or actions_used.get("__baby__", 0) >= 1)
    small_btn(ask_rect, "Ask Family for $", quick_ask_target(people, state) is None)

    list_rect = pygame.Rect(rect.x, rect.y + 42, rect.width, rect.height - 42)
    rows, combined, scroll_offset = get_people_layout(list_rect, people, friends, partner, scroll_offset)

    if not combined:
        draw_text(screen, "No relationships yet.", small_font, DARK_GREY,
                  list_rect.centerx, list_rect.centery, centre=True)

    for person, row_rect, buttons in rows:
        draw_rounded_rect(screen, WHITE, row_rect, radius=8)
        pygame.draw.rect(screen, BLACK, row_rect, 1, border_radius=8)

        tag_colour = CATEGORY_COLOURS.get(person["category"], LIGHT_GREY)
        thumb = pygame.Rect(row_rect.x + 4, row_rect.y + 3, 44, 44)
        draw_rounded_rect(screen, (245, 243, 248), thumb, radius=8)
        draw_person_avatar(screen, thumb, person)
        pygame.draw.rect(screen, tag_colour, thumb, 2, border_radius=8)

        draw_text(screen, person["name"], small_font, BLACK, row_rect.x + 54, row_rect.y + 6)
        rel = f"{person['relation']}, {person.get('age', '?')}"
        traits = ", ".join(person["traits"])
        options = ([f"{rel}, {person.get('compat', 50)}% match", rel]
                   if person["category"] == "partner" else [f"{rel}: {traits}", rel])
        sub = next((o for o in options if small_font.size(o)[0] < 158), _fit(rel, small_font, 158))
        draw_text(screen, sub, small_font, DARK_GREY, row_rect.x + 54, row_rect.y + 26)

        # top bar = bond, middle = trust (partner: bottom = romance); red dot = open conflict
        bx = row_rect.x + 228
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

    meet_rect = pygame.Rect(rect.x, rect.y, 162, 32)
    partner_rect = pygame.Rect(rect.x + 170, rect.y, 162, 32)
    baby_rect = pygame.Rect(rect.x + 340, rect.y, 162, 32)
    ask_rect = pygame.Rect(rect.x + 510, rect.y, 162, 32)

    # clicking a row (outside its buttons) opens that person's profile
    list_rect0 = pygame.Rect(rect.x, rect.y + 42, rect.width, rect.height - 42)
    rows0, _c, _s = get_people_layout(list_rect0, people, friends, partner, scroll_offset)
    for person, row_rect, buttons in rows0:
        if row_rect.collidepoint(mx, my) and not any(b.collidepoint(mx, my) for b in buttons.values()):
            return ("profile", person)

    if ask_rect.collidepoint(mx, my):
        target = quick_ask_target(people, state)
        return ("ask", target) if target is not None else None

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


def advance_deaths(people, friends, partner, state, log):
    """Year end: older relatives, friends and partners can pass away. You
    grieve (Mental drops more for people you were close to) and may inherit
    a little money. Returns the (possibly widowed) partner."""
    stats = state["stats"]
    def dies(p):
        a = p.get("age", 30)
        if a < 72: return False
        return a >= 100 or random.random() < (a - 71) * 0.025
    def grieve(p, left=0):
        hit = 5 if p["closeness"] >= 55 else 2
        stats["mental"] = max(0, stats["mental"] - hit)
        if left:
            state["money"] += left
            log(f"{p['name']} left you ${left}.")
    for p in list(people):
        if p.get("is_child") and p.get("age", 0) < 72:
            continue
        if dies(p):
            people.remove(p)
            log(f"Your {p['relation'].lower()}, {p['name']}, passed away at {p['age']}.")
            grieve(p, random.randint(15, 90) if p["category"] == "family" and not p.get("is_child") else 0)
    for p in list(friends):
        if dies(p):
            friends.remove(p)
            log(f"Your friend {p['name']} passed away.")
            grieve(p)
    if partner and dies(partner):
        log(f"{partner['name']} passed away at {partner['age']}.")
        grieve(partner, random.randint(40, 160) if partner.get("married") else 0)
        stats["mental"] = max(0, stats["mental"] - 4)
        return None
    return partner

def ask_for_money(person, state, age):
    """Ask a relative for money. Returns a short message. Kids usually get
    some; adults are asked to stand on their own feet more often."""
    state["actions_remaining"] -= 1
    state["actions_used"][(id(person), "Ask")] = 1
    person["contacted"] = True
    chance = (person["closeness"] + person["trust"]) / 200 + (0.25 if age < 18 else 0.0) - (0.2 if age >= 25 else 0.0)
    if "kind" in person["traits"]: chance += 0.1
    if age >= 25 and "ambitious" in person["traits"]: chance -= 0.1
    chance = max(0.1, min(0.95, chance))
    if random.random() < chance:
        lo, hi = (5, 12) if age < 13 else (10, 25) if age < 18 else (10, 30)
        amount = random.randint(lo, hi)
        state["money"] += amount
        if age >= 18:
            person["closeness"] = max(0, person["closeness"] - 3)
            person["trust"] = max(0, person["trust"] - 1)
        remember(person, age, f"Gave you ${amount}.")
        return f"{person['name']} gave you ${amount}."
    person["closeness"] = max(0, person["closeness"] - 2)
    remember(person, age, "Said no when you asked for money.")
    return f"{person['name']} said no."

def can_ask_money(person, state):
    return (person["category"] == "family" and not person.get("is_child") and person.get("age", 40) < 90
            and state["actions_remaining"] > 0 and not state["actions_used"].get((id(person), "Ask")))

def quick_ask_target(people, state):
    order = sorted([p for p in people if can_ask_money(p, state)],
                   key=lambda p: (p["relation"] not in ("Mother", "Father"), -p["closeness"]))
    return order[0] if order else None

def relationship_label(p):
    c = p["closeness"]
    if p["category"] == "partner":
        return "Spouse" if p.get("married") else "Partner"
    if p.get("is_child"):
        return "Your child"
    if c >= 80: return "Very close" if p["category"] == "family" else "Best friend"
    if c >= 55: return "Close"
    if c >= 30: return "Friendly" if p["category"] == "friend" else "Distant"
    return "Drifting apart"

def orientation_text(p, player_gender):
    a = p.get("age", 30)
    if a < 13:
        return "Too young to say"
    if p["category"] == "partner" or p["closeness"] >= 60:
        return {"Both": "Men and women"}.get(p["attracted"], p["attracted"])
    return "Unknown (get to know them)"

def _fit(text, fnt, width):
    if fnt.size(text)[0] <= width:
        return text
    while len(text) > 1 and fnt.size(text + "…")[0] > width:
        text = text[:-1]
    return text + "…"

def person_mood(p):
    return 25 if p["conflict"] >= 40 else (75 if p["closeness"] >= 55 else 50)

def draw_person_avatar(screen, rect, p):
    lk = p["look"]
    draw_avatar(screen, rect, p["gender"], tuple(lk["hair"]), lk["style"], tuple(lk["skin"]),
                lk["facial"], p.get("age", 30), person_mood(p))

PROFILE_BUTTONS = ("Talk", "Hang Out", "Argue", "Gift", "Ask for $", "Back")

def profile_layout(rect):
    btns = {}
    w, gap = 100, 8
    y = rect.bottom - 40
    for i, name in enumerate(PROFILE_BUTTONS):
        btns[name] = pygame.Rect(rect.x + 8 + i * (w + gap), y, w, 32)
    return btns

def draw_profile(screen, rect, p, mouse_pos, state, age):
    draw_rounded_rect(screen, (250, 248, 252), rect, radius=12)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=12)
    portrait = pygame.Rect(rect.x + 14, rect.y + 12, 150, 190)
    draw_rounded_rect(screen, WHITE, portrait, radius=12)
    pygame.draw.rect(screen, BLACK, portrait, 2, border_radius=12)
    draw_person_avatar(screen, portrait, p)
    tag = CATEGORY_COLOURS.get(p["category"], LIGHT_GREY)
    label = relationship_label(p)
    tag_rect = pygame.Rect(portrait.x, portrait.bottom + 8, portrait.w, 24)
    draw_rounded_rect(screen, tag, tag_rect, radius=10)
    draw_text(screen, label, small_font, WHITE, tag_rect.centerx, tag_rect.centery, centre=True)

    x = rect.x + 184
    draw_text(screen, p["name"], font, BLACK, x, rect.y + 10)
    sub = f"{p['relation']}, age {p.get('age', '?')}, {p['gender'].lower()}"
    draw_text(screen, sub, small_font, DARK_GREY, x, rect.y + 36)
    draw_text(screen, "Occupation: " + occupation(p), small_font, DARK_GREY, x, rect.y + 56)
    draw_text(screen, "Personality: " + ", ".join(p["traits"]), small_font, DARK_GREY, x, rect.y + 76)
    draw_text(screen, "Attracted to: " + orientation_text(p, state.get("gender")), small_font, DARK_GREY, x, rect.y + 96)
    bars = [("Bond", p["closeness"], tag), ("Trust", p["trust"], (120, 120, 130))]
    if p["category"] == "partner":
        bars.append(("Romance", p["romance"], CATEGORY_COLOURS["partner"]))
        bars.append(("Match", p.get("compat", 50), (230, 180, 60)))
    bars.append(("Conflict", p["conflict"], (215, 80, 80)))
    for n, (name, val, colr) in enumerate(bars):
        by = rect.y + 122 + n * 18
        draw_text(screen, name, small_font, BLACK, x, by - 3)
        bar = pygame.Rect(x + 70, by, 130, 10)
        draw_rounded_rect(screen, LIGHT_GREY, bar, radius=5)
        if val > 0:
            draw_rounded_rect(screen, colr, (bar.x, bar.y, int(bar.w * val / 100), bar.h), radius=5)

    mx = rect.x + 440
    draw_text(screen, "Shared memories", small_font, BLACK, mx, rect.y + 10)
    hist = p.get("history", [])
    if not hist:
        draw_text(screen, "Nothing yet. Spend time together!", small_font, DARK_GREY, mx, rect.y + 34)
    for n, (a, t) in enumerate(reversed(hist[-6:])):
        draw_text(screen, _fit(f"Age {a}: {t}", small_font, rect.right - mx - 12), small_font, DARK_GREY, mx, rect.y + 34 + n * 22)

    btns = profile_layout(rect)
    for name, b in btns.items():
        if name == "Back":
            off = False
        elif name == "Ask for $":
            if p["category"] != "family" or p.get("is_child"):
                continue
            off = not can_ask_money(p, state)
        else:
            uses = state["actions_used"].get((id(p), name), 0)
            off = state["actions_remaining"] <= 0 or uses >= MAX_USES_PER_PERSON_ACTION or (name == "Gift" and state["money"] < GIFT_COST)
        fill = LIGHT_GREY if off else (ACCENT if b.collidepoint(mouse_pos) else WHITE)
        draw_rounded_rect(screen, fill, b, radius=8)
        pygame.draw.rect(screen, BLACK, b, 2, border_radius=8)
        lab = name
        if name in ("Talk", "Hang Out", "Argue", "Gift"):
            u = state["actions_used"].get((id(p), name), 0)
            lab = name if u == 0 else f"{name} ({u}/{MAX_USES_PER_PERSON_ACTION})"
        draw_text(screen, lab, small_font, BLACK, b.centerx, b.centery, centre=True)
    return btns

def handle_profile_click(mx, my, rect, p, state, age):
    """Returns "back" or a message string (e.g. from asking for money), else None."""
    for name, b in profile_layout(rect).items():
        if not b.collidepoint(mx, my):
            continue
        if name == "Back":
            return "back"
        if name == "Ask for $":
            if can_ask_money(p, state):
                return ask_for_money(p, state, age)
            return None
        uses = state["actions_used"].get((id(p), name), 0)
        if uses < MAX_USES_PER_PERSON_ACTION and apply_interaction(p, name, state):
            state["actions_used"][(id(p), name)] = uses + 1
        return None
    return None
