"""Growing your family: babies from flings, adoption, IVF and surrogacy.

You can have children in any relationship (or none), at any age. Age changes
the odds of having a baby naturally and with IVF, but not whether adoption
is possible."""
import random
import pygame
from constants import fmt, INK, MUTED, ACCENT, GREEN, RED, DARK_GREY, WHITE
from constants import small_font, font, draw_text, draw_rounded_rect
import people as P

MAX_KIDS = 6

# ---------------------------------------------------------------- the odds
def fert_f(age):
    """Natural fertility of someone who can carry a baby."""
    if age < 17: return 0.0
    if age <= 30: return 1.0
    if age <= 34: return 0.85
    if age <= 37: return 0.65
    if age <= 40: return 0.4
    if age <= 43: return 0.18
    if age <= 46: return 0.06
    if age <= 49: return 0.02
    return 0.0

def fert_m(age):
    if age < 17: return 0.0
    if age <= 45: return 1.0
    if age <= 60: return 0.7
    if age <= 70: return 0.4
    if age <= 80: return 0.15
    return 0.05

def ivf_chance(carrier_age):
    if carrier_age <= 34: return 0.55
    if carrier_age <= 39: return 0.42
    if carrier_age <= 42: return 0.3
    if carrier_age <= 45: return 0.18
    return 0.3          # donor eggs from here on

def structure(state, partner, age):
    """Who could carry a baby, and whether a natural pregnancy is possible."""
    g = state.get("gender", "Female")
    pg = partner.get("gender") if partner else None
    page = partner.get("age", 30) if partner else None
    carriers = []
    if g == "Female":
        carriers.append(("you", age))
    if pg == "Female":
        carriers.append(("partner", page))
    natural = bool(partner) and pg is not None and pg != g and partner.get("status") != "situationship"
    return carriers, natural

def natural_chance(state, partner, age):
    carriers, natural = structure(state, partner, age)
    if not natural:
        return 0.0
    g = state.get("gender", "Female")
    f_age = age if g == "Female" else partner["age"]
    m_age = partner["age"] if g == "Female" else age
    base = 0.5 if partner.get("married") else 0.35
    return base * fert_f(f_age) * fert_m(m_age)

ADOPT = {"adopt0": ("Adopt a baby", 0, 12000), "adopt3": ("Adopt a toddler", 3, 9000),
         "adopt8": ("Adopt a child", 8, 6000), "adopt14": ("Adopt a teenager", 14, 4000)}

def adopt_chance(state, age, partner):
    c = 0.88
    if age >= 70: c *= 0.7
    elif age >= 60: c *= 0.85
    if state["stats"]["mental"] < 30: c *= 0.75
    if not partner: c *= 0.95
    return max(0.1, min(0.95, c))

def ivf_cost(carrier_age):
    return 12000 + (8000 if carrier_age >= 46 else 0)

SURROGATE_COST = 50000
SURROGATE_CHANCE = 0.6

# ---------------------------------------------------------------- making the child
def _skin(skin_tone, partner=None):
    pool = [tuple(skin_tone)]
    if partner:
        pool.append(tuple(partner["look"]["skin"]))
    return list(random.choice(pool))

def add_child(state, people, stats, partner, skin_tone, how, age0=0, other=None, log=None):
    """Creates the child and adds them to the family. `how` is a tag shown in
    the log: born, IVF, surrogate, adopted or a fling baby."""
    traits = list(state.get("player_traits", []))
    if how == "adopted":
        kid = P.make_child(traits, None)
        kid["stats"] = P.random_stats(None, 14)
        kid["age"] = age0
        kid["adopted"] = True
        kid["closeness"] = 70 if age0 == 0 else max(40, 62 - age0 * 2)
        kid["trust"] = 65 if age0 == 0 else 45
        kid["look"]["skin"] = list(random.choice([skin_tone, (255, 224, 189), (141, 85, 36), (198, 134, 66), (234, 192, 134)]))
    else:
        parents = [stats]
        ptraits = traits
        if other:
            parents.append(other["stats"])
            ptraits = traits + other["traits"]
        elif partner and how in ("born", "IVF"):
            parents.append(partner["stats"])
            ptraits = traits + partner["traits"]
        else:
            parents.append(P.random_stats(None, 18))
        kid = P.make_child(ptraits, parents)
        kid["look"]["skin"] = _skin(skin_tone, other or partner)
    kid["origin"] = how
    if other:
        kid["other_parent"] = other["name"]
    people.append(kid)
    stats["mental"] = min(100, stats["mental"] + 2)
    return kid

