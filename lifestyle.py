import worldjobs
from constants import fmt
"""Lifestyle: a BitLife-style menu of everyday things to do (Mind & Body,
Salon & Spa, Doctor, Love, Freelance Gigs, Money & Business, Leisure,
School, Pets and Crime), plus yearly upkeep for pets, businesses and prison.

Every item costs one action. Nothing is capped: repeating the same thing in
a year just gives smaller results. Under 18, small costs are covered by the
family and bigger ones need parents to say yes."""
import random
import pygame
from constants import OUTLINE, INK, MUTED
from constants import (WHITE, LIGHT_GREY, DARK_GREY, ACCENT, GREEN, RED,
                       font, small_font, draw_text, draw_rounded_rect)

PET_KINDS = [("dog", 13), ("cat", 14), ("hamster", 3), ("rabbit", 8), ("parrot", 20)]
PET_NAMES = ["Biscuit", "Mochi", "Pepper", "Ziggy", "Luna", "Bean", "Nugget", "Pixel", "Tofu", "Maple"]

INDUSTRIES = [
    {"id": "foodtruck", "name": "Food Truck",         "cost": 20000,  "min_stat": None},
    {"id": "beauty",    "name": "Beauty Supply",      "cost": 17500,  "min_stat": None},
    {"id": "clothing",  "name": "Clothing Outlet",    "cost": 25000,  "min_stat": None},
    {"id": "jewellery", "name": "Jewellery",          "cost": 40000,  "min_stat": None},
    {"id": "music",     "name": "Musical Instruments","cost": 22500,  "min_stat": None},
    {"id": "footwear",  "name": "Footwear",           "cost": 22500,  "min_stat": None},
    {"id": "sports",    "name": "Sporting Goods",     "cost": 25000,  "min_stat": None},
    {"id": "robotics",  "name": "Robotics",           "cost": 75000, "min_stat": ("academic", 70)},
]
IND_BY_ID = {i["id"]: i for i in INDUSTRIES}

# ---- gates (return a reason string when something is not allowed) ----------
def _jailed(state):
    return state.get("jail", 0) > 0

def _need_free_to_date(state, age, career):
    if state.get("_has_partner") and not state.get("_casual"):
        return "You're with someone. (Try 'Swipe in secret'...)"
    return None

def _need_partnerless(state, age, career):
    if state.get("_has_partner"):
        return "You already have a partner."
    return None

def _need_money(n):
    return lambda state, age, career: None if (state["money"] >= n or age < 18) else f"You need ${fmt(n)}."

def _need_stat(stat, n):
    return lambda state, age, career: None if state["stats"][stat] >= n else f"Needs {stat.title()} {n}+."

def _need_famous(state, age, career):
    return None if career.get("fame", 0) >= 25 else "You aren't famous enough yet."

# ---- items ---------------------------------------------------------------
def I(id, name, desc, min=0, max=99, cost=0, fx=None, skill=None, special=None, need=None, once=False, pay=None, **kw):
    d = {"id": id, "name": name, "desc": desc, "min": min, "max": max, "cost": cost, "fx": fx or {},
         "skill": skill, "special": special, "need": need, "once": once, "pay": pay}
    d.update(kw)
    return d

