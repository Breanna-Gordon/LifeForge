"""Running businesses: film studio, tech startup, construction firm and more.

Every business type has its own way of making money, and you choose how to
run it: hands-on (you work in it), with a manager (steady, smaller profit),
as a franchise (more branches) or float it on the stock market (big payout).
You can own up to three at once."""
import random
import pygame
from constants import fmt, OUTLINE, INK, MUTED
from constants import (WHITE, LIGHT_GREY, DARK_GREY, ACCENT, GREEN, RED,
                       font, small_font, draw_text, draw_rounded_rect)

MAX_BIZ = 3

# id, name, set-up cost, key stat, risk (0-1), min age, margin, blurb, extra needs
TYPES = [
    {"id": "foodtruck",  "name": "Food Truck",         "cost": 20000,  "stat": "social",   "risk": 0.30, "margin": 0.20, "min": 18, "blurb": "Cheap start, small steady profits."},
    {"id": "restaurant", "name": "Restaurant",         "cost": 80000,  "stat": "social",   "risk": 0.35, "margin": 0.16, "min": 21, "blurb": "Reputation is everything."},
    {"id": "shop",       "name": "Boutique Shop",      "cost": 35000,  "stat": "looks",    "risk": 0.28, "margin": 0.18, "min": 18, "blurb": "Clothes, beauty, jewellery."},
    {"id": "gym",        "name": "Gym",                "cost": 60000,  "stat": "athletic", "risk": 0.25, "margin": 0.17, "min": 21, "blurb": "Memberships bring in cash all year."},
    {"id": "construct",  "name": "Construction Firm",  "cost": 150000, "stat": "athletic", "risk": 0.25, "margin": 0.14, "min": 24, "blurb": "Big contracts, big machines, steady work.", "needs": ("athletic", 45)},
    {"id": "realty",     "name": "Real Estate Agency", "cost": 90000,  "stat": "social",   "risk": 0.32, "margin": 0.18, "min": 24, "blurb": "Commission on every sale."},
    {"id": "tech",       "name": "Tech Startup",       "cost": 50000,  "stat": "academic", "risk": 0.65, "margin": 0.30, "min": 20, "blurb": "Could flop. Could be worth millions.", "needs": ("academic", 55), "ipo": True},
    {"id": "gamestudio", "name": "Game Studio",        "cost": 70000,  "stat": "academic", "risk": 0.55, "margin": 0.26, "min": 20, "blurb": "One hit can change everything.", "needs": ("academic", 50), "hits": True},
    {"id": "studio",     "name": "Film Studio",        "cost": 200000, "stat": "social",   "risk": 0.60, "margin": 0.28, "min": 26, "blurb": "Make films. Blockbusters or bombs.", "hits": True, "ipo": True},
    {"id": "label",      "name": "Record Label",       "cost": 120000, "stat": "social",   "risk": 0.50, "margin": 0.24, "min": 24, "blurb": "Sign artists, chase hit records.", "hits": True},
    {"id": "fashion",    "name": "Fashion House",      "cost": 110000, "stat": "looks",    "risk": 0.45, "margin": 0.24, "min": 24, "blurb": "Seasons, shows and celebrity clients.", "needs": ("looks", 55), "hits": True},
    {"id": "farm",       "name": "Farm",               "cost": 55000,  "stat": "athletic", "risk": 0.20, "margin": 0.12, "min": 21, "blurb": "Slow, safe and stable."},
    {"id": "robotics",   "name": "Robotics Lab",       "cost": 180000, "stat": "academic", "risk": 0.50, "margin": 0.27, "min": 26, "blurb": "Future money, if it works.", "needs": ("academic", 70), "ipo": True},
]
BY_ID = {t["id"]: t for t in TYPES}

STYLES = [("hands", "Hands-on", "You work in it. Best profits, costs Mental."),
          ("manager", "Manager", "Hire a manager. Steady, 15% lower profit."),
          ("franchise", "Franchise", "Open more branches. Needs 3 years and rep 55+.")]
STYLE_NAME = {k: n for k, n, _ in STYLES}

