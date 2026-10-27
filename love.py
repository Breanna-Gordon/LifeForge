"""The Love window: matches in talking stages, dating apps and social media.

You can be talking to several people at once. Each match has a "stage":
  Talking  -> Seeing  -> (Make official: they become your partner)
Your official partner stays in the People tab. Keeping matches on the side
while you have a partner is cheating, and it can come out.

Apps come in tiers: free swipe app, a premium one, an invite-only app for
the wealthy, an app for famous people and a paid matchmaker. Teens can't use
apps, but they can ask out a crush at school."""
import random
import pygame
from constants import fmt, OUTLINE, INK, MUTED
from constants import (WHITE, LIGHT_GREY, DARK_GREY, ACCENT, GREEN, RED,
                       font, small_font, draw_text, draw_rounded_rect)
import worldjobs
from people import (make_prospect, draw_person_avatar, occupation, compatibility, remember, near_age,
                    make_person)

MAX_MATCHES = 5
VIEWS = [("matches", "Matches", 84), ("apps", "Dating apps", 112), ("social", "Social media", 118)]
RICH_JOBS = ["Surgeon", "Company CEO", "Investment Banker", "Film Director", "Pilot", "Judge", "Landowner", "Lawyer", "Architect"]
CELEB_JOBS = ["Actor", "Singer", "Footballer", "Influencer", "Model", "Basketball Player", "Comedian", "DJ"]

def _networth(state):
    return state.get("money", 0) + state.get("savings", 0) + state.get("invest", 0) - state.get("debt", 0)

def _rich(state, age, career):
    if _networth(state) >= 100000 or state.get("family_wealth") in ("Elite", "Royalty"):
        return None
    return "Needs about $100,000 in net worth, or a rich family."

def _famous(state, age, career):
    return None if career.get("fame", 0) >= 25 else "Needs fame 25+."

def _student(state, age, career):
    return None if career.get("enrolled") else "You need to be at college."

def _worker(state, age, career):
    return None if career.get("job") else "You need a job."

def _money(n):
    return lambda state, age, career: None if state["money"] >= n else f"You need ${fmt(n)}."

DATING_APPS = [
    {"id": "crush",  "name": "Ask out a crush", "desc": "Someone at school catches your eye.", "min": 13, "max": 17, "cost": 0, "tone": (236, 130, 178)},
    {"id": "spark",  "name": "Spark",           "desc": "Swipe through locals. Free.", "min": 18, "cost": 0, "tone": (255, 149, 66)},
    {"id": "gold",   "name": "Spark Gold",      "desc": "Better looks and better matches.", "min": 18, "cost": 300, "tone": (230, 180, 60)},
    {"id": "campus", "name": "Campus Match",    "desc": "Other students near you.", "min": 18, "max": 35, "cost": 0, "need": _student, "tone": (90, 140, 230)},
    {"id": "office", "name": "Office romance",  "desc": "A spark with a coworker.", "min": 18, "cost": 0, "need": _worker, "tone": (120, 120, 150)},
    {"id": "night",  "name": "Night out",       "desc": "Meet someone at a bar. $60.", "min": 18, "cost": 60, "tone": (160, 100, 220)},
    {"id": "velvet", "name": "Velvet",          "desc": "Invite-only. High earners.", "min": 21, "cost": 2500, "need": _rich, "tone": (60, 50, 90)},
    {"id": "stardust", "name": "Stardust",      "desc": "Only for famous people.", "min": 18, "cost": 5000, "need": _famous, "tone": (200, 90, 200)},
    {"id": "matchmaker", "name": "Matchmaker",  "desc": "A pro finds your best fit.", "min": 25, "cost": 12000, "need": _money(12000), "tone": (76, 175, 120)},
]
APP_BY_ID = {a["id"]: a for a in DATING_APPS}

