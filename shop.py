from constants import fmt
from constants import OUTLINE, INK, MUTED, draw_card, draw_pill, draw_shadow, fmt_short
import pygame
import assets
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
    {"id": "holiday","name": "Holiday",        "cost": 1500, "min": 6,  "max": 99, "fx": {"mental": 5, "social": 2, "physical": 1}},
    {"id": "hair",   "name": "New haircut",    "cost": 20,  "min": 10, "max": 99, "fx": {"looks": 3}},
    {"id": "outfit", "name": "New outfit",     "cost": 40,  "min": 10, "max": 99, "fx": {"looks": 3, "social": 1}},
    {"id": "skin",   "name": "Skincare",       "cost": 25,  "min": 13, "max": 99, "fx": {"looks": 2}},
    {"id": "bike",   "name": "Bike",           "cost": 80,  "min": 8,  "max": 99, "perm": True, "fx": {"physical": 1, "athletic": 1}, "note": "+1 Health and Athletic a year"},
    {"id": "laptop", "name": "Laptop",         "cost": 900, "min": 12, "max": 99, "perm": True, "fx": {"academic": 1}, "note": "+1 Academic a year"},
    {"id": "dog",    "name": "Dog",            "cost": 150, "min": 8,  "max": 99, "perm": True, "fx": {"social": 1, "mental": 1}, "note": "+1 Social and Mental a year"},
    {"id": "licence","name": "Driving lessons","cost": 800,  "min": 17, "max": 99, "perm": True, "fx": {}, "note": "Get your driving licence"},
    {"id": "car", "hidden": True,    "name": "Car",            "cost": 18000, "min": 17, "max": 99, "perm": True, "needs": "licence", "fx": {"social": 1}, "note": "Needs a licence. +5% pay, +1 Social a year"},
    {"id": "flat", "hidden": True,   "name": "Buy a flat",     "cost": 120000, "min": 18, "max": 99, "perm": True, "home": 120000, "fx": {}, "note": "No more rent. Value grows"},
    {"id": "house", "hidden": True,  "name": "Buy a house",    "cost": 300000, "min": 21, "max": 99, "perm": True, "home": 300000, "fx": {}, "note": "No more rent. Value grows"},
    {"id": "guitar", "name": "Guitar",         "cost": 90,  "min": 10, "max": 99, "perm": True, "fx": {"mental": 1}, "note": "+1 Mental a year"},
]

def available(age):
    return [i for i in ITEMS if i["min"] <= age <= i["max"] and not i.get("hidden")]

AMOUNTS = [("1k", 1000), ("10k", 10000), ("100k", 100000), ("1M", 1000000), ("Max", None)]
BANK_BUTTONS = [("dep", "Deposit"), ("wd", "Withdraw"), ("inv", "Invest"), ("invout", "Cash out"),
                ("borrow", "Borrow"), ("repay", "Repay"), ("sellhome", "Sell home")]
AUTO_MODES = [("off", "Off"), ("savings", "Savings"), ("invest", "Invest")]

def loan_limit(state):
    return max(40000, 3 * state.get("_income", 0))

def _chosen(state, key, age):
    """The amount a bank button would move right now (0 if it can't)."""
    amt = state.get("bank_amt", 1000)
    m, sv, d = state["money"], state.get("savings", 0), state.get("debt", 0)
    inv = state.get("invest", 0)
    room = max(0, loan_limit(state) - d)
    cap = {"dep": m, "wd": sv, "inv": m if age >= 18 else 0, "invout": inv, "borrow": room if age >= 18 else 0,
           "repay": min(d, m), "sellhome": 0}.get(key, 0)
    if key == "invout":
        return cap if amt is None else min(cap, amt)
    return cap if amt is None else min(cap, amt)