def _noun(kid):
    return "son" if kid["relation"] == "Son" else "daughter"

# ---------------------------------------------------------------- flings and babies
def surprise_year(state, age, partner, friends, people, career, log):
    """Casual relationships can lead to a baby. Returns a list of cards."""
    if len(P.children_of(people)) >= MAX_KIDS:
        return []
    g = state.get("gender", "Female")
    cands = []
    f = state.get("fling")
    if f:
        cands.append(f)
    for m in state.get("love", []):
        if m.get("stage") == "Seeing":
            cands.append(m)
    if partner and partner.get("status") == "situationship":
        cands.append(partner)
    for who in cands:
        if who.get("gender") == g:
            continue
        f_age = age if g == "Female" else who.get("age", 25)
        m_age = who.get("age", 25) if g == "Female" else age
        chance = 0.07 * fert_f(f_age) * fert_m(m_age)
        if random.random() < chance:
            if g == "Female":
                text = f"You're pregnant, and {who['name']} is the other parent."
            else:
                text = f"{who['name']} tells you she's expecting your baby."
            return [{"kind": "surprisebaby", "person": who, "text": text,
                     "why": "What do you want to do?"}]
    return []

def resolve_surprise(inv, pick, state, people, friends, stats, skin_tone, partner, log):
    who = inv["person"]
    if pick == "Stay out of it":
        stats["mental"] = max(0, stats["mental"] - 3)
        stats["social"] = max(0, stats["social"] - 1)
        log(f"You stayed out of it. {who['name']} raised the baby alone.")
        if who is state.get("fling"):
            state["fling"] = None
        if who in state.get("love", []):
            state["love"].remove(who)
        return partner
    kid = add_child(state, people, stats, partner, skin_tone, "fling", 0, other=who)
    together = pick.startswith("Raise")
    if together:
        kid["closeness"] = 72
        log(f"You and {who['name']} welcomed {_noun(kid)} {kid['name']}. You're co-parenting.")
    else:
        kid["closeness"] = 45
        kid["trust"] = 40
        log(f"{who['name']} had {_noun(kid)} {kid['name']}. You support them from a distance.")
    if who is state.get("fling"):
        state["fling"] = None
    if who in state.get("love", []):
        state["love"].remove(who)
    if who is not partner:
        who["category"], who["relation"] = "friend", "Co-parent"
        who["closeness"] = max(35, who.get("closeness", 40))
        friends.append(who)
    return partner

# ---------------------------------------------------------------- the "grow" view
def _used(state):
    return state["actions_used"].get("__grow__", 0) >= 1

def options(state, people, partner, age):
    """List of (id, title, detail, chance, cost, enabled, why_not)."""
    carriers, natural = structure(state, partner, age)
    out = []
    full = len(P.children_of(people)) >= MAX_KIDS
    spent = _used(state) or state["actions_remaining"] <= 0
    def ok(cost, extra=True):
        return (not full) and (not spent) and state["money"] >= cost and extra
    nc = natural_chance(state, partner, age)
    if natural:
        out.append(("nat", "Try for a baby", "With your partner" + (" (married)" if partner.get("married") else ""), nc, 0, ok(0, nc > 0)))
    if carriers:
        who, cage = carriers[0]
        cost = ivf_cost(cage)
        out.append(("ivf", "IVF", ("Donor eggs, so age matters less" if cage >= 46 else "Fertility treatment") +
                    (f" (carried by {who})" if len(carriers) > 1 else ""), ivf_chance(cage), cost, ok(cost)))
    out.append(("sur", "Surrogacy", "A surrogate carries your baby", SURROGATE_CHANCE, SURROGATE_COST, ok(SURROGATE_COST)))
    ac = adopt_chance(state, age, partner)
    for k, (t, a, c) in ADOPT.items():
        out.append((k, t, f"Age {a}" if a else "Newborn", ac, c, ok(c)))
    return out