ITEMS = {
    "mind": [
        I("gym", "Gym", "Work out at the gym", 14, cost=40, fx={"athletic": 2, "physical": 2, "looks": 1}),
        I("meditate", "Meditate", "Practise meditation", 8, fx={"mental": 3}),
        I("book", "Read a book", "Find a good book", 6, fx={"academic": 2, "mental": 1}),
        I("garden", "Garden", "Tend to your garden", 8, fx={"mental": 2, "physical": 1}),
        I("diet", "Healthy diet", "Start a diet plan", 13, cost=150, fx={"physical": 2, "looks": 2}, once=True),
        I("modelles", "Modelling lessons", "Poise and posing", 12, cost=120, fx={"looks": 1, "social": 1}, skill="modelling"),
        I("actles", "Acting lessons", "Take acting lessons", 8, cost=120, fx={"social": 1, "mental": 1}, skill="acting"),
        I("voiceles", "Voice lessons", "Train your voice", 6, cost=100, fx={"mental": 1, "social": 1}, skill="singing"),
        I("spacecamp", "Space camp", "Go to space camp", 8, 17, cost=800, fx={"academic": 3, "mental": 1}, once=True),
        I("memory", "Memory test", "Have your memory evaluated", 10, fx={"academic": 1}, special="memory"),
        I("yogaact", "Yoga session", "Stretch and breathe", 10, fx={"mental": 2, "physical": 1}),
        I("journal", "Write in a journal", "Get your thoughts out", 10, fx={"mental": 2}),
        I("marathon", "Run a marathon", "26 gruelling miles", 16, 70, cost=60, fx={"athletic": 4, "physical": 2, "mental": 1}, need=_need_stat("athletic", 45)),
    ],
    "salon": [
        I("haircut", "Barber / stylist", "Get a new hairstyle", 10, cost=60, fx={"looks": 1}, special="hair_style"),
        I("dye", "Dye job", "Change your hair colour", 12, cost=90, fx={"looks": 1}, special="hair_colour"),
        I("massage", "Massage", "Get a massage", 16, cost=120, fx={"mental": 3, "physical": 1}),
        I("nails", "Nail salon", "Get your nails done", 12, cost=70, fx={"looks": 1, "social": 1}),
        I("tan", "Tanning salon", "Work on your tan", 16, cost=60, fx={"looks": 2}, special="tan"),
        I("wax", "Waxing salon", "Get waxed", 16, cost=70, fx={"looks": 1}),
        I("tattoo", "Tattoo parlour", "Get inked", 18, cost=250, fx={"looks": 1, "social": 1}),
        I("facial", "Facial", "A glowing complexion", 14, cost=90, fx={"looks": 2}),
        I("eyebrow", "Eyebrows & lashes", "Frame your face", 14, cost=60, fx={"looks": 1}),
    ],
    "health": [
        I("doctor", "Doctor", "See a doctor for a check-up", 0, cost=250, fx={"physical": 4}, pay="family_health"),
        I("therapy", "Therapist", "Talk things through", 14, cost=150, fx={"mental": 5}),
        I("dentist", "Dentist", "Look after your smile", 6, cost=200, fx={"looks": 1, "physical": 1}, pay="family_health"),
        I("surgery", "Plastic surgery", "Change your looks (risky)", 18, cost=9000, special="surgery", once=True),
        I("rehab", "Rehab", "Reset bad habits", 16, cost=3500, fx={"mental": 4, "physical": 4}, special="rehab",
          need=lambda s, a, c: None if s.get("casino_plays", 0) >= 5 or s.get("record", 0) else "Nothing to recover from."),
        I("coach", "Life coach", "Set goals that stick", 16, cost=200, fx={"mental": 3, "academic": 1}),
        I("acupuncture", "Acupuncture", "Needles and calm", 16, cost=110, fx={"physical": 2, "mental": 2}),
        I("eyetest", "Eye test", "Check your vision", 5, cost=60, fx={"physical": 1}, pay="family_health"),
        I("hypno", "Hypnotist", "Break a bad habit", 16, cost=180, fx={"mental": 3}),
    ],
    "love": [
        I("datenight", "Treat yourself to a date", "A romantic evening out", 16, cost=150, special="datenight"),
        I("anniv", "Anniversary dinner", "Celebrate your partner", 18, cost=200, fx={"mental": 2, "social": 1},
          need=lambda s, a, c: None if s.get("_has_partner") else "You need a partner."),
    ],
    "gigs": [
        I("handyman", "Handyman", "$14/hour", 16, special="gig", rate=14, fx={"athletic": 1}, need=_need_stat("athletic", 35)),
        I("tutor", "Tutor", "$10/hour", 15, special="gig", rate=10, fx={"academic": 1, "social": 1}, need=_need_stat("academic", 50)),
        I("caretaker", "Caretaker", "$7/hour", 15, special="gig", rate=7, fx={"mental": 1}),
        I("lawn", "Lawn mower", "$7/hour", 12, special="gig", rate=7, fx={"physical": 1}),
        I("babysit", "Babysitter", "$5/hour", 13, special="gig", rate=5, fx={"social": 1}),
        I("dogwalk", "Dog walker", "$5/hour", 11, special="gig", rate=5, fx={"physical": 1}),
        I("petsit", "Pet sitter", "$5/hour", 12, special="gig", rate=5, fx={"mental": 1}),
    ],
    "money": [
        I("lottery", "Lottery", "Buy a $2 ticket", 18, cost=2, special="lottery"),
        I("casino", "Casino", "Bet $200 at the casino", 18, special="casino", need=_need_money(200)),
        I("sweeps", "Sweepstakes", "Enter for free", 12, special="sweeps"),
        I("shopping", "Shopping spree", "Go shopping", 14, cost=400, fx={"mental": 2, "looks": 1}),
        I("scratch", "Scratch card", "A quick $5 gamble", 18, cost=5, special="lottery"),
        I("garage", "Garage sale", "Sell your old stuff", 14, fx={"social": 1}, special="sweeps"),
    ],
    "leisure": [
        I("movie", "Movie theater", "Go to the movies", 5, cost=15, fx={"mental": 2, "social": 1}, special="movie"),
        I("vacation", "Vacation", "Go on holiday", 8, cost=2500, fx={"mental": 5, "physical": 1}, special="vacation"),
        I("social", "Social media", "Post something online", 12, special="social"),
        I("party", "Throw a party", "Invite everyone round", 14, cost=250, fx={"social": 3, "mental": 1}, special="party"),
        I("concert", "Concert", "See a live show", 12, cost=90, fx={"mental": 3, "social": 2}),
        I("themepark", "Theme park", "Rides and snacks", 5, cost=70, fx={"mental": 3, "social": 1}, pay="family_health"),
        I("museum", "Museum", "Culture day", 6, cost=15, fx={"academic": 2, "mental": 1}),
        I("karaoke", "Karaoke night", "Sing your heart out", 16, cost=40, fx={"social": 2, "mental": 2}),
        I("bowling", "Bowling", "Strikes and spares", 8, cost=25, fx={"social": 2, "athletic": 1}),
        I("fishing", "Fishing trip", "Wait and relax", 8, cost=20, fx={"mental": 3}),
        I("camping", "Camping trip", "Tents and stars", 10, cost=120, fx={"mental": 3, "physical": 2, "social": 1}),
        I("hiking", "Go hiking", "Fresh air and views", 10, fx={"physical": 2, "athletic": 2, "mental": 1}),
        I("photo", "Photography walk", "Take photos", 10, cost=0, fx={"mental": 2}, skill="photography"),
        I("cooking", "Cooking class", "Learn a recipe", 10, cost=60, fx={"mental": 1, "social": 1}, skill="cooking"),
    ],
    "school": [
        I("classmates", "Make friends", "Chat with classmates", 5, 25, fx={"social": 2}, special="classmates"),
        I("faculty", "Faculty", "Interact with your teachers", 5, 25, fx={"academic": 2}, special="faculty"),
        I("nurse", "Nurse", "Visit the school nurse", 5, 18, fx={"physical": 3}),
        I("private", "Prep school", "Ask for an elite prep school (IB diploma)", 8, 17, special="private_school", school="prep"),
        I("boarding", "Boarding school", "Ask for a boarding school", 11, 17, special="private_school", school="boarding"),
        I("artsac", "Arts academy", "Ask for a performing arts academy", 8, 17, special="private_school", school="arts"),
        I("sportsac", "Sports academy", "Ask for a sports academy", 8, 17, special="private_school", school="sports"),
    ],
    "pets": [
        I("adopt", "Adopt a pet", "Give a pet a home", 6, cost=300, special="adopt",
          need=lambda s, a, c: None if len(s.get("pets", [])) < 3 else "Three pets is plenty."),
        I("playpet", "Play with your pets", "Spend time together", 5, fx={"mental": 2, "physical": 1}, special="playpet",
          need=lambda s, a, c: None if s.get("pets") else "You don't have a pet."),
    ],
    "crime": [
        I("shoplift", "Shoplift", "Risk: low", 16, special="crime", crime=("shoplift", 15, 40, 0.22, "a shop")),
        I("pickpocket", "Pickpocket", "Risk: medium", 16, special="crime", crime=("pickpocket", 60, 220, 0.34, "a crowd")),
        I("scam", "Run a scam", "Risk: medium", 18, special="crime", crime=("scam", 400, 2000, 0.40, "a stranger")),
        I("burgle", "Burgle a house", "Risk: high", 18, special="crime", crime=("burgle", 1000, 4000, 0.52, "a house")),
        I("hack", "Hack a company", "Risk: high", 18, special="crime", need=_need_stat("academic", 60), crime=("hack", 1500, 6000, 0.45, "a company")),
        I("gta", "Steal a car", "Risk: high", 17, special="crime", crime=("gta", 800, 3500, 0.48, "a car")),
        I("bank", "Rob a bank", "Risk: very high", 18, special="crime", crime=("bank", 8000, 40000, 0.68, "a bank")),
    ],
    "prison": [
        I("pgym", "Prison gym", "Work out in the yard", 0, fx={"physical": 2, "athletic": 1}),
        I("plib", "Prison library", "Read and study", 0, fx={"academic": 2, "mental": 1}),
        I("good", "Good behaviour", "Try to shorten your sentence", 0, special="good_behaviour"),
    ],
}