def draw_shop_tab(screen, rect, mouse_pos, state, age):
    view = state.setdefault("shop_view", "shop")
    views = {"shop": pygame.Rect(rect.right - 340, rect.y - 2, 64, 26), "assets": pygame.Rect(rect.right - 272, rect.y - 2, 76, 26),
             "biz": pygame.Rect(rect.right - 192, rect.y - 2, 90, 26), "bank": pygame.Rect(rect.right - 98, rect.y - 2, 98, 26)}
    for key, label in (("shop", "Shop"), ("assets", "Assets"), ("biz", "Business"), ("bank", "Bank")):
        draw_pill(screen, views[key], label, small_font, mouse_pos, selected=view == key)
    if view == "biz":
        import business
        return {"items": [], "views": views, "bank": [], "biz": business.draw_business(screen, rect, mouse_pos, state, age)}
    if view == "assets":
        return {"items": [], "views": views, "bank": [], "assets": assets.draw_assets(screen, rect, mouse_pos, state, age)}
    if view == "bank":
        debt, sv = state.get("debt", 0), state.get("savings", 0)
        draw_text(screen, "Bank", font, INK, rect.x, rect.y)
        draw_text(screen, f"Cash ${fmt(state['money'])}   Savings ${fmt(sv)} (+3%)   Invested ${fmt(state.get('invest', 0))}   Debt ${fmt(debt)} (+5%)",
                  small_font, DARK_GREY, rect.x, rect.y + 28)
        nw = state["money"] + sv + state.get("invest", 0) - debt + assets.net_worth_assets(state)
        draw_text(screen, f"Net worth ${fmt(nw)}", small_font, GREEN if nw >= 0 else (200, 60, 60), rect.x + 70, rect.y + 4)
        draw_text(screen, f"Wages repay debt automatically. You can borrow up to ${fmt(loan_limit(state))} in total (18+).",
                  small_font, DARK_GREY, rect.x, rect.y + 48)
        hits, chips = [], []
        draw_text(screen, "Amount:", small_font, INK, rect.x, rect.y + 79)
        cur = state.get("bank_amt", 1000)
        for n, (lab, val) in enumerate(AMOUNTS):
            r = pygame.Rect(rect.x + 70 + n * 70, rect.y + 72, 64, 28)
            on = cur == val
            draw_pill(screen, r, lab, small_font, mouse_pos, selected=on)
            chips.append((("amt", val), r))
        bw = (rect.width - 3 * 8) // 4
        for n, (key, label) in enumerate(BANK_BUTTONS):
            r = pygame.Rect(rect.x + (n % 4) * (bw + 8), rect.y + 110 + (n // 4) * 42, bw, 36)
            if key == "sellhome":
                ok, text = bool(state.get("home")), label
            else:
                v = _chosen(state, key, age)
                ok = v > 0
                text = f"{label} ${fmt(v)}" if v else label
            draw_pill(screen, r, text, small_font, mouse_pos, disabled=not ok)
            hits.append((key, r))
        mode = state.get("auto_bank", "off")
        draw_text(screen, "Auto-manage spare cash each year:", small_font, INK, rect.x, rect.y + 207)
        for n, (k, lab) in enumerate(AUTO_MODES):
            r = pygame.Rect(rect.x + 290 + n * 86, rect.y + 200, 80, 28)
            draw_pill(screen, r, lab, small_font, mouse_pos, selected=mode == k)
            chips.append((("auto", k), r))
        draw_text(screen, "Repays debt first, then moves cash above a buffer into savings or investments.",
                  small_font, DARK_GREY, rect.x, rect.y + 236)
        return {"items": [], "views": views, "bank": hits, "chips": chips}
    all_items = available(age)
    per_page = 12
    pages = max(1, -(-len(all_items) // per_page))
    page = max(0, min(state.get("shop_page", 0), pages - 1))
    state["shop_page"] = page
    items = all_items[page * per_page:(page + 1) * per_page]
    if pages > 1:
        views["prev"] = pygame.Rect(rect.right - 410, rect.y - 2, 28, 26)
        views["next"] = pygame.Rect(rect.right - 376, rect.y - 2, 28, 26)
        for key, lab in (("prev", "<"), ("next", ">")):
            draw_rounded_rect(screen, WHITE if not views[key].collidepoint(mouse_pos) else (255, 236, 218), views[key], radius=8)
            pygame.draw.rect(screen, OUTLINE, views[key], 1, border_radius=8)
            draw_text(screen, lab, small_font, INK, views[key].centerx, views[key].centery, centre=True)
    owned, bought = state["owned"], state["bought_this_year"]
    draw_text(screen, f"Shop: ${fmt(state['money'])}" + (f"  (page {page + 1}/{pages})" if pages > 1 else ""), font, INK, rect.x, rect.y)
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
        draw_card(screen, r, fill=(255, 236, 218) if hovered else (WHITE if can or have else (240, 238, 244)), radius=10, shadow=False)
        draw_text(screen, it["name"], small_font, INK, r.x + 10, r.y + 2)
        sub = it.get("note") or ", ".join(f"{k.title()} +{v}" for k, v in it["fx"].items())
        draw_text(screen, sub, small_font, DARK_GREY, r.x + 10, r.y + 18)
        label = "Owned" if (have and it.get("perm")) else ("Bought" if have else f"${fmt(it['cost'])}")
        draw_text(screen, label, small_font, GREEN if have else (BLACK if can else DARK_GREY), r.right - 10 - small_font.size(label)[0], r.y + 10)
        hits.append((it, r))
    return {"items": hits, "views": views, "bank": []}

def _bank_ok(key, state, age):
    if key == "sellhome":
        return bool(state.get("home"))
    return _chosen(state, key, age) > 0

def handle_shop_click(mx, my, buttons, state, age, log):
    for key, vr in buttons.get("views", {}).items():
        if vr.collidepoint(mx, my):
            if key in ("prev", "next"):
                state["shop_page"] = max(0, state.get("shop_page", 0) + (1 if key == "next" else -1))
            else:
                state["shop_view"] = key
            return
    if buttons.get("biz") is not None:
        import business
        business.handle_business_click(mx, my, buttons["biz"], state, age, log)
        return
    if buttons.get("assets") is not None:
        assets.handle_assets_click(mx, my, buttons["assets"], state, age, log)
        return
    for (kind, val), r in buttons.get("chips", []):
        if r.collidepoint(mx, my):
            state["bank_amt" if kind == "amt" else "auto_bank"] = val
            return
    for key, r in buttons.get("bank", []):
        if not r.collidepoint(mx, my) or not _bank_ok(key, state, age):
            continue
        if key == "sellhome":
            assets.ensure(state)
            assets.do_prop(state, state["home"], "sell", log)
            return
        v = _chosen(state, key, age)
        if key == "dep":
            state["money"] -= v; state["savings"] = state.get("savings", 0) + v
            log(f"Deposited ${fmt(v)}.")
        elif key == "wd":
            state["money"] += v; state["savings"] -= v
            log(f"Withdrew ${fmt(v)}.")
        elif key == "inv":
            state["money"] -= v; state["invest"] = state.get("invest", 0) + v
            log(f"Invested ${fmt(v)}. Returns vary a lot from year to year.")
        elif key == "invout":
            state["money"] += v; state["invest"] -= v
            log(f"Cashed out ${fmt(v)} of investments.")
        elif key == "borrow":
            state["money"] += v; state["debt"] = state.get("debt", 0) + v
            log(f"Took out a ${fmt(v)} loan.")
        elif key == "repay":
            state["money"] -= v; state["debt"] -= v
            log(f"Repaid ${fmt(v)} of your debt.")
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
        log(f"Bought: {it['name']} (${fmt(it['cost'])}).")
        return

def apply_passives(state):
    for it in ITEMS:
        if it.get("perm") and it["id"] in state["owned"]:
            for k, v in it["fx"].items():
                state["stats"][k] = max(0, min(100, state["stats"][k] + v))


def bank_auto(state, log):
    """Year end: with auto-manage on, repay debt, then move cash above a
    buffer into savings or investments."""
    mode = state.get("auto_bank", "off")
    if mode == "off":
        return
    pay = min(state.get("debt", 0), max(0, state["money"] - 5000))
    if pay > 0:
        state["money"] -= pay
        state["debt"] -= pay
        log(f"Auto-repaid ${fmt(pay)} of debt.")
    buffer = max(10000, state.get("_income", 0) // 2)
    extra = state["money"] - buffer
    if extra <= 0 or state.get("age", 0) < 18:
        return
    state["money"] -= extra
    if mode == "invest":
        state["invest"] = state.get("invest", 0) + extra
        log(f"Auto-invested ${fmt(extra)} of spare cash.")
    else:
        state["savings"] = state.get("savings", 0) + extra
        log(f"Auto-saved ${fmt(extra)} of spare cash.")