SOCIAL_APPS = [
    {"id": "chirp",  "name": "Chirp",    "desc": "Short posts and hot takes", "min": 13, "stat": "social", "tone": (80, 170, 230)},
    {"id": "snap",   "name": "Snapshot", "desc": "Photos and stories", "min": 13, "stat": "looks", "tone": (240, 200, 60)},
    {"id": "reel",   "name": "ReelTok",  "desc": "Short videos", "min": 13, "stat": "social", "tone": (230, 90, 130)},
    {"id": "linked", "name": "LinkedUp", "desc": "Careers and contacts", "min": 16, "stat": "academic", "tone": (60, 110, 180)},
    {"id": "stream", "name": "Streamly", "desc": "Live streams", "min": 16, "stat": "athletic", "tone": (140, 90, 220)},
]
SOCIAL_BY_ID = {a["id"]: a for a in SOCIAL_APPS}

def ensure(state):
    state.setdefault("love", [])
    state.setdefault("social", {})

# ---- layout ---------------------------------------------------------------------
def view_rects(rect):
    out, x = {}, rect.right
    for key, _, w in reversed(VIEWS):
        x -= w
        out[key] = pygame.Rect(x, rect.y - 2, w, 24)
        x -= 4
    return out

def _chip(screen, r, label, mouse_pos, enabled=True, primary=False):
    hov = enabled and r.collidepoint(mouse_pos)
    fill = LIGHT_GREY if not enabled else (ACCENT if (hov or primary) else WHITE)
    draw_rounded_rect(screen, fill, r, radius=8)
    pygame.draw.rect(screen, OUTLINE, r, 1, border_radius=8)
    draw_text(screen, label, small_font, INK if enabled else DARK_GREY, r.centerx, r.centery, centre=True)

def stage_colour(stage):
    return {"Talking": (90, 140, 230), "Seeing": (220, 90, 140), "Ready": (76, 175, 120)}.get(stage, (140, 140, 160))

# ---- drawing --------------------------------------------------------------------
def draw_love_tab(screen, rect, mouse_pos, state, age, career, partner):
    ensure(state)
    view = state.setdefault("love_view", "matches")
    views = view_rects(rect)
    for key, label, _ in VIEWS:
        vr = views[key]
        on = view == key
        draw_rounded_rect(screen, ACCENT if on else (WHITE if not vr.collidepoint(mouse_pos) else (235, 235, 240)), vr, radius=8)
        pygame.draw.rect(screen, OUTLINE, vr, 2, border_radius=8)
        draw_text(screen, label, small_font, INK, vr.centerx, vr.centery, centre=True)
    left = state["actions_remaining"]
    b = {"views": views, "rows": [], "apps": [], "social": []}
    if view == "matches":
        _draw_matches(screen, rect, mouse_pos, state, age, partner, b, left)
    elif view == "apps":
        _draw_apps(screen, rect, mouse_pos, state, age, career, b, left)
    else:
        _draw_social(screen, rect, mouse_pos, state, age, career, b, left)
    return b