CATEGORIES = [
    ("mind", "Mind & Body", "Work on self-improvement", 6, None),
    ("salon", "Salon & Spa", "Take time for yourself", 10, None),
    ("health", "Doctor & Health", "Look after yourself", 0, None),
    ("love", "Date night", "Treat your partner", 16, lambda s, a, c: bool(s.get("_has_partner"))),
    ("gigs", "Freelance Gigs", "Make some quick money", 11, None),
    ("money", "Money & Business", "Lottery, casino, your own company", 12, None),
    ("leisure", "Leisure", "Movies, holidays, social media", 5, None),
    ("school", "School", "Teachers, classmates, nurse", 5, lambda s, a, c: a <= 25 and (a < 18 or c.get("enrolled"))),
    ("pets", "Pets", "Adopt and play", 6, None),
    ("crime", "Crime", "Break the law (risky)", 16, None),
]
CAT_BY_KEY = {c[0]: c for c in CATEGORIES}

def _industry_items():
    out = []
    for ind in INDUSTRIES:
        out.append(I("ind_" + ind["id"], ind["name"], f"Setup ${fmt(ind['cost'])}", 18, cost=ind["cost"],
                     special="start_business", industry=ind["id"],
                     need=_biz_need(ind)))
    return out

def _biz_need(ind):
    def need(state, age, career):
        if state.get("business"):
            return "You already own a business."
        if ind["min_stat"] and state["stats"][ind["min_stat"][0]] < ind["min_stat"][1]:
            return f"Needs {ind['min_stat'][0].title()} {ind['min_stat'][1]}+."
        return None
    return need