def draw_grow(screen, body, mouse, state, people, partner, age, b):
    n_kids = len(P.children_of(people))
    draw_text(screen, "Grow your family", font, INK, body.x, body.y + 2)
    draw_text(screen, "Any age, any relationship. One attempt a year.", small_font, MUTED, body.x + 210, body.y + 6)
    carriers, natural = structure(state, partner, age)
    y = body.y + 36
    opts = options(state, people, partner, age)
    if not natural:
        why = "No partner" if not partner else "Not possible naturally" if partner.get("status") != "situationship" else "Make it official first"
        draw_text(screen, f"Natural: {why}. Other routes below.", small_font, MUTED, body.x, y)
        y += 24
    b.setdefault("grow", [])
    for (key, title, detail, chance, cost, enabled) in opts:
        draw_text(screen, title, font, INK if enabled else MUTED, body.x, y)
        draw_text(screen, detail, small_font, MUTED, body.x + 170, y + 3)
        draw_text(screen, f"{int(chance * 100)}% chance", small_font, GREEN if enabled else MUTED, body.x + 400, y + 3)
        draw_text(screen, f"${fmt(cost)}" if cost else "free", small_font, INK if enabled else MUTED, body.x + 500, y + 3)
        r = pygame.Rect(body.right - 66, y - 2, 60, 26)
        if enabled:
            draw_rounded_rect(screen, ACCENT if r.collidepoint(mouse) else (232, 226, 214), r, radius=8)
        draw_text(screen, "Try", small_font, INK if enabled else MUTED, r.centerx, r.centery, centre=True)
        if enabled:
            b["grow"].append((key, r))
        y += 34
    y += 8
    draw_text(screen, f"You have {n_kids} child{'ren' if n_kids != 1 else ''} (up to {MAX_KIDS}).", small_font, MUTED, body.x, y)
    if partner is None:
        draw_text(screen, "You can raise a child on your own.", small_font, MUTED, body.x + 230, y)

def perform(action, state, people, partner, stats, skin_tone, age, log):
    """Carries out an attempt. Returns True if a child joined the family."""
    state["actions_used"]["__grow__"] = 1
    state["actions_remaining"] -= 1
    carriers, natural = structure(state, partner, age)
    if action == "nat":
        if random.random() < natural_chance(state, partner, age):
            kid = add_child(state, people, stats, partner, skin_tone, "born", 0, log=log)
            log(f"Welcomed {_noun(kid)} {kid['name']}.")
            return True
        log("Tried for a baby but no luck this year." + (" Fertility treatment (IVF) may help." if age >= 35 else ""))
        return False
    if action == "ivf":
        who, cage = carriers[0]
        cost = ivf_cost(cage)
        state["money"] -= cost
        if random.random() < ivf_chance(cage):
            kid = add_child(state, people, stats, partner, skin_tone, "IVF", 0, log=log)
            if cage >= 50:
                stats["physical"] = max(0, stats["physical"] - 4)
            log(f"IVF worked! Welcomed {_noun(kid)} {kid['name']} (cost ${fmt(cost)}).")
            return True
        log(f"The IVF cycle didn't work this time (cost ${fmt(cost)}).")
        stats["mental"] = max(0, stats["mental"] - 2)
        return False
    if action == "sur":
        state["money"] -= SURROGATE_COST
        if random.random() < SURROGATE_CHANCE:
            kid = add_child(state, people, stats, partner, skin_tone, "surrogate", 0, log=log)
            log(f"Your surrogate gave birth to {_noun(kid)} {kid['name']} (cost ${fmt(SURROGATE_COST)}).")
            return True
        log(f"The surrogacy didn't work out this time (cost ${fmt(SURROGATE_COST)}).")
        stats["mental"] = max(0, stats["mental"] - 2)
        return False
    if action in ADOPT:
        t, a, c = ADOPT[action]
        if random.random() < adopt_chance(state, age, partner):
            state["money"] -= c
            kid = add_child(state, people, stats, partner, skin_tone, "adopted", a, log=log)
            log(f"Adopted {_noun(kid)} {kid['name']}, age {a} (cost ${fmt(c)}).")
            return True
        fee = c // 4
        state["money"] -= fee
        log(f"The adoption wasn't approved this time. The agency kept a ${fmt(fee)} fee.")
        return False
    return False
