import random
import pygame
from constants import OUTLINE, INK, MUTED, draw_card, draw_pill, draw_shadow
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
    "enemy": (215, 80, 80),
}
STAT_KEYS = ["looks", "social", "academic", "athletic", "mental"]
STAT_NAMES = {"looks": "Looks", "social": "Social", "academic": "Academic", "athletic": "Athletic", "mental": "Mental"}
STAT_BAR_COLOURS = {"looks": (236, 130, 178), "social": (160, 100, 220), "academic": (70, 170, 150),
                    "athletic": (80, 190, 210), "mental": (90, 140, 230)}

def random_stats(base=None, spread=16):
    """Random stats around a base (other stats, or 50)."""
    out = {}
    for k in STAT_KEYS:
        centre = base[k] if base and k in base else random.randint(30, 70)
        out[k] = max(5, min(98, int(random.gauss(centre, spread))))
    return out

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

def make_child(parent_traits, parent_stats=None):
    gender = random.choice(["Male", "Female"])
    child = make_person("Son" if gender == "Male" else "Daughter", "family", gender, closeness=70)
    child["age"] = 0
    child["attracted"] = random_attraction(gender)
    child["is_child"] = True
    child["trust"] = 65
    inherited = random.choice(parent_traits) if parent_traits else random.choice(TRAITS)
    child["traits"] = list({inherited, random.choice(TRAITS)})
    # stats are inherited: the average of both parents, with some luck
    if parent_stats:
        avg = {k: sum(ps.get(k, 50) for ps in parent_stats) / len(parent_stats) for k in STAT_KEYS}
        child["stats"] = {k: max(5, min(98, int(random.gauss(avg[k], 10)))) for k in STAT_KEYS}
    return child

TRAITS = ["kind", "hot-tempered", "outgoing", "introverted", "loyal", "shy", "funny", "ambitious", "jealous"]
TRUST_FX = {"Talk": 2, "Hang Out": 3, "Argue": -6, "Gift": 1, "Compliment": 1}
ROMANCE_FX = {"Talk": 3, "Hang Out": 6, "Argue": -8, "Gift": 6, "Compliment": 5}

