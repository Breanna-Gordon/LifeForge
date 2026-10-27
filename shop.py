from constants import OUTLINE, INK, MUTED, draw_card, draw_pill, draw_shadow
import pygame
from constants import (WHITE, BLACK, LIGHT_GREY, DARK_GREY, ACCENT, GREEN,
                       font, small_font, draw_text, draw_rounded_rect)

# once_a_year items are treats you can buy again every year; permanent items
# are bought once and then give a small boost every year you own them.
ITEMS = [
    {"id": "heirloom", "name": "Family keepsake", "cost": 0, "min": 0, "max": 0, "perm": True, "hidden": True, "fx": {"mental": 1}, "note": "+1 Mental a year"},
    {"id": "treat",  "name": "Treat yourself", "cost": 10,  "min": 3,  "max": 99, "fx": {"mental": 2}},
    {"id": "toy",    "name": "New toy",        "cost": 15,  "min": 2,  "max": 12, "fx": {"mental": 2, "social": 1}},
    {"id": "trip",   "name": "Day trip",       "cost": 25,  "min": 6,  "max": 99, "fx": {"social": 2, "mental": 2}},
    {"id": "gym",    "name": "Gym membership", "cost": 40,  "min": 14, "max": 99, "fx": {"physical": 3, "athletic": 3, "looks": 1}},
    {"id": "night",  "name": "Night out",      "cost": 30,  "min": 18, "max": 99, "fx": {"social": 3, "mental": 1}},
    {"id": "check",  "name": "Health check-up","cost": 50,  "min": 18, "max": 99, "fx": {"physical": 3}},
    {"id": "course", "name": "Online course",  "cost": 60,  "min": 12, "max": 99, "fx": {"academic": 4}},
    {"id": "holiday","name": "Holiday",        "cost": 120, "min": 6,  "max": 99, "fx": {"mental": 5, "social": 2, "physical": 1}},
    {"id": "hair",   "name": "New haircut",    "cost": 20,  "min": 10, "max": 99, "fx": {"looks": 3}},
    {"id": "outfit", "name": "New outfit",     "cost": 40,  "min": 10, "max": 99, "fx": {"looks": 3, "social": 1}},
    {"id": "skin",   "name": "Skincare",       "cost": 25,  "min": 13, "max": 99, "fx": {"looks": 2}},
    {"id": "bike",   "name": "Bike",           "cost": 80,  "min": 8,  "max": 99, "perm": True, "fx": {"physical": 1, "athletic": 1}, "note": "+1 Health and Athletic a year"},
    {"id": "laptop", "name": "Laptop",         "cost": 200, "min": 12, "max": 99, "perm": True, "fx": {"academic": 1}, "note": "+1 Academic a year"},
    {"id": "dog",    "name": "Dog",            "cost": 150, "min": 8,  "max": 99, "perm": True, "fx": {"social": 1, "mental": 1}, "note": "+1 Social and Mental a year"},
    {"id": "licence","name": "Driving lessons","cost": 40,  "min": 17, "max": 99, "perm": True, "fx": {}, "note": "Get your driving licence"},
    {"id": "car",    "name": "Car",            "cost": 180, "min": 17, "max": 99, "perm": True, "needs": "licence", "fx": {"social": 1}, "note": "Needs a licence. +5% pay, +1 Social a year"},
    {"id": "flat",   "name": "Buy a flat",     "cost": 220, "min": 18, "max": 99, "perm": True, "home": 220, "fx": {}, "note": "No more rent. Value grows"},
    {"id": "house",  "name": "Buy a house",    "cost": 520, "min": 21, "max": 99, "perm": True, "home": 520, "fx": {}, "note": "No more rent. Value grows"},
    {"id": "guitar", "name": "Guitar",         "cost": 90,  "min": 10, "max": 99, "perm": True, "fx": {"mental": 1}, "note": "+1 Mental a year"},
]

def available(age):
    return [i for i in ITEMS if i["min"] <= age <= i["max"] and not i.get("hidden")]