def ensure_state(state):
    state.setdefault("pets", [])
    state.setdefault("business", None)
    state.setdefault("demand", {})
    state.setdefault("jail", 0)
    state.setdefault("record", 0)
    state.setdefault("casino_plays", 0)
    state.setdefault("trips", 0)
    state.setdefault("gigs_done", 0)
    state.setdefault("surgeries", 0)
    state.setdefault("lottery_won", False)
    state.setdefault("achievements", [])
    for ind in INDUSTRIES:
        state["demand"].setdefault(ind["id"], random.randint(25, 80))

def items_for(cat, state, age):
    if _jailed(state):
        return ITEMS["prison"]
    pool = _industry_items() if cat == "industries" else ITEMS.get(cat, [])
    return [it for it in pool if it["min"] <= age <= it["max"]]

def visible_categories(state, age, career):
    if _jailed(state):
        return []
    return [c for c in CATEGORIES if c[3] <= age and (c[4] is None or c[4](state, age, career))]

# ---- paying ------------------------------------------------------------------
def _pay(state, age, item, log):
    """Returns the money actually taken, or None if the request fails."""
    cost = item["cost"]
    if not cost:
        return 0
    if age >= 18:
        return cost if state["money"] >= cost else None
    # children: family covers little things and kids' health care; bigger
    # items need a parent to say yes
    if cost <= 40 or item.get("pay") == "family_health":
        return 0
    flag = "__askpay__" + item["id"]
    if item["id"] in state.get("parent_pays", []):
        return 0
    if state["actions_used"].get(flag) == "no":
        log(f"Your parents already said no to {item['name'].lower()} this year.")
        return None
    if not state.get("parents_ok"):
        log("There's nobody to pay for that right now.")
        return None
    chance = worldjobs.tier_value(state, {"Struggling": 0.35, "Comfortable": 0.75, "Wealthy": 0.95})
    if random.random() > chance:
        state["actions_used"][flag] = "no"
        log(f"You asked your parents to pay for {item['name'].lower()}, but they said not this year.")
        return None
    state.setdefault("parent_pays", []).append(item["id"])
    log(f"Your parents agreed to pay for {item['name'].lower()}, and will keep paying for it.")
    return 0

def _gain(state, fx, dim=1.0):
    s = state["stats"]
    for k, v in fx.items():
        s[k] = max(0, min(100, s[k] + (max(1, round(v * dim)) if v > 0 else v)))

def item_label(item, state, age):
    cost = item["cost"]
    if item.get("special") == "gig":
        return "Work"
    if not cost:
        return "Free"
    if age < 18 and cost > 40 and item.get("pay") != "family_health":
        return "Parents pay" if item["id"] in state.get("parent_pays", []) else "Ask parents"
    if age < 18:
        return "Covered"
    return f"${fmt(cost)}"

# ---- drawing ------------------------------------------------------------------
def view_rects(rect):
    labels = [("clubs", "Clubs", 66), ("outings", "Outings", 80), ("sports", "Sports", 72), ("life", "Lifestyle", 0)]
    out, x = {}, rect.right
    for key, _, w in reversed(labels):
        x -= w
        out[key] = pygame.Rect(x, rect.y - 2, w, 24)
        x -= 4
    return out

