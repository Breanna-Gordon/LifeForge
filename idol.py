"""The idol path: audition for an agency, train for years, debut in a group,
release albums, tour, and maybe go solo when the contract runs out.

state["idol"] holds everything:
  stage     "trainee", "group", "solo" or "ended"
  agency    index into AGENCIES
  skills    vocal / dance / rap / visual, 0-100
  years     years in the current stage
  group, position, fandom, albums [(title, year, sales, peak)], debt (trainee costs still owed)
"""
import math
import random
import pygame
from constants import (WHITE, INK, MUTED, OUTLINE, ACCENT, LIGHT_GREY, DARK_GREY, font, small_font,
                       draw_text, draw_rounded_rect, fmt)
from stories import S, with_

# name, audition bar, debut bar, yearly trainee cost, artist's share of earnings
AGENCIES = [("Starlight Entertainment", 42, 56, 15000, 0.35),
            ("Nova Music", 52, 63, 25000, 0.30),
            ("Apex Entertainment", 64, 70, 40000, 0.25)]
SKILLS = ("vocal", "dance", "rap", "visual")
SKILL_LABEL = {"vocal": "Vocal", "dance": "Dance", "rap": "Rap", "visual": "Visual"}
SKILL_COL = {"vocal": (236, 120, 160), "dance": (110, 150, 236), "rap": (150, 110, 220), "visual": (240, 170, 70)}
POSITION = {"vocal": "Main vocalist", "dance": "Main dancer", "rap": "Main rapper", "visual": "Visual"}
_GROUP_A = ["LUMI", "NOVA", "ECLIPSE", "VELVET", "ORBIT", "PRISM", "HALO", "AURORA", "STELLA", "NEON", "ZEPHYR", "MIRAGE"]
_GROUP_B = ["", "", "", "9", "X", " WAVE", "ISLE", "RA", " BLOOM", "VERSE"]
_ALBUM_A = ["Midnight", "Paper", "Golden", "Electric", "Summer", "Velvet", "Crystal", "Neon", "Lunar", "Wild"]
_ALBUM_B = ["Hearts", "Runaway", "Signal", "Dream", "Fever", "Parade", "Echo", "Garden", "Tempo", "Rush"]
CONTRACT_YEARS = 7
MAX_PER_YEAR = 2           # each training action, per year


def data(state):
    return state.get("idol")

def active(state):
    d = data(state)
    return bool(d) and d["stage"] in ("trainee", "group", "solo")

def _avg(d):
    return sum(d["skills"][k] for k in SKILLS) / len(SKILLS)

def _fame(state, n=None):
    c = state.get("_career") or {}
    if n is not None:
        c["fame"] = max(0, min(100, c.get("fame", 0) + n))
    return c.get("fame", 0)

