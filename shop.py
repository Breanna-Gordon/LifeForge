import pygame
from constants import (WHITE, BLACK, LIGHT_GREY, DARK_GREY, ACCENT, GREEN,
                       font, small_font, draw_text, draw_rounded_rect)

# once_a_year items are treats you can buy again every year; permanent items
# are bought once and then give a small boost every year you own them.
ITEMS = [
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
    {"id": "guitar", "name": "Guitar",         "cost": 90,  "min": 10, "max": 99, "perm": True, "fx": {"mental": 1}, "note": "+1 Mental a year"},
]

def available(age):
    return [i for i in ITEMS if i["min"] <= age <= i["max"]]

def draw_shop_tab(screen, rect, mouse_pos, state, age):
    items = available(age)
    owned, bought = state["owned"], state["bought_this_year"]
    draw_text(screen, f"Shop — you have ${state['money']}", font, BLACK, rect.x, rect.y)
    cols, row_h = 2, 36
    col_w = (rect.width - 12) // cols
    hits = []
    for n, it in enumerate(items):
        col, row = n % cols, n // cols
        r = pygame.Rect(rect.x + col * (col_w + 12), rect.y + 28 + row * (row_h + 3), col_w, row_h)
        have = it["id"] in owned if it.get("perm") else it["id"] in bought
        can = (not have) and state["money"] >= it["cost"]
        hovered = r.collidepoint(mouse_pos) and can
        fill = ACCENT if hovered else (LIGHT_GREY if not can else WHITE)
        draw_rounded_rect(screen, fill, r, radius=8)
        pygame.draw.rect(screen, BLACK, r, 2, border_radius=8)
        draw_text(screen, it["name"], small_font, BLACK, r.x + 10, r.y + 2)
        sub = it.get("note") or ", ".join(f"{k.title()} +{v}" for k, v in it["fx"].items())
        draw_text(screen, sub, small_font, DARK_GREY, r.x + 10, r.y + 18)
        label = "Owned" if (have and it.get("perm")) else ("Bought" if have else f"${it['cost']}")
        draw_text(screen, label, small_font, GREEN if have else BLACK, r.right - 10 - small_font.size(label)[0], r.y + 10)
        hits.append((it, r))
    return {"items": hits}

def handle_shop_click(mx, my, buttons, state, age, log):
    for it, r in buttons.get("items", []):
        if not r.collidepoint(mx, my):
            continue
        perm = it.get("perm")
        have = it["id"] in state["owned"] if perm else it["id"] in state["bought_this_year"]
        if have or state["money"] < it["cost"]:
            return
        state["money"] -= it["cost"]
        if perm:
            state["owned"].add(it["id"])
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