def draw_lifestyle(screen, rect, mouse_pos, state, age, career):
    ensure_state(state)
    cat = state.get("_ls_cat")
    if _jailed(state):
        cat = "prison"
    hits, back = [], None
    title = "Lifestyle"
    if cat and cat != "prison":
        title = CAT_BY_KEY[cat][1] if cat in CAT_BY_KEY else "Industries"
    if cat == "prison":
        title = f"In prison ({state['jail']} year{'s' if state['jail'] != 1 else ''} left)"
    draw_text(screen, f"{title}  ({state['actions_remaining']} actions left)", font, INK, rect.x, rect.y)
    cols, row_h = 2, 36
    col_w = (rect.width - 12) // cols
    y0 = rect.y + 28
    if cat and cat != "prison":
        back = pygame.Rect(rect.x + 318, rect.y - 2, 84, 24)
        draw_rounded_rect(screen, ACCENT if back.collidepoint(mouse_pos) else WHITE, back, radius=8)
        pygame.draw.rect(screen, OUTLINE, back, 2, border_radius=8)
        draw_text(screen, "< Back", small_font, INK, back.centerx, back.centery, centre=True)
    if cat is None:
        for n, (key, name, sub, mn, vis) in enumerate(visible_categories(state, age, career)):
            col, row = n % cols, n // cols
            r = pygame.Rect(rect.x + col * (col_w + 12), y0 + row * (row_h + 3), col_w, row_h)
            hov = r.collidepoint(mouse_pos)
            draw_rounded_rect(screen, ACCENT if hov else WHITE, r, radius=8)
            pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
            draw_text(screen, name, small_font, INK, r.x + 10, r.y + 2)
            draw_text(screen, sub, small_font, DARK_GREY, r.x + 10, r.y + 18)
            draw_text(screen, ">", small_font, MUTED, r.right - 18, r.y + 10)
            hits.append(("cat", key, r))
        return {"ls": hits, "ls_back": None}
    for n, it in enumerate(items_for(cat, state, age)):
        col, row = n % cols, n // cols
        r = pygame.Rect(rect.x + col * (col_w + 12), y0 + row * (row_h + 3), col_w, row_h)
        reason = it["need"](state, age, career) if it.get("need") else None
        if it["once"] and state["actions_used"].get("__ls__" + it["id"], 0) >= 1:
            reason = "Done for this year."
        can = state["actions_remaining"] > 0 and reason is None and (it["cost"] <= state["money"] or age < 18 or not it["cost"])
        hov = r.collidepoint(mouse_pos) and can
        draw_rounded_rect(screen, ACCENT if hov else (WHITE if can else LIGHT_GREY), r, radius=8)
        pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
        draw_text(screen, it["name"], small_font, INK, r.x + 10, r.y + 2)
        sub = reason or it["desc"]
        if it.get("industry"):
            d = state["demand"].get(it["industry"], 50)
            sub = reason or f"Setup ${fmt(it['cost'])}"
            bar = pygame.Rect(r.right - 70, r.y + 21, 56, 8)
            draw_rounded_rect(screen, LIGHT_GREY, bar, radius=4)
            draw_rounded_rect(screen, GREEN if d >= 55 else (230, 170, 60) if d >= 35 else RED, (bar.x, bar.y, int(bar.w * d / 100), bar.h), radius=4)
            sub = _clip(sub, r.w - 90)
        elif it["id"] == "sellbiz" and state.get("business"):
            sub = f"Get back about ${fmt(int(state['business']['cost'] * 0.7))}"
        elif it.get("special") == "gig":
            sub = f"{it['desc']}"
        if reason is None and it["fx"] and not it.get("industry") and it.get("special") != "gig":
            sub = it["desc"]
        draw_text(screen, _clip(sub, r.w - 20), small_font, DARK_GREY if reason is None else RED, r.x + 10, r.y + 18)
        label = item_label(it, state, age)
        n_done = state["actions_used"].get("__ls__" + it["id"], 0)
        if n_done and not it["once"]:
            label += f"  x{n_done}"
        draw_text(screen, label, small_font, GREEN if label == "Free" else INK, r.right - 10 - small_font.size(label)[0], r.y + 2)
        hits.append(("item", it, r))
    return {"ls": hits, "ls_back": back}

def _clip(text, width):
    while small_font.size(text)[0] > width and len(text) > 4:
        text = text[:-2]
    return text

# ---- clicks -------------------------------------------------------------------
def handle_lifestyle_click(mx, my, buttons, state, age, career, friends, make_friend, log):
    ensure_state(state)
    back = buttons.get("ls_back")
    if back and back.collidepoint(mx, my):
        state["_ls_cat"] = "money" if state.get("_ls_cat") == "industries" else None
        return
    for kind, obj, r in buttons.get("ls", []):
        if not r.collidepoint(mx, my):
            continue
        if kind == "cat":
            state["_ls_cat"] = obj
            return
        _use(obj, state, age, career, friends, make_friend, log)
        return