BANK_BUTTONS = [
    ("dep50", "Deposit $50 (3% a year)"), ("wd50", "Withdraw $50"),
    ("loan100", "Take a $100 loan"), ("loan300", "Take a $300 loan"),
    ("rep50", "Repay $50"), ("repall", "Repay as much as possible"),
    ("inv50", "Invest $50 (risky)"), ("invout", "Cash out investments"),
    ("sellhome", "Sell your home"),
]

def draw_shop_tab(screen, rect, mouse_pos, state, age):
    view = state.setdefault("shop_view", "shop")
    views = {"shop": pygame.Rect(rect.right - 230, rect.y - 2, 100, 24), "bank": pygame.Rect(rect.right - 124, rect.y - 2, 124, 24)}
    for key, label in (("shop", "Shop"), ("bank", "Bank")):
        vr = views[key]
        draw_rounded_rect(screen, ACCENT if view == key else (WHITE if not vr.collidepoint(mouse_pos) else (235, 235, 240)), vr, radius=8)
        pygame.draw.rect(screen, OUTLINE, vr, 2, border_radius=8)
        draw_text(screen, label, small_font, INK, vr.centerx, vr.centery, centre=True)
    if view == "bank":
        debt, sv = state.get("debt", 0), state.get("savings", 0)
        draw_text(screen, "Bank", font, INK, rect.x, rect.y)
        draw_text(screen, f"Cash ${state['money']}   Savings ${sv} (+3%)   Invested ${state.get('invest', 0)}   Debt ${debt} (+5%)",
                  small_font, DARK_GREY, rect.x, rect.y + 28)
        draw_text(screen, "Debt is repaid automatically from your wages. Loans are for ages 18+ (up to $600 total).",
                  small_font, DARK_GREY, rect.x, rect.y + 48)
        cols = 2
        col_w = (rect.width - 12) // cols
        hits = []
        for n, (key, label) in enumerate(BANK_BUTTONS):
            r = pygame.Rect(rect.x + (n % cols) * (col_w + 12), rect.y + 70 + (n // cols) * 40, col_w, 34)
            ok = _bank_ok(key, state, age)
            draw_rounded_rect(screen, ACCENT if (ok and r.collidepoint(mouse_pos)) else (WHITE if ok else LIGHT_GREY), r, radius=8)
            pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
            draw_text(screen, label, small_font, INK, r.centerx, r.centery, centre=True)
            hits.append((key, r))
        return {"items": [], "views": views, "bank": hits}
    all_items = available(age)
    per_page = 12
    pages = max(1, -(-len(all_items) // per_page))
    page = max(0, min(state.get("shop_page", 0), pages - 1))
    state["shop_page"] = page
    items = all_items[page * per_page:(page + 1) * per_page]
    if pages > 1:
        views["prev"] = pygame.Rect(rect.right - 340, rect.y - 2, 28, 24)
        views["next"] = pygame.Rect(rect.right - 306, rect.y - 2, 28, 24)
        for key, lab in (("prev", "<"), ("next", ">")):
            draw_rounded_rect(screen, WHITE if not views[key].collidepoint(mouse_pos) else (255, 236, 218), views[key], radius=8)
            pygame.draw.rect(screen, OUTLINE, views[key], 1, border_radius=8)
            draw_text(screen, lab, small_font, INK, views[key].centerx, views[key].centery, centre=True)
    owned, bought = state["owned"], state["bought_this_year"]
    draw_text(screen, f"Shop: ${state['money']}" + (f"  (page {page + 1}/{pages})" if pages > 1 else ""), font, INK, rect.x, rect.y)
    cols, row_h = 2, 36
    col_w = (rect.width - 12) // cols
    hits = []
    for n, it in enumerate(items):
        col, row = n % cols, n // cols
        r = pygame.Rect(rect.x + col * (col_w + 12), rect.y + 28 + row * (row_h + 3), col_w, row_h)
        have = it["id"] in owned if it.get("perm") else it["id"] in bought
        can = (not have) and state["money"] >= it["cost"] and (not it.get("needs") or it["needs"] in owned) \
              and not (it.get("home") and state.get("home"))
        hovered = r.collidepoint(mouse_pos) and can
        fill = ACCENT if hovered else (LIGHT_GREY if not can else WHITE)
        draw_rounded_rect(screen, fill, r, radius=8)
        pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
        draw_text(screen, it["name"], small_font, INK, r.x + 10, r.y + 2)
        sub = it.get("note") or ", ".join(f"{k.title()} +{v}" for k, v in it["fx"].items())
        draw_text(screen, sub, small_font, DARK_GREY, r.x + 10, r.y + 18)
        label = "Owned" if (have and it.get("perm")) else ("Bought" if have else f"${it['cost']}")
        draw_text(screen, label, small_font, GREEN if have else BLACK, r.right - 10 - small_font.size(label)[0], r.y + 10)
        hits.append((it, r))
    return {"items": hits, "views": views, "bank": []}

def _bank_ok(key, state, age):
    m, sv, d = state["money"], state.get("savings", 0), state.get("debt", 0)
    return {"inv50": age >= 18 and m >= 50, "invout": state.get("invest", 0) > 0, "sellhome": bool(state.get("home")),
            "dep50": m >= 50, "wd50": sv >= 50, "loan100": age >= 18 and d + 100 <= 600,
            "loan300": age >= 18 and d + 300 <= 600, "rep50": d > 0 and m > 0, "repall": d > 0 and m > 0}[key]

def handle_shop_click(mx, my, buttons, state, age, log):
    for key, vr in buttons.get("views", {}).items():
        if vr.collidepoint(mx, my):
            if key in ("prev", "next"):
                state["shop_page"] = max(0, state.get("shop_page", 0) + (1 if key == "next" else -1))
            else:
                state["shop_view"] = key
            return
    for key, r in buttons.get("bank", []):
        if not r.collidepoint(mx, my) or not _bank_ok(key, state, age):
            continue
        if key == "dep50":
            state["money"] -= 50; state["savings"] = state.get("savings", 0) + 50
        elif key == "wd50":
            state["money"] += 50; state["savings"] -= 50
        elif key == "inv50":
            state["money"] -= 50; state["invest"] = state.get("invest", 0) + 50
            log("Invested $50. Returns vary a lot from year to year.")
        elif key == "invout":
            state["money"] += state["invest"]; log(f"Cashed out ${state['invest']} of investments."); state["invest"] = 0
        elif key == "sellhome":
            h = state["home"]; state["money"] += h["value"]; state["home"] = None
            state["owned"].discard("flat"); state["owned"].discard("house")
            log(f"Sold {h['name']} for ${h['value']}. You pay rent again.")
        elif key.startswith("loan"):
            amt = int(key[4:]); state["money"] += amt; state["debt"] = state.get("debt", 0) + amt
            log(f"Took out a ${amt} loan.")
        else:
            amt = min(state["debt"], state["money"], 50 if key == "rep50" else 10**6)
            state["money"] -= amt; state["debt"] -= amt
            log(f"Repaid ${amt} of your debt.")
        return
    for it, r in buttons.get("items", []):
        if not r.collidepoint(mx, my):
            continue
        perm = it.get("perm")
        have = it["id"] in state["owned"] if perm else it["id"] in state["bought_this_year"]
        if have or state["money"] < it["cost"]:
            return
        if it.get("needs") and it["needs"] not in state["owned"]:
            return
        if it.get("home") and state.get("home"):
            return
        state["money"] -= it["cost"]
        if perm:
            state["owned"].add(it["id"])
            if it.get("home"):
                state["home"] = {"name": it["name"].replace("Buy a ", "Your ").title(), "value": it["home"]}
        else:
            state["bought_this_year"].add(it["id"])
            for k, v in it["fx"].items():
                state["stats"][k] = max(0, min(100, state["stats"][k] + v))
        log(f"Bought: {it['name']} (${it['cost']}).")
        return

def apply_passives(state):
    for it in ITEMS:
        if it.get("perm") and it["id"] in state["owned"]:
            for k, v in it["fx"].items():
                state["stats"][k] = max(0, min(100, state["stats"][k] + v))