def _draw_matches(screen, rect, mouse_pos, state, age, partner, b, left):
    love = state["love"]
    draw_text(screen, f"Matches ({len(love)}/{MAX_MATCHES})   {left} actions left", font, INK, rect.x, rect.y)
    if partner:
        status = "situationship" if partner.get("status") == "situationship" else "partner"
        note = f"Your {status} is {partner['name']}. Seeing others behind their back is cheating."
        draw_text(screen, note, small_font, (180, 80, 80) if love else MUTED, rect.x, rect.y + 24)
    if not love:
        txt = ("You're not talking to anyone. Open Dating apps to meet someone." if age >= 18 else
               "No crushes yet. Ask someone out from the Dating apps tab." if age >= 13 else
               "Romance starts at 13.")
        draw_text(screen, txt, small_font, MUTED, rect.x, rect.y + 56)
        return
    y = rect.y + 46
    for p in love[:MAX_MATCHES]:
        row = pygame.Rect(rect.x, y, rect.width, 50)
        draw_rounded_rect(screen, (252, 250, 254), row, radius=10)
        pygame.draw.rect(screen, (225, 220, 238), row, 1, border_radius=10)
        av = pygame.Rect(row.x + 6, row.y + 4, 36, 42)
        draw_person_avatar(screen, av, p)
        draw_text(screen, p["name"], small_font, INK, row.x + 50, row.y + 4)
        ready = p.get("stage") == "Seeing" and p.get("spark", 40) >= 70
        stage = "Ready" if ready else p.get("stage", "Talking")
        sc = stage_colour(stage)
        chip = pygame.Rect(row.x + 50 + small_font.size(p["name"])[0] + 8, row.y + 5, 62, 16)
        draw_rounded_rect(screen, sc, chip, radius=8)
        draw_text(screen, stage if stage != "Ready" else "Seeing", small_font, WHITE, chip.centerx, chip.centery - 1, centre=True)
        sub = f"{p.get('age', '?')}, {occupation(p)}"
        draw_text(screen, sub[:30], small_font, DARK_GREY, row.x + 50, row.y + 28)
        bar = pygame.Rect(row.x + 218, row.y + 18, 70, 8)
        draw_rounded_rect(screen, LIGHT_GREY, bar, radius=4)
        draw_rounded_rect(screen, (230, 100, 140), (bar.x, bar.y, int(bar.w * p.get("spark", 40) / 100), bar.h), radius=4)
        draw_text(screen, "Spark", small_font, MUTED, bar.x, row.y + 3)
        btns = {}
        bx = row.x + 300
        for key, label, w in (("text", "Text", 50), ("date", "Date $" + str(date_cost(p)), 76), ("official", "Official", 62), ("drop", "Drop", 48)):
            r = pygame.Rect(bx, row.y + 10, w, 30)
            if key == "official":
                en = left > 0
            elif key == "drop":
                en = True
            else:
                en = left > 0 and (key != "date" or state["money"] >= date_cost(p))
            _chip(screen, r, label, mouse_pos, en, primary=(key == "official" and ready))
            btns[key] = r
            bx += w + 5
        b["rows"].append((p, btns))
        y += 54