def _use(it, state, age, career, friends, make_friend, log):
    if state["actions_remaining"] <= 0:
        return
    if it.get("special") == "open_industries":
        state["_ls_cat"] = "industries"
        return
    reason = it["need"](state, age, career) if it.get("need") else None
    if reason:
        log(reason)
        return
    flag = "__ls__" + it["id"]
    n_before = state["actions_used"].get(flag, 0)
    if it["once"] and n_before >= 1:
        return
    paid = _pay(state, age, it, log)
    if paid is None:
        return
    state["actions_remaining"] -= 1
    state["actions_used"][flag] = n_before + 1
    state["money"] -= paid
    dim = max(0.3, 1 / (1 + 0.5 * n_before))
    _gain(state, it["fx"], dim)
    if it["skill"]:
        sk = state.setdefault("skills", {})
        sk[it["skill"]] = sk.get(it["skill"], 0) + 1
        log(f"{it['name']}: {it['skill'].title()} is now level {sk[it['skill']]}.")
    sp = it.get("special")
    if sp:
        SPECIAL[sp](it, state, age, career, friends, make_friend, log, dim, paid)
    elif not it["skill"]:
        log(f"{it['name']}.")

# ---- special handlers -----------------------------------------------------------
def _sp_hair_style(it, state, age, career, friends, make_friend, log, dim, paid):
    state["_hair_change"] = "style"
    log("Got a brand new hairstyle.")

def _sp_hair_colour(it, state, age, career, friends, make_friend, log, dim, paid):
    state["_hair_change"] = "colour"
    log("Dyed your hair a new colour.")

def _sp_tan(it, state, age, career, friends, make_friend, log, dim, paid):
    if random.random() < 0.2:
        state["stats"]["physical"] = max(0, state["stats"]["physical"] - 3)
        log("Got a bit too much sun at the tanning salon.")
    else:
        log("Worked on your tan.")

def _sp_surgery(it, state, age, career, friends, make_friend, log, dim, paid):
    state["surgeries"] = state.get("surgeries", 0) + 1
    s = state["stats"]
    if random.random() < 0.15:
        s["looks"] = max(0, s["looks"] - 8)
        s["physical"] = max(0, s["physical"] - 5)
        log("The plastic surgery went badly wrong.")
    else:
        s["looks"] = min(100, s["looks"] + random.randint(7, 12))
        log("Plastic surgery: you like what you see.")

def _sp_rehab(it, state, age, career, friends, make_friend, log, dim, paid):
    state["casino_plays"] = 0
    log("A stint in rehab helped you reset.")

def _sp_memory(it, state, age, career, friends, make_friend, log, dim, paid):
    sc = state["stats"]["academic"]
    log("Memory test: " + ("sharp as a tack." if sc >= 70 else "pretty average." if sc >= 40 else "could be better. Try reading more."))

def _sp_dating(it, state, age, career, friends, make_friend, log, dim, paid):
    state["_want_prospect"] = "dating"
    log("Browsed the dating app...")

def _sp_dating_plus(it, state, age, career, friends, make_friend, log, dim, paid):
    state["_want_prospect"] = "plus"
    log("Browsed the premium dating app...")

def _sp_dating_secret(it, state, age, career, friends, make_friend, log, dim, paid):
    state["_want_prospect"] = "secret"
    log("Swiped in secret...")

def _sp_celeb(it, state, age, career, friends, make_friend, log, dim, paid):
    state["_want_prospect"] = "celeb"
    log("Tried the celebrity dating app...")

def _sp_datenight(it, state, age, career, friends, make_friend, log, dim, paid):
    if state.get("_has_partner"):
        state["_date_night"] = True       # main nudges the partner's bonds
        state["stats"]["mental"] = min(100, state["stats"]["mental"] + 2)
        log("A lovely evening out with your partner.")
    else:
        state["stats"]["mental"] = min(100, state["stats"]["mental"] + 1)
        log("Treated yourself to a night out, solo.")

def _sp_gig(it, state, age, career, friends, make_friend, log, dim, paid):
    hours = max(3, round(random.randint(8, 22) * max(0.4, 1 / (1 + 0.25 * (state["actions_used"].get("__ls__" + it["id"], 1) - 1)))))
    got = it["rate"] * hours
    state["money"] += got
    state["gigs_done"] = state.get("gigs_done", 0) + 1
    log(f"{it['name']} gig: earned ${fmt(got)} for {hours} hours' work.")