INTERACTIONS = {
    "Talk":     {"closeness": 4,  "mental": 1},
    "Hang Out": {"closeness": 7,  "social": 2, "physical": 1},
    "Argue":    {"closeness": -9, "mental": -2},
    "Gift":     {"closeness": 11, "social": 1},  # money cost handled separately
    "Compliment": {"closeness": 3, "mental": 1},
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
        "stats": random_stats(),
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
        p.setdefault("stats", random_stats())

def generate_family(skin=None, hair=None, player_stats=None):
    """A starting cast of relatives with ages and a family resemblance:
    parents, grandparents on both sides, and a random number of siblings."""
    def kin(rel, g, close, age):
        near = skin if (skin and random.random() < 0.7) else None
        p = make_person(rel, "family", g, closeness=close, age=age, skin=near)
        if rel in ("Mother", "Father", "Sibling") and hair and random.random() < 0.5:
            p["look"]["hair"] = list(hair)
        if "Sibling" in rel and player_stats:
            p["stats"] = random_stats(player_stats, 13)   # siblings share genes with you
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
    # no hard cap: repeating the same thing with the same person in a year
    # just gives smaller and smaller effects
    uses = state["actions_used"].get((id(person), action), 0)
    dim = max(0.3, 1 / (1 + 0.4 * uses))
    if action == "Gift":
        if state["money"] < GIFT_COST:
            return False
        state["money"] -= GIFT_COST

    stats = state["stats"]
    t = person["traits"]
    m = trait_modifier(person, action)
    person["closeness"] = max(0, min(100, person["closeness"] + round(effects["closeness"] * m * dim)))

    trust = round(TRUST_FX[action] * dim) if TRUST_FX[action] > 0 else TRUST_FX[action]
    if trust < 0 and "loyal" in t:
        trust //= 2
    person["trust"] = max(0, min(100, person["trust"] + trust))

    if action == "Argue":
        person["conflict"] = min(100, person["conflict"] + round(15 * (1.5 if "hot-tempered" in t else 1)))
    else:
        relief = 3 + (7 if person["conflict"] >= 40 and action != "Argue" else 0)
        person["conflict"] = max(0, person["conflict"] - round(relief * dim if relief > 3 else relief))

    if person["category"] == "partner":
        gain = round(ROMANCE_FX[action] * (dim if ROMANCE_FX[action] > 0 else 1))
        if gain > 0:   # a good personality match makes romance grow faster
            gain = round(gain * (0.7 + 0.6 * person.get("compat", 50) / 100))
        person["romance"] = max(0, min(100, person["romance"] + gain))

    for stat, value in effects.items():
        if stat == "closeness":
            continue
        stats[stat] = max(0, min(100, stats[stat] + (round(value * dim) if value > 0 else value)))
    if action == "Talk" and "funny" in t:
        stats["mental"] = min(100, stats["mental"] + 1)
    if action == "Talk" and "ambitious" in t:
        stats["academic"] = min(100, stats["academic"] + 1)
    if action == "Hang Out" and "introverted" in state.get("player_traits", []):
        stats["mental"] = max(0, stats["mental"] - 1)

    person["contacted"] = True
    state["actions_remaining"] -= 1
    state["actions_used"][(id(person), action)] = uses + 1
    remember(person, state.get("age", 0), {"Talk": "Had a good chat.", "Hang Out": "Spent time together.",
                                           "Argue": "Had an argument.", "Gift": "You gave them a gift.", "Compliment": "You paid them a compliment."}[action])
    return True

def advance_relationships(people, friends, partner, log):
    """Year end: relationships you ignore fade, friends can drift away,
    partners can break up (or divorce), and children grow up.
    Returns the (possibly ended) partner."""
    for person in people + friends + ([partner] if partner else []):
        neglected = not person.get("contacted")
        if neglected:
            loss = {"family": 2, "friend": 5, "partner": 6, "enemy": 0}.get(person["category"], 3)
            if person.get("is_child") and person.get("age", 18) < 13:
                loss = 3
            if "loyal" in person["traits"]:
                loss = max(1, loss - 2)
            person["closeness"] = max(0, person["closeness"] - loss)
            person["trust"] = max(0, person["trust"] - 2)
            if person["category"] == "partner":
                person["romance"] = max(0, person["romance"] - 6)
        person["conflict"] = max(0, person["conflict"] - (2 if person["category"] == "enemy" else 5))
        person["contacted"] = False
        person["age"] = person.get("age", 30) + 1
        if person.get("is_child") and person["age"] == 18:
            log(f"{person['name']} turned 18.")

    for f in list(friends):
        if f["category"] == "enemy":
            if f["conflict"] < 20:
                f["category"], f["relation"], f["closeness"] = "friend", "Acquaintance", max(f["closeness"], 25)
                log(f"You and {f['name']} are no longer enemies.")
            continue
        if f["conflict"] >= 70 and f["closeness"] < 35:
            f["category"], f["relation"] = "enemy", "Enemy"
            log(f"{f['name']} has become your enemy.")
        elif f["closeness"] <= 8:
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
            partner["married"] = False
            if partner["conflict"] >= 50:
                partner["category"], partner["relation"] = "enemy", "Ex (bad terms)"
            else:
                partner["category"], partner["relation"] = "friend", "Ex"
                partner["closeness"] = max(15, partner["closeness"] // 2)
            partner["romance"] = 0
            friends.append(partner)
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

    meet_done = False
    meet_hovered = meet_rect.collidepoint(mouse_pos)
    fill = LIGHT_GREY if (meet_done or state["actions_remaining"] <= 0) else (ACCENT if meet_hovered else WHITE)
    draw_rounded_rect(screen, fill, meet_rect, radius=8)
    pygame.draw.rect(screen, OUTLINE, meet_rect, 2, border_radius=8)
    draw_text(screen, meet_label, small_font, INK, meet_rect.centerx, meet_rect.centery, centre=True)

    def small_btn(r, label, disabled):
        hovered = r.collidepoint(mouse_pos)
        fill = LIGHT_GREY if disabled else (ACCENT if hovered else WHITE)
        draw_rounded_rect(screen, fill, r, radius=8)
        pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
        draw_text(screen, label, small_font, INK, r.centerx, r.centery, centre=True)

    no_budget = state["actions_remaining"] <= 0
    if partner is None:
        old_enough = age >= PARTNER_MIN_AGE
        label = "Look for a Partner" if old_enough else f"Partner (from age {PARTNER_MIN_AGE})"
        small_btn(partner_rect, label, not old_enough or no_budget)
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
        pygame.draw.rect(screen, OUTLINE, row_rect, 1, border_radius=8)

        tag_colour = CATEGORY_COLOURS.get(person["category"], LIGHT_GREY)
        thumb = pygame.Rect(row_rect.x + 4, row_rect.y + 3, 44, 44)
        draw_rounded_rect(screen, (245, 243, 248), thumb, radius=8)
        draw_person_avatar(screen, thumb, person)
        pygame.draw.rect(screen, tag_colour, thumb, 2, border_radius=8)

        draw_text(screen, person["name"], small_font, INK, row_rect.x + 54, row_rect.y + 6)
        st_label, st_col = stage_of(person)
        draw_text(screen, st_label, small_font, st_col, row_rect.x + 54 + small_font.size(person["name"])[0] + 8, row_rect.y + 6)
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
            maxed = False
            no_budget = state["actions_remaining"] <= 0
            hovered = brect.collidepoint(mouse_pos)
            fill = LIGHT_GREY if (maxed or no_budget) else (ACCENT if hovered else WHITE)
            draw_rounded_rect(screen, fill, brect, radius=6)
            pygame.draw.rect(screen, OUTLINE, brect, 1, border_radius=6)
            label = action if uses == 0 else f"{action} ({uses})"
            draw_text(screen, label, small_font, INK, brect.centerx, brect.centery, centre=True)

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

    if meet_rect.collidepoint(mx, my) :
        actions_used["__meet__"] = actions_used.get("__meet__", 0) + 1
        state["actions_remaining"] -= 1
        return "meet"

    if (partner is None and age >= PARTNER_MIN_AGE and partner_rect.collidepoint(mx, my)
            ):
        actions_used["__partner__"] = actions_used.get("__partner__", 0) + 1
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
            apply_interaction(person, action, state)
            return None

    return None


def advance_deaths(people, friends, partner, state, log):
    """Year end: older relatives, friends and partners can pass away. You
    grieve (Mental drops more for people you were close to) and may inherit
    money, a home or a keepsake. Returns the (possibly widowed) partner."""
    stats = state["stats"]
    mult = {"Struggling": 0.6, "Comfortable": 1.0, "Wealthy": 2.0}[state.get("family_wealth", "Comfortable")]
    def dies(p):
        a = p.get("age", 30)
        if a < 72: return False
        return a >= 100 or random.random() < (a - 71) * 0.025
    def inherit(p, lo, hi, house_chance):
        gift = int(random.randint(lo, hi) * mult)
        state["money"] += gift
        log(f"{p['name']} left you ${gift}.")
        if random.random() < house_chance:
            value = int(random.randint(150, 380) * (0.8 + mult / 4))
            if state.get("home"):
                cash = int(value * 0.6)
                state["money"] += cash
                log(f"You inherited {p['name']}'s house and sold it for ${cash}.")
            else:
                state["home"] = {"name": f"{p['name']}'s house", "value": value}
                log(f"You inherited {p['name']}'s house (worth about ${value}). You no longer pay rent.")
        if random.random() < 0.3 and "heirloom" not in state["owned"]:
            state["owned"].add("heirloom")
            log(f"You inherited a keepsake from {p['name']}.")
    def grieve(p):
        stats["mental"] = max(0, stats["mental"] - (5 if p["closeness"] >= 55 else 2))
    for p in list(people):
        if p.get("is_child") and p.get("age", 0) < 72:
            continue
        if dies(p):
            people.remove(p)
            log(f"Your {p['relation'].lower()}, {p['name']}, passed away at {p['age']}.")
            grieve(p)
            if p["category"] == "family" and not p.get("is_child"):
                if p["relation"] in ("Mother", "Father"):
                    inherit(p, 60, 220, 0.4)
                elif "Grand" in p["relation"]:
                    inherit(p, 20, 110, 0.2)
                else:
                    inherit(p, 10, 60, 0.05)
    for p in list(friends):
        if dies(p):
            friends.remove(p)
            log(f"Your friend {p['name']} passed away.")
            grieve(p)
    if partner and dies(partner):
        log(f"{partner['name']} passed away at {partner['age']}.")
        grieve(partner)
        stats["mental"] = max(0, stats["mental"] - 4)
        if partner.get("married"):
            inherit(partner, 80, 260, 0.35)
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
        mult = {"Struggling": 0.6, "Comfortable": 1.0, "Wealthy": 2.0}[state.get("family_wealth", "Comfortable")]
        amount = max(1, int(random.randint(lo, hi) * mult))
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

def stage_of(p):
    """(label, colour) describing where the relationship is right now."""
    c, cf = p["closeness"], p["conflict"]
    cat = p["category"]
    if cat == "enemy":
        if cf >= 80: return "Nemesis", (170, 40, 40)
        if cf >= 60: return "Enemy", (200, 60, 60)
        if cf >= 40: return "Rival", (215, 110, 70)
        return "Tense", (225, 150, 80)
    if cat == "partner":
        if p.get("married"): return "Spouse", (220, 90, 140)
        r = p.get("romance", 0)
        if r >= 75: return "In love", (225, 70, 120)
        if r >= 50: return "Dating", (220, 90, 140)
        if r >= 25: return "Seeing each other", (225, 130, 160)
        return "Cooling off", (170, 130, 150)
    if p.get("is_child"):
        return "Your child", (90, 140, 230)
    if cf >= 40:
        return "Falling out", (215, 110, 70)
    if cat == "family":
        if c >= 80: return "Very close", (60, 110, 215)
        if c >= 55: return "Close", (90, 140, 230)
        if c >= 30: return "Distant", (130, 150, 190)
        return "Estranged", (140, 140, 160)
    if c >= 80: return "Best friend", (50, 160, 100)
    if c >= 55: return "Close friend", (76, 175, 120)
    if c >= 30: return "Friend", (110, 190, 140)
    return "Acquaintance", (150, 170, 155)

def relationship_label(p):
    return stage_of(p)[0]

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

def near_age(age):
    if age < 18:
        return max(5, age + random.randint(-1, 1))
    return max(18, age + random.randint(-8, 8))

def date_chance(player_stats, cand, fame=0):
    """How likely this person is to say yes if you ask them out."""
    c = cand["stats"]
    p = (0.2 + 0.5 * (player_stats["looks"] + player_stats["social"]) / 200
         + (cand.get("compat", 50) - 50) / 200 + fame / 300
         - (c["looks"] + c["social"] - 100) / 600)
    return max(0.05, min(0.95, p))

def make_prospect(state, age, traits, relation="Partner", category="partner"):
    """A possible partner who is attracted to the player's gender, and
    (mostly) someone the player is attracted to. Includes stats and a
    personality match score so the player can decide."""
    want = state.get("attracted", "Both")
    gender = state.get("gender", "Male")
    for _ in range(30):
        cg = "Male" if want == "Men" else "Female" if want == "Women" else random.choice(["Male", "Female"])
        if random.random() < 0.12:
            cg = random.choice(["Male", "Female"])
        cand = make_person(relation, category, cg, closeness=45, age=max(16 if age >= 16 else 5, near_age(age)))
        if is_attracted(cand["attracted"], gender):
            break
    cand["compat"] = compatibility(state.get("player_traits", []), cand["traits"])
    return cand

def popularity_reasons(state, fame):
    stats = state["stats"]
    parts = {"looks": max(0, stats["looks"] - 50) / 100 * 0.7, "social": max(0, stats["social"] - 50) / 100 * 0.7,
             "fame": fame / 100 * 0.6}
    return parts

def generate_invites(state, age, friends, partner, fame, ctx_people):
    """Other characters sometimes reach out to you. Looks, social skill and
    fame each raise the odds independently. Returns a list of invites."""
    out = []
    stats = state["stats"]
    parts = popularity_reasons(state, fame)
    if partner is None and age >= 13:
        p = 1 - (1 - 0.06) * (1 - parts["looks"]) * (1 - parts["social"]) * (1 - parts["fame"])
        if random.random() < p:
            cand = make_prospect(state, age, state.get("player_traits", []), "Admirer", "partner")
            top = max(parts, key=parts.get)
            why = {"looks": "They like how you look.", "social": "You're popular and easy to talk to.",
                   "fame": "They're a fan of yours."}[top] if parts[top] > 0.05 else "You caught their eye."
            if age < 16:
                kind, text = "dance", f"{cand['name']} asks you to the school dance."
            elif age < 25:
                kind, text = "date", f"{cand['name']} asks you out."
            else:
                kind, text = "date", f"{cand['name']} asks you to dinner."
            out.append({"kind": kind, "person": cand, "text": text, "why": why})
    if age >= 5 and len(friends) < 8 and random.random() < 0.15 + stats["social"] / 250:
        fr = make_person("Friend", "friend", closeness=40, age=near_age(age))
        out.append({"kind": "friend", "person": fr, "text": f"{fr['name']} wants to be your friend.",
                    "why": "They think you seem fun." if stats["social"] >= 50 else "They'd like to get to know you."})
    close = [f for f in friends if f["category"] == "friend" and f["closeness"] >= 45]
    close += [p for p in ctx_people if p["category"] == "family" and not p.get("is_child") and p["closeness"] >= 55 and p.get("age", 40) < 80]
    if close and random.random() < 0.4:
        who = random.choice(close)
        plan = random.choice(["go to the cinema", "come to a party", "go for a long walk", "have a games night", "get food together"]
                             if age >= 12 else ["come and play", "have a sleepover", "go to the park"])
        out.append({"kind": "hangout", "person": who, "text": f"{who['name']} invites you to {plan}.",
                    "why": "A chance to strengthen your bond."})
    random.shuffle(out)
    return out[:3]

def accept_invite(inv, state, age, friends, partner, log):
    """Applies accepting an invite. Returns the (possibly new) partner."""
    p, kind = inv["person"], inv["kind"]
    stats = state["stats"]
    if kind == "hangout":
        p["closeness"] = min(100, p["closeness"] + 8)
        p["trust"] = min(100, p["trust"] + 3)
        p["contacted"] = True
        stats["social"] = min(100, stats["social"] + 2)
        stats["mental"] = min(100, stats["mental"] + 1)
        remember(p, age, "You accepted their invitation.")
        log(f"Accepted {p['name']}'s invitation. It was great.")
        return partner
    if kind == "friend":
        p["category"], p["relation"] = "friend", "Friend"
        friends.append(p)
        remember(p, age, "Became friends.")
        log(f"Became friends with {p['name']}.")
        return partner
    if kind == "dance":
        stats["social"] = min(100, stats["social"] + 3)
        stats["mental"] = min(100, stats["mental"] + 2)
        sparks = age >= 16 and partner is None and p["compat"] >= 50 and random.random() < 0.5
        if sparks:
            p["category"], p["relation"], p["romance"] = "partner", "Partner", 45
            remember(p, age, "Went to the dance together.")
            log(f"Went to the dance with {p['name']}, and started dating.")
            return p
        p["category"], p["relation"], p["closeness"] = "friend", "Friend", 55
        friends.append(p)
        remember(p, age, "Went to the school dance together.")
        log(f"Went to the dance with {p['name']}. You became friends.")
        return partner
    # a date
    if partner is None and age >= 16:
        p["category"], p["relation"], p["romance"], p["closeness"] = "partner", "Partner", 45, 50
        remember(p, age, "Started dating.")
        log(f"Started dating {p['name']} ({p['compat']}% match).")
        return p
    return partner

def decline_invite(inv, state, age, friends, log):
    p, kind = inv["person"], inv["kind"]
    if kind == "hangout":
        p["closeness"] = max(0, p["closeness"] - 3)
        log(f"Turned down {p['name']}'s invitation.")
    elif kind in ("date", "dance"):
        if ("jealous" in p["traits"] or "hot-tempered" in p["traits"]) and random.random() < 0.25:
            p["category"], p["relation"], p["conflict"], p["closeness"] = "enemy", "Rival", 45, 10
            friends.append(p)
            log(f"{p['name']} took the rejection badly and now resents you.")
        else:
            log(f"Politely turned down {p['name']}.")
    else:
        log(f"Declined {p['name']}'s friendship offer.")

PROFILE_BUTTONS = ("Talk", "Hang Out", "Compliment", "Argue", "Gift", "Ask for $", "Ask out", "Back")

def profile_layout(rect, names=PROFILE_BUTTONS):
    btns = {}
    gap = 4
    w = min(90, (rect.width - 16 - gap * (len(names) - 1)) // max(1, len(names)))
    y = rect.bottom - 40
    for i, name in enumerate(names):
        btns[name] = pygame.Rect(rect.x + 8 + i * (w + gap), y, w, 32)
    return btns

def can_ask_out(p, state, age):
    return (p["category"] == "friend" and state.get("_has_partner") is False and age >= 16 and p.get("age", 30) >= 16
            and is_attracted(p["attracted"], state.get("gender", "Male"))
            and is_attracted(state.get("attracted", "Both"), p["gender"]) and state["actions_remaining"] > 0)

def draw_stat_bars(screen, x, y, p, width=130):
    for n, k in enumerate(STAT_KEYS):
        by = y + n * 20
        draw_text(screen, STAT_NAMES[k], small_font, DARK_GREY, x, by - 3)
        bar = pygame.Rect(x + 80, by, width - 10, 10)
        draw_rounded_rect(screen, LIGHT_GREY, bar, radius=5)
        v = p.get("stats", {}).get(k, 0)
        if v > 0:
            draw_rounded_rect(screen, STAT_BAR_COLOURS[k], (bar.x, bar.y, int(bar.w * v / 100), bar.h), radius=5)
        draw_text(screen, str(v), small_font, DARK_GREY, bar.right + 6, by - 3)

def draw_profile(screen, rect, p, mouse_pos, state, age, mode="profile", header="", note="", labels=None):
    """mode: "profile" (full), "prospect" or "invite" (a decision card with
    two buttons given in `labels`)."""
    draw_rounded_rect(screen, (250, 248, 252), rect, radius=14)
    pygame.draw.rect(screen, (150, 144, 176), rect, 2, border_radius=14)
    portrait = pygame.Rect(rect.x + 14, rect.y + 12, 150, 190)
    draw_rounded_rect(screen, WHITE, portrait, radius=12)
    pygame.draw.rect(screen, (150, 144, 176), portrait, 2, border_radius=12)
    draw_person_avatar(screen, portrait, p)
    label, tag = stage_of(p) if mode == "profile" else (header or "New", (255, 149, 66))
    tag_rect = pygame.Rect(portrait.x, portrait.bottom + 8, portrait.w, 24)
    draw_rounded_rect(screen, tag, tag_rect, radius=12)
    draw_text(screen, label, small_font, WHITE, tag_rect.centerx, tag_rect.centery, centre=True)

    x = rect.x + 182
    draw_text(screen, p["name"], font, INK, x, rect.y + 10)
    draw_text(screen, f"{p['relation'] if mode == 'profile' else 'Age ' + str(p.get('age', '?'))}"
                      f"{', age ' + str(p.get('age', '?')) if mode == 'profile' else ''}, {p['gender'].lower()}",
              small_font, DARK_GREY, x, rect.y + 34)
    draw_text(screen, "Occupation: " + occupation(p), small_font, DARK_GREY, x, rect.y + 54)
    draw_text(screen, "Personality: " + ", ".join(p["traits"]), small_font, DARK_GREY, x, rect.y + 74)
    draw_text(screen, "Attracted to: " + (orientation_text(p, state.get("gender")) if mode == "profile"
              else {"Both": "Men and women"}.get(p["attracted"], p["attracted"])), small_font, DARK_GREY, x, rect.y + 94)
    if mode == "profile":
        bars = [("Bond", p["closeness"], CATEGORY_COLOURS.get(p["category"], LIGHT_GREY)), ("Trust", p["trust"], (120, 120, 130))]
        if p["category"] == "partner":
            bars.append(("Romance", p["romance"], CATEGORY_COLOURS["partner"]))
            bars.append(("Match", p.get("compat", 50), (230, 180, 60)))
        bars.append(("Conflict", p["conflict"], (215, 80, 80)))
    else:
        mt = p.get("compat", 50)
        bars = [("Match", mt, (230, 180, 60))]
        draw_text(screen, f"Personality match: {mt}%" + (" (great)" if mt >= 65 else " (clashing)" if mt < 40 else ""),
                  small_font, BLACK, x, rect.y + 116)
        bars = []
        if note:
            draw_text(screen, _fit(note, small_font, 250), small_font, DARK_GREY, x, rect.y + 138)
        if mode == "prospect":
            ch = int(100 * date_chance(state["stats"], p, state.get("_fame", 0)))
            draw_text(screen, f"Chance they say yes: about {ch}%", small_font, DARK_GREY, x, rect.y + 158)
    for n, (name, val, colr) in enumerate(bars):
        by = rect.y + 122 + n * 18
        draw_text(screen, name, small_font, INK, x, by - 3)
        bar = pygame.Rect(x + 70, by, 130, 10)
        draw_rounded_rect(screen, LIGHT_GREY, bar, radius=5)
        if val > 0:
            draw_rounded_rect(screen, colr, (bar.x, bar.y, int(bar.w * val / 100), bar.h), radius=5)

    mx = rect.x + 440
    draw_text(screen, "Stats", small_font, INK, mx, rect.y + 10)
    draw_stat_bars(screen, mx, rect.y + 32, p, 110)
    if mode == "profile":
        draw_text(screen, "Shared memories", small_font, INK, mx, rect.y + 142)
        hist = p.get("history", [])
        if not hist:
            draw_text(screen, "Nothing yet. Spend time together!", small_font, DARK_GREY, mx, rect.y + 162)
        for n, (a, t) in enumerate(reversed(hist[-4:])):
            draw_text(screen, _fit(f"Age {a}: {t}", small_font, rect.right - mx - 12), small_font, DARK_GREY, mx, rect.y + 162 + n * 20)

    if mode == "profile":
        names = [n for n in PROFILE_BUTTONS if not (n == "Ask for $" and (p["category"] != "family" or p.get("is_child")))
                 and not (n == "Ask out" and not can_ask_out(p, state, age))]
        btns = profile_layout(rect, names)
    else:
        btns = {}
        for i, lab in enumerate(labels or ("Accept", "Decline")):
            btns[lab] = pygame.Rect(rect.x + 190 + i * 220, rect.bottom - 48, 205, 38)
    for name, b in btns.items():
        if mode != "profile":
            off = False
        elif name == "Back":
            off = False
        elif name == "Ask for $":
            off = not can_ask_money(p, state)
        elif name == "Ask out":
            off = False
        else:
            off = state["actions_remaining"] <= 0 or (name == "Gift" and state["money"] < GIFT_COST)
        primary = mode != "profile" and name == (labels or ("Accept",))[0]
        fill = LIGHT_GREY if off else (ACCENT if (b.collidepoint(mouse_pos) or primary) else WHITE)
        draw_rounded_rect(screen, fill, b, radius=10)
        pygame.draw.rect(screen, (150, 144, 176), b, 2, border_radius=10)
        lab = name
        if name in ("Talk", "Hang Out", "Compliment", "Argue", "Gift"):
            u = state["actions_used"].get((id(p), name), 0)
            lab = name if u == 0 else f"{name} ({u})"
        draw_text(screen, lab, small_font, INK, b.centerx, b.centery, centre=True)
    return btns

def handle_profile_click(mx, my, rect, p, state, age):
    """Returns "back", ("askout", person), a message string, or None."""
    names = [n for n in PROFILE_BUTTONS if not (n == "Ask for $" and (p["category"] != "family" or p.get("is_child")))
             and not (n == "Ask out" and not can_ask_out(p, state, age))]
    for name, b in profile_layout(rect, names).items():
        if not b.collidepoint(mx, my):
            continue
        if name == "Back":
            return "back"
        if name == "Ask for $":
            if can_ask_money(p, state):
                return ask_for_money(p, state, age)
            return None
        if name == "Ask out":
            return ("askout", p)
        apply_interaction(p, name, state)
        return None
    return None

def handle_decision_click(mx, my, rect, labels):
    """For prospect/invite cards: returns the label of the clicked button."""
    for i, lab in enumerate(labels):
        if pygame.Rect(rect.x + 190 + i * 220, rect.bottom - 48, 205, 38).collidepoint(mx, my):
            return lab
    return None