def date_cost(p):
    return 40 + (max(0, (p.get("fin") or {}).get("pay", 0)) // 1500 if p.get("age", 30) >= 18 else 0) // 2 * 2

def _app_reason(app, state, age, career):
    if age < app["min"]:
        return f"Age {app['min']}+"
    if app.get("max") and age > app["max"]:
        return "Too old for this one."
    if len(state["love"]) >= MAX_MATCHES:
        return "Your matches are full. Drop someone."
    if app.get("need"):
        r = app["need"](state, age, career)
        if r:
            return r
    if app["cost"] and state["money"] < app["cost"]:
        return f"Needs ${fmt(app['cost'])}."
    if state["actions_remaining"] <= 0:
        return "No actions left."
    return None

def _draw_apps(screen, rect, mouse_pos, state, age, career, b, left):
    draw_text(screen, f"Dating apps   {left} actions left", font, INK, rect.x, rect.y)
    cols, row_h = 2, 46
    col_w = (rect.width - 12) // cols
    shown = [a for a in DATING_APPS if a["min"] <= age + 4 and (not a.get("max") or age <= a["max"] + 6)]
    for n, a in enumerate(shown):
        col, row = n % cols, n // cols
        r = pygame.Rect(rect.x + col * (col_w + 12), rect.y + 30 + row * (row_h + 5), col_w, row_h)
        reason = _app_reason(a, state, age, career)
        hov = r.collidepoint(mouse_pos) and reason is None
        draw_rounded_rect(screen, ACCENT if hov else (WHITE if reason is None else LIGHT_GREY), r, radius=10)
        pygame.draw.rect(screen, OUTLINE, r, 1, border_radius=10)
        pygame.draw.circle(screen, a["tone"], (r.x + 22, r.centery), 14)
        draw_text(screen, a["name"][0], small_font, WHITE, r.x + 22, r.centery, centre=True)
        draw_text(screen, a["name"], small_font, INK, r.x + 44, r.y + 5)
        sub = reason or a["desc"]
        txt = sub
        while small_font.size(txt)[0] > col_w - 54 and len(txt) > 6:
            txt = txt[:-2]
        draw_text(screen, txt, small_font, RED if reason else DARK_GREY, r.x + 44, r.y + 25)
        lab = "Free" if not a["cost"] else f"${fmt(a['cost'])}"
        draw_text(screen, lab, small_font, GREEN if not a["cost"] else INK, r.right - 10 - small_font.size(lab)[0], r.y + 5)
        b["apps"].append((a, r))
    if age < 13:
        draw_text(screen, "Romance starts at 13.", small_font, MUTED, rect.x, rect.y + 40)

def _draw_social(screen, rect, mouse_pos, state, age, career, b, left):
    soc = state["social"]
    total = sum(soc.values())
    draw_text(screen, f"Social media   {left} actions left", font, INK, rect.x, rect.y)
    draw_text(screen, f"{fmt(total)} followers in all", small_font, MUTED, rect.right - 160, rect.y + 30)
    cols, row_h = 2, 46
    col_w = (rect.width - 12) // cols
    shown = [a for a in SOCIAL_APPS if a["min"] <= age]
    if not shown:
        draw_text(screen, "Social media opens at 13.", small_font, MUTED, rect.x, rect.y + 40)
    for n, a in enumerate(shown):
        col, row = n % cols, n // cols
        r = pygame.Rect(rect.x + col * (col_w + 12), rect.y + 30 + row * (row_h + 5), col_w, row_h)
        can = left > 0
        hov = r.collidepoint(mouse_pos) and can
        draw_rounded_rect(screen, ACCENT if hov else (WHITE if can else LIGHT_GREY), r, radius=10)
        pygame.draw.rect(screen, OUTLINE, r, 1, border_radius=10)
        pygame.draw.circle(screen, a["tone"], (r.x + 22, r.centery), 14)
        draw_text(screen, a["name"][0], small_font, WHITE, r.x + 22, r.centery, centre=True)
        draw_text(screen, a["name"], small_font, INK, r.x + 44, r.y + 5)
        draw_text(screen, a["desc"], small_font, DARK_GREY, r.x + 44, r.y + 25)
        fol = f"{fmt(soc.get(a['id'], 0))} followers"
        draw_text(screen, fol, small_font, INK, r.right - 10 - small_font.size(fol)[0], r.y + 5)
        draw_text(screen, "Post", small_font, MUTED, r.right - 10 - small_font.size("Post")[0], r.y + 25)
        b["social"].append((a, r))
    if total >= 10000:
        income = int(total * 0.015)
        draw_text(screen, f"Sponsors pay you about ${fmt(income)} a year.", small_font, GREEN, rect.x, rect.bottom - 22)

# ---- actions --------------------------------------------------------------------
def _boost(p, stats=0, compat=0):
    for k in ("looks", "social"):
        p["stats"][k] = min(100, p["stats"][k] + stats)
    p["compat"] = min(100, p.get("compat", 50) + compat)

def make_app_prospect(app_id, state, age, career):
    """Builds the person an app serves up."""
    traits = state.get("player_traits", [])
    p = make_prospect(state, age, traits, "Match", "partner")
    if app_id == "crush":
        p["age"] = max(13, min(17, near_age(age)))
        p["job_title"] = "Student"
    elif app_id == "gold":
        _boost(p, 10, 12)
    elif app_id == "campus":
        p["job_title"] = "Student"
        p["fin"] = {"pay": 0, "savings": random.randint(0, 3000), "debt": random.randint(0, 20000)}
    elif app_id == "office":
        job = career.get("job") or {}
        worldjobs.assign_job(p, worldjobs.coworker_job(job.get("base") or job.get("title", "Manager")))
        p["relation"] = "Coworker"
    elif app_id == "night":
        _boost(p, 5, 0)
    elif app_id == "velvet":
        worldjobs.assign_job(p, worldjobs.BY_TITLE[random.choice(RICH_JOBS)])
        _boost(p, 12, 8)
    elif app_id == "stardust":
        worldjobs.assign_job(p, worldjobs.BY_TITLE[random.choice(CELEB_JOBS)])
        _boost(p, 18, 6)
        p["famous"] = True
    elif app_id == "matchmaker":
        _boost(p, 8, 30)
        p["compat"] = max(p["compat"], 80)
    p["relation"] = p.get("relation") if p.get("relation") == "Coworker" else "Match"
    return p

def handle_love_click(mx, my, buttons, state, age, career, partner, friends, log):
    """Returns None, or a tuple for main.py to act on:
    ("prospect", person) opens the ask-out card; ("official", person) makes
    them your partner."""
    ensure(state)
    for key, vr in buttons.get("views", {}).items():
        if vr.collidepoint(mx, my):
            state["love_view"] = key
            return None
    stats = state["stats"]
    for p, btns in buttons.get("rows", []):
        for key, r in btns.items():
            if not r.collidepoint(mx, my):
                continue
            if key == "drop":
                state["love"].remove(p)
                log(f"You let things go with {p['name']}.")
                return None
            if state["actions_remaining"] <= 0:
                return None
            if key == "official":
                if p.get("stage") != "Seeing" and random.random() < 0.5:
                    state["actions_remaining"] -= 1
                    log(f"{p['name']} says it's too soon to be official. Keep seeing each other.")
                    return None
                return ("official", p)
            state["actions_remaining"] -= 1
            p["touched"] = True
            if key == "text":
                p["spark"] = min(100, p.get("spark", 40) + random.randint(4, 9))
                p["closeness"] = min(100, p["closeness"] + 2)
                p["texts"] = p.get("texts", 0) + 1
                if p.get("stage") == "Talking" and p["texts"] >= 3 and p["spark"] >= 55:
                    p["stage"] = "Seeing"
                    log(f"You and {p['name']} are seeing each other now.")
                else:
                    log(random.choice([f"You and {p['name']} texted all evening.", f"{p['name']} sent you a meme. You laughed.", f"A long call with {p['name']}."]))
            else:
                cost = date_cost(p)
                if state["money"] < cost:
                    state["actions_remaining"] += 1
                    return None
                state["money"] -= cost
                match = (p.get("compat", 50) - 50) / 100
                gain = random.randint(6, 14) + int(match * 12)
                p["spark"] = max(0, min(100, p.get("spark", 40) + gain))
                p["closeness"] = min(100, p["closeness"] + 5)
                p["trust"] = min(100, p.get("trust", 40) + 3)
                p["dates"] = p.get("dates", 0) + 1
                stats["mental"] = min(100, stats["mental"] + 1)
                if p.get("stage") == "Talking" and p["dates"] >= 1:
                    p["stage"] = "Seeing"
                log(f"A date with {p['name']} went {'wonderfully' if gain >= 14 else 'well' if gain >= 8 else 'okay'}.")
            return None
    for a, r in buttons.get("apps", []):
        if not r.collidepoint(mx, my):
            continue
        reason = _app_reason(a, state, age, career)
        if reason:
            log(reason)
            return None
        state["actions_remaining"] -= 1
        state["money"] -= a["cost"]
        p = make_app_prospect(a["id"], state, age, career)
        return ("prospect", p)
    for a, r in buttons.get("social", []):
        if not r.collidepoint(mx, my):
            continue
        if state["actions_remaining"] <= 0:
            return None
        return social_post(a, state, age, career, log)
    return None

def add_match(state, p, casual=False, log=None):
    ensure(state)
    p["category"], p["relation"] = "partner", "Match"
    p["stage"] = "Seeing" if casual else "Talking"
    p["spark"] = 52 if casual else 42
    p["texts"] = 0
    p["dates"] = 0
    p["romance"] = max(p.get("romance", 0), 35)
    state["love"].append(p)

def social_post(app, state, age, career, log):
    """Posting costs an action and grows your following."""
    stats = state["stats"]
    soc = state["social"]
    fol = soc.get(app["id"], 0)
    state["actions_remaining"] -= 1
    quality = stats[app["stat"]] + stats["looks"] * 0.2 + career.get("fame", 0) * 0.5
    gain = int((20 + quality * 1.5) * (1 + fol / 4000) * random.uniform(0.6, 1.5))
    note = f"You posted on {app['name']} and gained {fmt(gain)} followers."
    r = random.random()
    if r < 0.07:
        gain *= 8
        note = f"Your {app['name']} post went viral! +{fmt(gain)} followers."
        stats["social"] = min(100, stats["social"] + 2)
    elif r < 0.11 and fol > 500:
        gain = -max(5, fol // 12)
        note = f"A post on {app['name']} backfired. You lost {fmt(-gain)} followers."
        stats["mental"] = max(0, stats["mental"] - 3)
    soc[app["id"]] = max(0, fol + gain)
    stats["mental"] = max(0, min(100, stats["mental"] + (0 if gain >= 0 else 0)))
    if app["id"] == "snap" and gain > 0:
        stats["looks"] = min(100, stats["looks"] + (1 if random.random() < 0.3 else 0))
    if app["id"] == "linked" and career.get("job"):
        career["job"]["perf"] = min(100, career["job"].get("perf", 55) + 3)
        note += " Your boss noticed."
    total = sum(soc.values())
    career["fame"] = max(career.get("fame", 0), min(60, total // 4000))
    log(note)
    if age >= 16 and len(state["love"]) < MAX_MATCHES and random.random() < 0.18 and gain > 0:
        return ("dm", None)
    return None

def love_year(state, age, partner, friends, career, log):
    """Year end: matches age, cool off if you ignore them, and anything
    behind your partner's back may come out. Social income arrives."""
    ensure(state)
    stats = state["stats"]
    for p in list(state["love"]):
        p["age"] = p.get("age", 25) + 1
        if p.pop("touched", False):
            p["spark"] = min(100, p.get("spark", 40) + 2)
        else:
            p["spark"] = p.get("spark", 40) - 14
        p["texts"] = 0
        if p["spark"] <= 8:
            state["love"].remove(p)
            log(f"{p['name']} stopped replying. That one faded out.")
            continue
        if p.get("stage") == "Seeing" and p["spark"] >= 75 and not p.get("asked"):
            p["asked"] = True
            log(f"{p['name']} hinted they'd like to make it official.")
    if partner and state["love"]:
        for p in list(state["love"]):
            risk = 0.12 if p.get("stage") == "Talking" else 0.3
            if random.random() < risk:
                partner["trust"] = max(0, partner.get("trust", 50) - 25)
                partner["conflict"] = min(100, partner.get("conflict", 0) + 30)
                partner["cheated"] = True
                log(f"{partner['name']} found out you were talking to {p['name']}. They are furious.")
                stats["mental"] = max(0, stats["mental"] - 4)
                import romance as _r
                if partner["trust"] < 20 or partner["conflict"] >= 70:
                    _r.they_end_it(partner, friends, state, log, "they found out about the others")
                    return None
                break
    soc = state["social"]
    if soc:
        for k in soc:
            soc[k] = int(soc[k] * random.uniform(0.96, 1.05))
        total = sum(soc.values())
        if total >= 10000:
            income = int(total * 0.015)
            state["money"] += income
            log(f"Sponsors paid you ${fmt(income)} for your {fmt(total)} followers.")
    return partner