def _sp_lottery(it, state, age, career, friends, make_friend, log, dim, paid):
    r = random.random()
    if r < 1 / 20000:
        state["money"] += 250000
        state["lottery_won"] = True
        log("You won the lottery jackpot: $250,000!")
    elif r < 1 / 20000 + 1 / 12:
        state["money"] += 10
        log("Lottery: you won $10.")
    else:
        log("Lottery: no luck this time.")

def _sp_casino(it, state, age, career, friends, make_friend, log, dim, paid):
    state["casino_plays"] = state.get("casino_plays", 0) + 1
    if random.random() < 0.46:
        state["money"] += 200
        log("Casino: you won $200!")
    else:
        state["money"] -= 200
        state["stats"]["mental"] = max(0, state["stats"]["mental"] - 1)
        log("Casino: you lost $200.")

def _sp_sweeps(it, state, age, career, friends, make_friend, log, dim, paid):
    if random.random() < 1 / 120:
        state["money"] += 500
        log("You won $500 in a sweepstake!")
    else:
        log("Entered the sweepstakes. Nothing yet.")

def _sp_start_business(it, state, age, career, friends, make_friend, log, dim, paid):
    ind = IND_BY_ID[it["industry"]]
    state["business"] = {"industry": ind["id"], "name": ind["name"], "cost": ind["cost"], "years": 0}
    state["_ls_cat"] = "money"
    log(f"Opened a {ind['name']} business.")

def _sp_sell_business(it, state, age, career, friends, make_friend, log, dim, paid):
    b = state["business"]
    got = int(b["cost"] * 0.7)
    state["money"] += got
    state["business"] = None
    log(f"Sold your {b['name']} business for ${fmt(got)}.")

def _sp_movie(it, state, age, career, friends, make_friend, log, dim, paid):
    if friends and random.random() < 0.5:
        f = random.choice(friends)
        f["closeness"] = min(100, f["closeness"] + 3)
        log(f"Watched a film with {f['name']}.")
    else:
        log("Went to the movies.")

def _sp_vacation(it, state, age, career, friends, make_friend, log, dim, paid):
    state["trips"] = state.get("trips", 0) + 1
    r = random.random()
    if r < 0.15 and age >= 18:
        lost = min(state["money"], 40)
        state["money"] -= lost
        log(f"Holiday mishap: lost ${fmt(lost)} of spending money, but still had fun.")
    elif r < 0.35:
        log("Met interesting people on holiday.")
        if len(friends) < 8:
            f = make_friend()
            log(f"Made a friend abroad: {f['name']}.")
    else:
        log("A relaxing holiday away.")

def _sp_social(it, state, age, career, friends, make_friend, log, dim, paid):
    s = state["stats"]
    if random.random() < 0.08 + (0.1 if s["looks"] >= 70 else 0):
        s["social"] = min(100, s["social"] + 4)
        career["fame"] = min(100, career.get("fame", 0) + 3)
        log("A post went viral!")
    elif random.random() < 0.1:
        s["mental"] = max(0, s["mental"] - 2)
        log("Trolls ruined your day online.")
    else:
        s["social"] = min(100, s["social"] + 1)
        log("Posted online and got some likes.")

def _sp_party(it, state, age, career, friends, make_friend, log, dim, paid):
    for f in friends:
        f["closeness"] = min(100, f["closeness"] + 2)
    log("Threw a party for your friends.")

def _sp_classmates(it, state, age, career, friends, make_friend, log, dim, paid):
    cl = state.get("classmates", [])
    if not cl:
        log("There's nobody in your class right now.")
        return
    c = random.choice(cl)
    c["closeness"] = min(100, c["closeness"] + 10)
    c["contacted"] = True
    if c["closeness"] >= 40 and random.random() < 0.6 and len(friends) < 10:
        cl.remove(c)
        c["category"], c["relation"] = "friend", "Friend"
        friends.append(c)
        log(f"Became friends with {c['name']} at school.")
    else:
        log(f"Chatted with {c['name']} from class.")

def _sp_faculty(it, state, age, career, friends, make_friend, log, dim, paid):
    log("A teacher gave you extra guidance." if random.random() < 0.7 else "A teacher gave you a tough talk about homework.")

SCHOOLS = {"prep": ("Elite prep school", "IB Diploma", {"academic": 3}, {"academic": 1}, 6),
           "boarding": ("Boarding school", "Boarding School Certificate", {"academic": 2, "mental": 1}, {"academic": 1, "social": 1}, 4),
           "arts": ("Arts academy", "Performing Arts Diploma", {"looks": 2, "social": 2}, {"social": 1, "looks": 1}, 3),
           "sports": ("Sports academy", "Sports Excellence Diploma", {"athletic": 4}, {"athletic": 1, "physical": 1}, 3)}