def ensure(state):
    state.setdefault("businesses", [])
    old = state.get("business")
    if old and not state.get("_biz_migrated"):
        t = BY_ID.get(old.get("industry"), BY_ID["foodtruck"])
        state["businesses"].append(new_biz(t, old.get("cost", t["cost"]), old.get("name")))
        state["businesses"][-1]["years"] = old.get("years", 0)
    state["_biz_migrated"] = True
    state["business"] = state["businesses"][0] if state["businesses"] else None

def new_biz(t, capital, name=None):
    return {"type": t["id"], "name": name or t["name"], "value": capital, "capital": capital, "run": "hands",
            "rep": 40, "staff": 2, "branches": 1, "years": 0, "profit": 0, "demand": random.randint(40, 70),
            "hit": 0, "equity": 100, "public": False}

def need_reason(t, state, age):
    if age < t["min"]:
        return f"Age {t['min']}+"
    if t.get("needs") and state["stats"][t["needs"][0]] < t["needs"][1]:
        return f"{t['needs'][0].title()} {t['needs'][1]}+"
    if state["money"] < t["cost"]:
        return f"${fmt(t['cost'])}"
    if len(state["businesses"]) >= MAX_BIZ:
        return "3 is the limit"
    if state["actions_remaining"] <= 0:
        return "No actions"
    return None

# ---- drawing ------------------------------------------------------------------
def _btn(screen, r, label, mouse_pos, en=True, primary=False):
    hov = en and r.collidepoint(mouse_pos)
    draw_rounded_rect(screen, LIGHT_GREY if not en else (ACCENT if (hov or primary) else WHITE), r, radius=8)
    pygame.draw.rect(screen, OUTLINE, r, 1, border_radius=8)
    draw_text(screen, label, small_font, INK if en else DARK_GREY, r.centerx, r.centery, centre=True)

def draw_business(screen, rect, mouse_pos, state, age):
    ensure(state)
    biz = state["businesses"]
    left = state["actions_remaining"]
    b = {"start": None, "picks": [], "rows": [], "back": None}
    draw_text(screen, f"Business  ({len(biz)}/{MAX_BIZ})", font, INK, rect.x, rect.y)
    if state.get("_biz_pick"):
        back = pygame.Rect(rect.x + 150, rect.y - 2, 86, 24)
        _btn(screen, back, "< Back", mouse_pos)
        b["back"] = back
        for n, t in enumerate(TYPES):
            col, row = n % 2, n // 2
            r = pygame.Rect(rect.x + col * 337, rect.y + 28 + row * 41, 331, 38)
            why = need_reason(t, state, age)
            hov = r.collidepoint(mouse_pos) and why is None
            draw_rounded_rect(screen, ACCENT if hov else (WHITE if why is None else LIGHT_GREY), r, radius=8)
            pygame.draw.rect(screen, OUTLINE, r, 1, border_radius=8)
            draw_text(screen, t["name"], small_font, INK, r.x + 8, r.y + 2)
            draw_text(screen, t["blurb"], small_font, DARK_GREY, r.x + 8, r.y + 19)
            lab = f"${fmt(t['cost'])}"
            draw_text(screen, lab, small_font, RED if (why and why.startswith("$")) else INK, r.right - 8 - small_font.size(lab)[0], r.y + 2)
            if why and not why.startswith("$"):
                draw_text(screen, why, small_font, RED, r.right - 8 - small_font.size(why)[0], r.y + 19)
            b["picks"].append((t, r))
        return b
    start = pygame.Rect(rect.x + 150, rect.y - 2, 136, 24)
    _btn(screen, start, "Start a business", mouse_pos, len(biz) < MAX_BIZ and age >= 18)
    b["start"] = start
    if not biz:
        draw_text(screen, f"You don't own a business. Start one to build a fortune (or lose one).   {left} actions left.", small_font, MUTED, rect.x, rect.y + 34)
        draw_text(screen, "Film studios, tech startups, construction firms and more, each run differently.", small_font, MUTED, rect.x, rect.y + 56)
        return b
    y = rect.y + 30
    for bz in biz:
        t = BY_ID[bz["type"]]
        row = pygame.Rect(rect.x, y, rect.width, 86)
        draw_rounded_rect(screen, (252, 250, 254), row, radius=10)
        pygame.draw.rect(screen, (225, 220, 238), row, 1, border_radius=10)
        draw_text(screen, bz["name"], font, INK, row.x + 10, row.y + 6)
        sub = f"{STYLE_NAME[bz['run']]}  ·  {bz['branches']} branch{'es' if bz['branches'] != 1 else ''}  ·  {bz['staff']} staff  ·  {bz['years']} yrs"
        if bz.get("public"):
            sub += "  ·  PUBLIC"
        draw_text(screen, sub, small_font, DARK_GREY, row.x + 10, row.y + 26)
        draw_text(screen, f"Worth ${fmt(bz['value'])}", small_font, INK, row.right - 190, row.y + 8)
        pr = bz.get("profit", 0)
        draw_text(screen, f"Last year {'+' if pr >= 0 else '-'}${fmt(abs(pr))}", small_font, GREEN if pr >= 0 else RED, row.right - 190, row.y + 28)
        for lab, v, x0, colr in (("Rep", bz["rep"], row.x + 10, (230, 180, 60)), ("Demand", bz["demand"], row.x + 170, (90, 140, 230))):
            draw_text(screen, lab, small_font, MUTED, x0, row.y + 42)
            bar = pygame.Rect(x0 + 64, row.y + 47, 70, 8)
            draw_rounded_rect(screen, LIGHT_GREY, bar, radius=4)
            draw_rounded_rect(screen, colr, (bar.x, bar.y, int(bar.w * v / 100), bar.h), radius=4)
        btns = {}
        bx = row.x + 10
        opts = [("mkt", f"Marketing ${fmt(max(500, bz['value'] // 20))}", 150), ("hire", "Hire staff", 80), ("style", "Run style", 78)]
        if t.get("hits"):
            opts.append(("launch", "Launch a hit", 92))
        if t.get("ipo") and bz["years"] >= 5 and bz["value"] >= 1000000 and not bz.get("public"):
            opts.append(("ipo", "Go public", 82))
        opts.append(("sell", "Sell", 52))
        for key, label, w in opts:
            r = pygame.Rect(bx, row.y + 58, w, 24)
            en = key == "sell" or left > 0
            _btn(screen, r, label, mouse_pos, en)
            btns[key] = r
            bx += w + 5
        b["rows"].append((bz, btns))
        y += 90
        if y + 86 > rect.bottom:
            break
    return b