def _start_skills(state):
    import skills as SK
    s = state["stats"]
    return {"vocal": min(90, 22 + SK.level_of(state, "singing") * 6 + s["social"] // 5),
            "dance": min(90, 22 + SK.level_of(state, "dance") * 6 + s["athletic"] // 5),
            "rap": min(90, 18 + SK.level_of(state, "music") * 5 + s["academic"] // 8 + s["social"] // 10),
            "visual": min(95, int(s["looks"] * 0.85))}

def job_label(state):
    d = data(state)
    if not d:
        return None
    ag = AGENCIES[d["agency"]][0]
    if d["stage"] == "trainee":
        return f"Trainee, {ag.split()[0]}"
    if d["stage"] == "group":
        return f"Idol, {d['group']}"
    if d["stage"] == "solo":
        return "Solo artist"
    return None

def last_pay(state):
    d = data(state)
    return d.get("last_pay", 0) if d else 0


# ---------------------------------------------------------------- actions
def audition(state, log):
    age = state["age"]
    if state.get("_idol_aud") == age:
        return log("Agencies only hold open auditions once a year.")
    state["_idol_aud"] = age
    skills = _start_skills(state)
    pull = fame_pull(state)
    score = sum(skills.values()) / 4 * 0.6 + state["stats"]["looks"] * 0.4 + random.randint(-8, 8) + pull
    offers = [i for i, a in enumerate(AGENCIES) if score >= a[1]]
    if not offers:
        return log("No agency called back. Practise singing or dance (Skills) and work on your looks, then try again.")
    tier = max(offers)
    state["idol"] = {"stage": "trainee", "agency": tier, "skills": skills, "years": 0, "group": None, "position": None,
                     "fandom": 0, "albums": [], "debt": 0, "used": {}, "total_years": 0, "contract": 0}
    log(f"You passed the audition! {AGENCIES[tier][0]} signed you as a trainee."
        + (" Your name got you noticed before you'd sung a note." if pull >= 4 else ""))

def fame_pull(state):
    """Audition points from fame: agencies love a name the public already knows."""
    import celebrity
    return int(_fame(state) * 0.15) + (4 if celebrity.showbiz_family(state) else 0)

def _train(d, state, key, log):
    cur = d["skills"][key]
    gain = max(1, round((random.randint(2, 5) + (1 if state["stats"]["mental"] >= 60 else 0)) * (1 - cur / 125)))
    d["skills"][key] = min(100, d["skills"][key] + gain)
    st = state["stats"]
    if key == "dance":
        st["athletic"] = min(100, st["athletic"] + 1)
    elif key == "visual":
        st["looks"] = min(100, st["looks"] + 1)
    st["mental"] = max(0, st["mental"] - 1)
    log(f"{SKILL_LABEL[key]} training: +{gain} (now {d['skills'][key]}).")

def fan_cap(d):
    """How big a fandom can get: bigger agencies reach further, better idols keep fans."""
    return int(2_000_000 * (1 + d["agency"] * 1.5) * (0.4 + _avg(d) / 100) * (1.4 if d["stage"] == "solo" else 1.0)
               * (0.85 + d.get("fame", 0) / 220))

def grow(d, rate, flat=0):
    room = max(0.0, 1 - d["fandom"] / fan_cap(d))
    d["fandom"] = int(d["fandom"] + d["fandom"] * rate * room + flat * room)

def _album_name():
    return f"{random.choice(_ALBUM_A)} {random.choice(_ALBUM_B)}"

def _earn(state, d, gross, what, log):
    """The agency takes its cut and recovers trainee costs before you see a cent."""
    share = 0.7 if d["stage"] == "solo" and d.get("indie") else AGENCIES[d["agency"]][4] + (0.15 if d.get("renewed") else 0)
    mine = int(gross * share)
    repay = min(d["debt"], mine)
    d["debt"] -= repay
    mine -= repay
    state["money"] += mine
    d["pay_year"] = d.get("pay_year", 0) + mine
    note = f" (${fmt(repay)} went to repaying trainee costs)" if repay else ""
    log(f"{what} You took home ${fmt(mine)}{note}.")

def comeback(state, d, log):
    quality = max(10, min(100, _avg(d) + random.randint(-12, 12) + min(8, d["years"] * 2) + d.get("pen", 0) // 8))
    fame = _fame(state)
    sales = int(max(2000, d["fandom"]) * random.uniform(0.1, 0.25) * (0.5 + quality / 100) * (1 + fame / 150))
    peak = max(1, min(100, int(118 - quality * 0.65 - math.log10(max(10, sales)) * 9 + random.randint(-8, 8))))
    title = _album_name()
    kind = "album" if len(d["albums"]) % 3 == 2 else "mini album"
    d["albums"].append((title, state["age"], sales, peak))
    grow(d, 0.15 * quality / 70 + (0.1 if peak <= 10 else 0), 4000 + fame * 400)
    _fame(state, 2 + (4 if peak <= 10 else 0) + (4 if peak == 1 else 0))
    _earn(state, d, sales * 12, f"Your {kind} '{title}' sold {fmt(sales)} copies and peaked at #{peak}.", log)
    if d.get("pen", 0) >= 20:       # songwriting royalties are yours, not the agency's
        roy = int(sales * 2 * d["pen"] / 100)
        state["money"] += roy
        d["pay_year"] = d.get("pay_year", 0) + roy
        log(f"You wrote on the {kind}: ${fmt(roy)} in songwriting royalties.")

def tour(state, d, log):
    cities = min(60, random.randint(6, 12) + d["fandom"] // 400000)
    gross = int(cities * min(d["fandom"] * 0.006, 25000) * random.uniform(40, 70) * (1 + _fame(state) / 200))      # shows x seats x ticket price
    grow(d, 0.06)
    d["tours"] = d.get("tours", 0) + 1
    st = state["stats"]
    st["physical"] = max(0, st["physical"] - 4)
    st["mental"] = max(0, st["mental"] - 3)
    st["social"] = min(100, st["social"] + 2)
    _fame(state, 4)
    _earn(state, d, gross, f"Your tour played {cities} cities to sold-out crowds.", log)

ACTIONS = {
    "trainee": [("vocal", "Vocal lessons"), ("dance", "Dance practice"), ("rap", "Rap & songwriting"), ("visual", "Visual & variety coaching"),
                ("rest", "Rest day"), ("quit", "Leave the agency")],
    "group": [("comeback", "Release a comeback"), ("tour", "Go on tour"), ("fanmeet", "Hold a fan meeting"), ("variety", "Guest on a variety show"),
              ("write", "Write & produce a song"), ("drama", "Act in a drama"), ("cf", "Shoot an ad (CF)"),
              ("vocal", "Vocal practice"), ("dance", "Dance practice"), ("solo", "Debut as a soloist"), ("quit", "Leave the industry")],
    "solo": [("comeback", "Release an album"), ("tour", "Go on tour"), ("fanmeet", "Hold a fan meeting"), ("variety", "Guest on a variety show"),
             ("write", "Write & produce a song"), ("drama", "Act in a drama"), ("cf", "Shoot an ad (CF)"),
             ("vocal", "Vocal practice"), ("dance", "Dance practice"), ("quit", "Retire from music")],
}
_ONCE = {"comeback", "tour", "solo", "drama"}       # once a year
_TWICE = {"fanmeet", "variety", "write", "cf"}

def can(state, d, key):
    """None if allowed, else the reason it isn't."""
    used = d.setdefault("used", {})
    if key in _ONCE and used.get(key):
        return "Once a year"
    if (key in SKILLS or key in _TWICE) and used.get(key, 0) >= MAX_PER_YEAR:
        return "Done twice this year"
    if key == "tour" and not d["albums"]:
        return "Release music first"
    if key == "tour" and d["fandom"] < 30000:
        return "Needs 30k fans"
    if key == "solo" and (d["years"] < 3 or _fame(state) < 45):
        return "3 years + fame 45"
    if key == "write":
        import skills as SK
        if SK.level_of(state, "music") < 2 and d.get("pen", 0) < 10:
            return "Needs Music skill 2"
    if key == "drama" and d["skills"]["visual"] < 55:
        return "Needs Visual 55"
    if key == "cf" and d["skills"]["visual"] < 45:
        return "Needs Visual 45"
    return None

def do(state, key, log):
    d = data(state)
    if can(state, d, key):
        return False
    used = d["used"]
    used[key] = used.get(key, 0) + 1
    d["fame"] = _fame(state)
    st = state["stats"]
    if key in SKILLS:
        _train(d, state, key, log)
    elif key == "rest":
        st["mental"] = min(100, st["mental"] + 4)
        log("You took a rare day off. You slept for fourteen hours.")
    elif key == "comeback":
        comeback(state, d, log)
    elif key == "tour":
        tour(state, d, log)
    elif key == "fanmeet":
        grow(d, 0.03, 2000)
        st["social"] = min(100, st["social"] + 2)
        st["mental"] = min(100, st["mental"] + 1)
        log("Your fan meeting sold out in minutes. Fans cried, you cried.")
    elif key == "variety":
        _fame(state, 3)
        grow(d, 0.01 + _fame(state) / 2500)
        st["social"] = min(100, st["social"] + 2)
        log("Your variety show appearance became a viral clip.")
    elif key == "write":
        import pathways
        gain = max(1, round(random.randint(4, 8) * (1 - d.get("pen", 0) / 120)))
        d["pen"] = min(100, d.get("pen", 0) + gain)
        pathways.credit(state, "songs")
        st["mental"] = max(0, st["mental"] - 1)
        log(f"You spent nights in the studio writing. Songwriting +{gain} (now {d['pen']}). Your next release will be better.")
    elif key == "drama":
        import pathways
        pathways.credit(state, "acting")
        _fame(state, 3)
        grow(d, 0.03)
        st["mental"] = max(0, st["mental"] - 2)
        _earn(state, d, 60000 + _fame(state) * 3000, "You filmed a drama between schedules. Viewers loved you.", log)
    elif key == "cf":
        import pathways
        pathways.credit(state, "modelling")
        st["looks"] = min(100, st["looks"] + 1)
        _earn(state, d, 20000 + int(d["fandom"] * 0.04), "You shot an ad campaign for a big brand.", log)
    elif key == "solo":
        go_solo(state, d, log)
    elif key == "quit":
        end(state, d, log, "You walked away from the idol life.")
    return True

def go_solo(state, d, log, indie=False):
    d["stage"], d["years"], d["indie"] = "solo", 0, indie
    d["fandom"] = int(d["fandom"] * 0.7)
    _fame(state, 4)
    log(f"You made your solo debut{' as an independent artist' if indie else ''}. Some fans followed you, some stayed with {d['group']}.")

def end(state, d, log, text):
    d["stage"] = "ended"
    log(text)


# ---------------------------------------------------------------- yearly upkeep
def year(state, career, age, log):
    d = data(state)
    if not d or d["stage"] == "ended":
        return
    d["used"] = {}
    d["years"] += 1
    d["total_years"] = d.get("total_years", 0) + 1
    d["last_pay"], d["pay_year"] = d.get("pay_year", 0), 0
    name, aud_bar, debut_bar, cost, _ = AGENCIES[d["agency"]]
    st = state["stats"]
    fame = d["fame"] = _fame(state)
    debut_bar -= fame // 6          # a known name sells albums, so the bar is lower
    if d.get("fast"):
        debut_bar -= 6
    if d["stage"] == "trainee":
        d["debt"] += cost
        st["mental"] = max(0, st["mental"] - 2)
        avg = _avg(d)
        cut = (avg < debut_bar - 8 and d["years"] >= 2 and random.random() < 0.3) or (d["years"] >= 5 and random.random() < 0.35)
        if cut or age > 25:
            end(state, d, log, f"After your evaluation, {name} let you go. It hurts, but you're free." + (" Your trainee debt was written off." if d["debt"] else ""))
            d["debt"] = 0
        elif (d["years"] >= 2 or d.get("fast")) and avg >= debut_bar and random.random() < 0.3 + (avg - debut_bar) / 30 + fame / 250:
            best = max(SKILLS, key=lambda k: d["skills"][k])
            d["stage"], d["years"], d["contract"] = "group", 0, CONTRACT_YEARS
            d["group"] = random.choice(_GROUP_A) + random.choice(_GROUP_B)
            d["position"] = POSITION[best]
            d["fandom"] = int(random.uniform(8000, 25000) * (d["agency"] + 1) * (1 + fame / 35))
            _fame(state, 12)
            log(f"Debut day! You debuted as the {d['position'].lower()} of {d['group']} under {name}."
                + (" The press covered it everywhere: your name was already known." if fame >= 25 else ""))
        else:
            log(f"Another year of training at {name}. Monthly evaluations: {int(avg)}/100 (debut needs about {debut_bar}).")
        return
    # debuted
    st["mental"] = max(0, st["mental"] - 1)
    if not d["used"] and d.get("_quiet"):
        pass
    released = any(a[1] == age - 1 or a[1] == age for a in d["albums"][-1:])
    if released:
        grow(d, 0.02)
    else:
        d["fandom"] = int(d["fandom"] * 0.88)
    target = min(96, int(math.log10(max(10, d["fandom"])) * 16))
    career["fame"] = max(career.get("fame", 0), int(career.get("fame", 0) * 0.6 + target * 0.4))
    if d["stage"] == "group":
        d["contract"] -= 1
        # nobody made the call: the contract lapses and the group winds down
        if d["contract"] <= (-1 if d.get("renewed") else -3):
            end(state, d, log, f"{d['group']}'s contract ran out and the members went their separate ways.")

def snapshot_rows(state):
    d = data(state)
    if not d or d["stage"] in ("trainee", "ended"):
        return []
    from publiclife import short
    return [("Fandom", short(d["fandom"]))]


# ---------------------------------------------------------------- the Idol panel
def _bar(screen, x, y, w, v, col):
    r = pygame.Rect(x, y, w, 8)
    draw_rounded_rect(screen, LIGHT_GREY, r, radius=4)
    draw_rounded_rect(screen, col, (r.x, r.y, max(6, int(w * v / 100)), r.h), radius=4)

def draw_panel(screen, rect, mouse, state):
    buttons = {"_idol": True, "acts": []}
    d = data(state)
    age = state.get("age", 0)
    no_budget = state["actions_remaining"] <= 0
    if not d or d["stage"] == "ended":
        draw_text(screen, "Idol", font, INK, rect.x, rect.y)
        if d:
            draw_text(screen, f"Your idol days are behind you. {len(d['albums'])} releases, {d.get('tours', 0)} tours.", small_font, MUTED, rect.x, rect.y + 32)
        draw_text(screen, "Agencies train young singers and dancers for years before they debut in a group.", small_font, MUTED, rect.x, rect.y + 56)
        draw_text(screen, "They judge your singing, dancing and looks. Practise Singing and Dance under Skills first.", small_font, MUTED, rect.x, rect.y + 76)
        for n, a in enumerate(AGENCIES):
            draw_text(screen, f"{a[0]}: audition bar {a[1]}, keeps {int(a[4] * 100)}% for you", small_font, DARK_GREY, rect.x + 10, rect.y + 108 + n * 22)
        pull = fame_pull(state)
        if pull:
            draw_text(screen, f"Your fame gives you +{pull} at auditions, and it will boost your sales and fandom.",
                      small_font, (176, 90, 140), rect.x, rect.y + 238)
        b = pygame.Rect(rect.x, rect.y + 186, 220, 40)
        ok = 11 <= age <= 23 and not no_budget and not (d and d["stage"] == "ended")
        draw_rounded_rect(screen, ACCENT if ok and b.collidepoint(mouse) else (WHITE if ok else LIGHT_GREY), b, radius=10)
        pygame.draw.rect(screen, OUTLINE, b, 1, border_radius=10)
        draw_text(screen, "Audition for an agency", small_font, INK, b.centerx, b.centery, centre=True)
        if not 11 <= age <= 23:
            draw_text(screen, "Auditions are for ages 11 to 23.", small_font, DARK_GREY, b.right + 12, b.y + 12)
        if ok:
            buttons["audition"] = b
        return buttons
    ag = AGENCIES[d["agency"]][0]
    if d["stage"] == "trainee":
        head, sub = f"Trainee at {ag}", f"Year {d['years'] + 1} of training. Debut needs skills around {AGENCIES[d['agency']][2]}."
    elif d["stage"] == "group":
        head, sub = f"{d['position']} of {d['group']}", f"{ag} · debuted {d['years']} yr{'s' if d['years'] != 1 else ''} ago · contract: {max(0, d['contract'])} yrs left"
    else:
        head, sub = "Solo artist", ("Independent" if d.get("indie") else ag) + f" · {d['years']} yrs solo"
    draw_text(screen, head, font, INK, rect.x, rect.y)
    draw_text(screen, sub, small_font, MUTED, rect.x, rect.y + 28)
    from publiclife import short
    info = f"Fandom {short(d['fandom'])}" if d["stage"] != "trainee" else "Fandom: not debuted yet"
    info += f"   ·   Fame {_fame(state)}"
    if d["debt"]:
        info += f"   ·   Trainee debt ${fmt(d['debt'])}"
    draw_text(screen, info, small_font, DARK_GREY, rect.x, rect.y + 48)
    card = pygame.Rect(rect.x, rect.y + 74, 250, 128)
    draw_rounded_rect(screen, WHITE, card, radius=12)
    pygame.draw.rect(screen, OUTLINE, card, 1, border_radius=12)
    for n, k in enumerate(SKILLS):
        y = card.y + 12 + n * 28
        draw_text(screen, SKILL_LABEL[k], small_font, INK, card.x + 12, y)
        draw_text(screen, str(d["skills"][k]), small_font, MUTED, card.right - 34, y)
        _bar(screen, card.x + 70, y + 6, 140, d["skills"][k], SKILL_COL[k])
    acts = ACTIONS[d["stage"]]
    for n, (key, label) in enumerate(acts):
        r = pygame.Rect(rect.x + 266 + (n % 2) * 205, rect.y + 74 + (n // 2) * 46, 198, 40)
        why = can(state, d, key)
        hot = not why and not no_budget
        danger = key == "quit"
        fill = (255, 236, 218) if hot and r.collidepoint(mouse) else (WHITE if hot else LIGHT_GREY)
        draw_rounded_rect(screen, fill, r, radius=10)
        pygame.draw.rect(screen, (200, 110, 110) if danger else OUTLINE, r, 1, border_radius=10)
        draw_text(screen, label, small_font, (170, 60, 60) if danger else (INK if hot else DARK_GREY), r.x + 10, r.y + (4 if why else 11))
        if why:
            draw_text(screen, why, small_font, DARK_GREY, r.x + 10, r.y + 21)
        if hot:
            buttons["acts"].append((key, r))
    y = rect.y + 74 + ((len(acts) + 1) // 2) * 46 + 14
    if d["albums"]:
        draw_text(screen, "Discography", small_font, INK, rect.x, y)
        for n, (title, yr, sales, peak) in enumerate(reversed(d["albums"][-6:])):
            draw_text(screen, f"Age {yr}   '{title}'   {fmt(sales)} sold   peak #{peak}", small_font, MUTED, rect.x + 10, y + 22 + n * 20)
    elif d["stage"] == "trainee":
        draw_text(screen, "Train hard: the agency evaluates you every month and only the best debut.", small_font, MUTED, rect.x, y)
    return buttons

def handle_click(mx, my, buttons, state, log):
    if state["actions_remaining"] <= 0:
        return
    if buttons.get("audition") and buttons["audition"].collidepoint(mx, my):
        audition(state, log)
        state["actions_remaining"] -= 1
        return
    for key, r in buttons.get("acts", []):
        if r.collidepoint(mx, my) and do(state, key, log):
            state["actions_remaining"] -= 1
            return


# ---------------------------------------------------------------- stories
def _boost(fandom_mult=1.0, fame=0, skill=None, debut=False):
    def fn(state):
        d = data(state)
        if not d:
            return ""
        d["fandom"] = min(fan_cap(d), int(d["fandom"] * fandom_mult) + (20000 if debut else 0))
        _fame(state, fame)
        if skill:
            for k in SKILLS:
                d["skills"][k] = min(100, d["skills"][k] + skill)
        return ""
    return fn

def _fast(state):
    d = data(state)
    d["fast"] = True
    return "Your debut was moved up. The other trainees noticed."

def _renew(choice):
    def fn(state):
        d = data(state)
        if choice == "renew":
            d["contract"], d["renewed"] = 5, True
            return "You renewed with better terms: a bigger share of what you earn."
        if choice == "indie":
            go_solo(state, d, lambda t: None, indie=True)
            return f"{d['group']} went on hiatus and you went independent, keeping most of what you earn."
        end(state, d, lambda t: None, "")
        return f"{d['group']} disbanded after a final farewell concert."
    return fn

def _hiatus(state):
    st = state["stats"]
    st["mental"] = min(100, st["mental"] + 10)
    d = data(state)
    d["fandom"] = int(d["fandom"] * 0.85)
    return "You took a hiatus to recover. Fans sent thousands of letters."

def beats(state, ctx, age):
    d = data(state)
    if not d or d["stage"] == "ended":
        return []
    out = []
    partner = ctx.get("partner")
    best_peak = min((a[3] for a in d["albums"]), default=100)
    import celebrity
    kin = state.get("famous_kin") if celebrity.floor(state) >= 10 else None
    if kin and d["stage"] == "trainee" and not d.get("fast"):
        out.append(("idol_fasttrack", f"The CEO wants to fast-track your debut. Your famous {kin['relation'].lower()} would guarantee headlines.",
                    {"Take the shortcut": with_(S(fn=_fast), mental=1), "Earn it like everyone else": with_(S(fn=_boost(skill=3)), mental=2)}))
    if kin and d["stage"] in ("group", "solo"):
        out.append(("~idol_nepo", f"Netizens call you a 'nepo baby' who only debuted because of {kin['name'].split()[0]}.",
                    {"Let your stage speak for you": {"gamble": [S(fn=_boost(1.06, 2, 2)), {"mental": -3}]},
                     "Clap back online": {"gamble": [S(fn=_boost(1.03, 4)), with_(S(fn=_boost(0.9, -4)), mental=-3)]},
                     "Thank your family in an interview": with_(S(fn=_boost(1.02)), social=2, mental=-1)}))
    if d["stage"] == "trainee":
        out.append(("idol_diet", "Before monthly evaluations, the agency puts every trainee on a strict diet.",
                    {"Follow it": {"looks": 2, "physical": -3, "mental": -2}, "Eat sensibly anyway": {"mental": 1}}))
        out.append(("idol_survival", "A TV survival show wants trainees from your agency. The winners debut instantly.",
                    {"Go on the show": {"gamble": [with_(S(fn=_boost(1.0, 10, 6, True)), mental=-2), with_(S(fn=_boost(1.0, 3)), mental=-6)]},
                     "Stay and train": S(fn=_boost(skill=2))}))
        if d["years"] >= 3:
            out.append(("idol_stuck", "Trainees who joined after you have already debuted. You're still waiting.",
                        {"Keep going": {"mental": -3}, "Ask for a meeting with the CEO": {"gamble": [S(fn=_boost(skill=4)), {"mental": -2}]}}))
        return out
    if partner:
        out.append(("idol_dating", f"A photo of you and {partner['name'].split()[0]} leaks. Your contract has a dating ban.",
                    {"Deny everything": {"gamble": [{"mental": -2}, with_(S(fn=_boost(0.8, -6)), mental=-4)]},
                     "Confirm it proudly": with_(S(fn=_boost(0.88, 2)), mental=3),
                     "Break up to protect your career": with_({"person": (partner, {"closeness": -40})}, mental=-6)}))
    if d["fandom"] >= 100000 and random.random() < 0.4:
        out.append(("~idol_sasaeng", "Obsessive fans followed your van home and found your address.",
                    {"Move and tighten security": with_(S(cash=-20000), mental=-1), "Post a plea for privacy": {"mental": -2, "social": 1}}))
    if state["stats"]["mental"] < 35:
        out.append(("~idol_burnout", "You can barely get out of bed before schedules. Something has to give.",
                    {"Take a hiatus": S(fn=_hiatus), "Push through": {"mental": -6, "physical": -2}}))
    if best_peak <= 3:
        out.append(("idol_award", "You're nominated for Song of the Year at the biggest music awards.",
                    {"Attend": {"gamble": [with_(S(fn=_boost(1.2, 10)), mental=8), {"mental": -1}]}, "Skip it to rest": {"mental": 2}}))
    if d["stage"] == "group" and d["years"] >= 2:
        out.append(("idol_fanwar", "Your fandom is in a vicious online war with a rival group's fans.",
                    {"Ask fans to be kind": with_(S(fn=_boost(1.02)), social=2), "Stay out of it": {"mental": -1}}))
    if d["stage"] == "group" and d["contract"] <= 0:
        out.append(("idol_contract", f"{d['group']}'s 7-year contract is ending. Everyone's waiting for your decision.",
                    {"Renew together": S(fn=_renew("renew")), "Go independent": S(fn=_renew("indie")), "Disband and move on": S(fn=_renew("end"))}))
    return out