def _sp_private_school(it, state, age, career, friends, make_friend, log, dim, paid):
    chance = worldjobs.tier_value(state, {"Struggling": 0.05, "Comfortable": 0.25, "Wealthy": 0.6})
    kind = it.get("school", "prep")
    name, diploma, join_fx, _, _ = SCHOOLS[kind]
    if state.get("private_school"):
        log("You already go to a private school.")
    elif state.get("parents_ok") and random.random() < chance:
        state["private_school"] = kind
        for k, v in join_fx.items():
            state["stats"][k] = min(100, state["stats"][k] + v)
        log(f"Your parents agreed. You joined the {name.lower()}!")
    else:
        log("Your parents said that school isn't an option.")

def _sp_adopt(it, state, age, career, friends, make_friend, log, dim, paid):
    kind, life = random.choice(PET_KINDS)
    name = random.choice(PET_NAMES)
    state["pets"].append({"name": name, "kind": kind, "age": 0, "life": life + random.randint(-2, 2)})
    log(f"Adopted a {kind} called {name}.")

def _sp_playpet(it, state, age, career, friends, make_friend, log, dim, paid):
    p = random.choice(state["pets"])
    log(f"Played with {p['name']} the {p['kind']}.")

def _sp_crime(it, state, age, career, friends, make_friend, log, dim, paid):
    key, lo, hi, risk, target = it["crime"]
    s = state["stats"]
    risk = max(0.08, risk - (s["academic"] - 50) / 400 - (s["social"] - 50) / 600 + 0.05 * state.get("record", 0))
    if random.random() >= risk:
        got = random.randint(lo, hi)
        state["money"] += got
        s["mental"] = max(0, s["mental"] - 1)
        log(f"You got away with it: ${fmt(got)} from {target}.")
        return
    state["record"] = state.get("record", 0) + 1
    if key == "shoplift" and random.random() < 0.6:
        fine = min(state["money"], random.randint(100, 600))
        state["money"] -= fine
        log(f"Caught shoplifting. You were fined ${fmt(fine)} and got a criminal record.")
        return
    years = random.randint(1, 3) if key in ("shoplift", "pickpocket", "scam") else random.randint(2, 4)
    state["jail"] = years
    career["job"] = None
    career["hustle"] = None
    if career.get("enrolled"):
        career["enrolled"] = False
    state["activities"] = {}
    state["_ls_cat"] = None
    log(f"Caught! You were sentenced to {years} year{'s' if years != 1 else ''} in prison.")

def _sp_good_behaviour(it, state, age, career, friends, make_friend, log, dim, paid):
    if random.random() < 0.5 and state["jail"] > 1:
        state["jail"] -= 1
        log("Good behaviour: your sentence was shortened by a year.")
    else:
        log("You kept your head down. Nothing changed yet.")

SPECIAL = {k[4:]: v for k, v in globals().items() if k.startswith("_sp_")}

# ---- yearly upkeep ------------------------------------------------------------
def advance_lifestyle_year(state, career, age, log):
    ensure_state(state)
    s = state["stats"]
    if state["jail"] > 0:
        state["jail"] -= 1
        s["mental"] = max(0, s["mental"] - 3)
        s["social"] = max(0, s["social"] - 2)
        if state["jail"] == 0:
            log("You were released from prison.")
        else:
            log(f"Another year in prison ({state['jail']} left).")
    pets = state["pets"]
    for p in list(pets):
        p["age"] += 1
        if p["age"] >= p["life"]:
            pets.remove(p)
            s["mental"] = max(0, s["mental"] - 3)
            log(f"{p['name']} the {p['kind']} passed away. You miss them.")
    if pets:
        s["mental"] = min(100, s["mental"] + min(2, len(pets)))
        if age >= 18:
            vet = 300 * len(pets)
            state["money"] = max(0, state["money"] - vet)
    for k in state["demand"]:
        state["demand"][k] = max(10, min(95, state["demand"][k] + random.randint(-12, 12)))
    import business as _biz
    _biz.business_year(state, age, career, log)
    ps = state.get("private_school")
    if ps and age < 18:
        kind = ps if isinstance(ps, str) and ps in SCHOOLS else "prep"
        for k, v in SCHOOLS[kind][3].items():
            s[k] = min(100, s[k] + v)
        if age == 17:
            career["prestige"] = career.get("prestige", 0) + SCHOOLS[kind][4]
            state["school_diploma"] = SCHOOLS[kind][1]
            log(f"You graduated with a {SCHOOLS[kind][1]}. Universities notice.")