# ---- clicks ---------------------------------------------------------------------
def handle_business_click(mx, my, b, state, age, log):
    ensure(state)
    stats = state["stats"]
    if b.get("back") and b["back"].collidepoint(mx, my):
        state["_biz_pick"] = False
        return
    if b.get("start") and b["start"].collidepoint(mx, my) and len(state["businesses"]) < MAX_BIZ:
        state["_biz_pick"] = True
        return
    for t, r in b.get("picks", []):
        if r.collidepoint(mx, my):
            why = need_reason(t, state, age)
            if why:
                log(f"Can't start a {t['name'].lower()}: {why}.")
                return
            state["actions_remaining"] -= 1
            state["money"] -= t["cost"]
            state["businesses"].append(new_biz(t, t["cost"]))
            state["business"] = state["businesses"][0]
            state["_biz_pick"] = False
            log(f"You opened a {t['name'].lower()}.")
            return
    for bz, btns in b.get("rows", []):
        for key, r in btns.items():
            if not r.collidepoint(mx, my):
                continue
            t = BY_ID[bz["type"]]
            if key == "sell":
                got = int(bz["value"] * (0.7 if not bz.get("public") else 0.9) * bz.get("equity", 100) / 100)
                state["money"] += got
                state["businesses"].remove(bz)
                state["business"] = state["businesses"][0] if state["businesses"] else None
                log(f"You sold {bz['name']} for ${fmt(got)}.")
                return
            if state["actions_remaining"] <= 0:
                return
            if key == "mkt":
                cost = max(500, bz["value"] // 20)
                if state["money"] < cost:
                    return
                state["money"] -= cost
                state["actions_remaining"] -= 1
                bz["rep"] = min(100, bz["rep"] + random.randint(4, 10))
                bz["demand"] = min(100, bz["demand"] + random.randint(2, 8))
                log(f"A marketing push for {bz['name']}.")
            elif key == "hire":
                cost = 3000 + bz["staff"] * 800
                if state["money"] < cost:
                    return
                state["money"] -= cost
                state["actions_remaining"] -= 1
                bz["staff"] += 1
                bz["value"] = int(bz["value"] * 1.04)
                log(f"{bz['name']} hired another person.")
            elif key == "style":
                state["actions_remaining"] -= 1
                order = [s[0] for s in STYLES]
                nxt = order[(order.index(bz["run"]) + 1) % 3]
                if nxt == "franchise" and (bz["years"] < 3 or bz["rep"] < 55):
                    nxt = "hands"
                bz["run"] = nxt
                log(f"{bz['name']} is now run: {STYLE_NAME[nxt].lower()}.")
            elif key == "launch":
                cost = max(2000, bz["value"] // 10)
                if state["money"] < cost:
                    return
                state["money"] -= cost
                state["actions_remaining"] -= 1
                roll = random.random() + (stats[t["stat"]] - 50) / 300 + (bz["rep"] - 50) / 400
                if roll > 0.72:
                    bz["hit"] = 2
                    bz["value"] = int(bz["value"] * 1.25)
                    log(f"{bz['name']} had a smash hit!")
                elif roll > 0.35:
                    bz["value"] = int(bz["value"] * 1.08)
                    log(f"{bz['name']} released something decent.")
                else:
                    bz["value"] = int(bz["value"] * 0.9)
                    log(f"{bz['name']}'s big launch flopped.")
            elif key == "ipo":
                payout = int(bz["value"] * 0.35)
                bz["equity"] = 65
                bz["public"] = True
                bz["value"] = int(bz["value"] * 1.2)
                state["money"] += payout
                state["actions_remaining"] -= 1
                log(f"{bz['name']} went public! You raised ${fmt(payout)} for 35% of the company.")
            return

# ---- yearly ---------------------------------------------------------------------
def business_year(state, age, career, log):
    ensure(state)
    stats = state["stats"]
    if state.get("jail"):
        return
    for bz in list(state["businesses"]):
        t = BY_ID[bz["type"]]
        bz["years"] += 1
        bz["demand"] = max(10, min(95, bz["demand"] + random.randint(-12, 12)))
        skill = stats[t["stat"]] / 100
        style = bz["run"]
        revenue = 0.55 * bz["value"] * t["margin"] * (0.4 + bz["demand"] / 100 + bz["rep"] / 200 + skill * 0.6)
        revenue *= 1 + 0.09 * (bz["branches"] - 1) + 0.03 * bz["staff"]
        costs = bz["value"] * 0.12 + bz["staff"] * 2600
        if style == "manager":
            costs += revenue * 0.15
        if style == "hands":
            revenue *= 1.1
            stats["mental"] = max(0, stats["mental"] - 2)
        if style == "franchise":
            if bz["years"] >= 3 and bz["rep"] >= 55 and random.random() < 0.55:
                bz["branches"] += 1
                bz["value"] = int(bz["value"] * 1.12)
                log(f"{bz['name']} opened branch number {bz['branches']}.")
            costs += bz["branches"] * 6000
        swing = random.gauss(0, bz["value"] * t["risk"] * 0.18)
        if bz.get("hit"):
            revenue *= 1.6
            bz["hit"] -= 1
        profit = int(revenue - costs + swing)
        if t["risk"] >= 0.5 and random.random() < 0.06:
            profit -= int(bz["value"] * 0.25)
            log(f"{bz['name']} was hit by a setback (a lawsuit, a delay).")
        bz["profit"] = profit
        mine = int(profit * bz.get("equity", 100) / 100)
        state["money"] += mine
        bz["value"] = max(5000, int(bz["value"] * (1 + profit / max(1, bz["value"]) * 0.25)))
        bz["rep"] = max(0, min(100, bz["rep"] + random.randint(-4, 5)))
        if state["money"] < 0:
            state["debt"] = state.get("debt", 0) - state["money"]
            state["money"] = 0
        log(f"{bz['name']} {'made' if mine >= 0 else 'lost'} ${fmt(abs(mine))} this year.")
        if bz["value"] <= 6000 and bz["profit"] < 0 and random.random() < 0.5:
            state["businesses"].remove(bz)
            log(f"{bz['name']} went bust.")
    state["business"] = state["businesses"][0] if state["businesses"] else None
