import random
import pygame
from constants import (WHITE, BLACK, LIGHT_GREY, DARK_GREY, ACCENT, GREEN, RED,
                       font, small_font, draw_text, draw_rounded_rect)

MAX_ACTIVITIES = 3

# kind: "club", "society" or "sport". Sports have tryouts (athletic >= join
# is a safe pass; below it you can still get lucky) and a keep level: if
# your Athletic stat falls below it you're cut from the team.
ACTIVITIES = [
    {"id": "art",     "name": "Art Club",          "kind": "club",    "min": 8,  "fx": {"mental": 2, "looks": 0}},
    {"id": "chess",   "name": "Chess Club",        "kind": "club",    "min": 9,  "fx": {"academic": 2, "mental": 1}},
    {"id": "drama",   "name": "Drama Society",     "kind": "society", "min": 11, "fx": {"social": 2, "looks": 1}},
    {"id": "coding",  "name": "Coding Club",       "kind": "club",    "min": 11, "fx": {"academic": 2}},
    {"id": "band",    "name": "Music Band",        "kind": "club",    "min": 12, "fx": {"social": 1, "mental": 2}},
    {"id": "debate",  "name": "Debate Society",    "kind": "society", "min": 13, "fx": {"academic": 1, "social": 2}},
    {"id": "volunteer","name": "Volunteering",     "kind": "society", "min": 14, "fx": {"social": 2, "mental": 1}},
    {"id": "gaming",  "name": "Gaming Society",    "kind": "society", "min": 16, "fx": {"social": 3}},
    {"id": "football","name": "Football Team",    "kind": "sport",   "min": 8,  "join": 45, "keep": 35, "fx": {"athletic": 3, "physical": 1, "social": 1}},
    {"id": "basket",  "name": "Basketball Team",   "kind": "sport",   "min": 10, "join": 50, "keep": 40, "fx": {"athletic": 3, "physical": 1, "social": 1}},
    {"id": "swim",    "name": "Swimming Team",     "kind": "sport",   "min": 8,  "join": 50, "keep": 40, "fx": {"athletic": 3, "physical": 2, "looks": 1}},
    {"id": "track",   "name": "Athletics Team",    "kind": "sport",   "min": 10, "join": 55, "keep": 45, "fx": {"athletic": 4, "physical": 2}},
    {"id": "rugby",   "name": "Rugby Team",        "kind": "sport",   "min": 14, "join": 60, "keep": 50, "fx": {"athletic": 4, "physical": 1, "social": 1}},
]
BY_ID = {a["id"]: a for a in ACTIVITIES}

def available(age):
    return [a for a in ACTIVITIES if a["min"] <= age]

def tryout_chance(stats, act):
    if act["kind"] != "sport":
        return 1.0
    return max(0.05, min(0.95, (stats["athletic"] - act["join"] + 20) / 40))

def on_team(state):
    return any(BY_ID[i]["kind"] == "sport" for i in state["activities"])

def draw_activities_tab(screen, rect, mouse_pos, state, age):
    items = available(age)
    mine = state["activities"]
    draw_text(screen, f"Clubs, societies and sports ({len(mine)}/{MAX_ACTIVITIES} joined)", font, BLACK, rect.x, rect.y)
    cols, row_h = 2, 36
    col_w = (rect.width - 12) // cols
    hits = []
    for n, a in enumerate(items):
        col, row = n % cols, n // cols
        r = pygame.Rect(rect.x + col * (col_w + 12), rect.y + 28 + row * (row_h + 3), col_w, row_h)
        joined = a["id"] in mine
        full = len(mine) >= MAX_ACTIVITIES
        done = state["actions_used"].get("__act__" + a["id"], 0) >= 1
        can = state["actions_remaining"] > 0 and not full and not done and not joined
        hovered = r.collidepoint(mouse_pos) and (can or joined)
        fill = GREEN if joined and not hovered else (ACCENT if hovered else (WHITE if can else LIGHT_GREY))
        draw_rounded_rect(screen, fill, r, radius=8)
        pygame.draw.rect(screen, BLACK, r, 2, border_radius=8)
        draw_text(screen, a["name"], small_font, BLACK, r.x + 10, r.y + 2)
        if a["kind"] == "sport":
            sub = f"Tryout. Needs Athletic {a['join']}+, cut below {a['keep']}"
        else:
            sub = ", ".join(f"{k.title()} +{v}" for k, v in a["fx"].items() if v)
        draw_text(screen, sub, small_font, DARK_GREY, r.x + 10, r.y + 18)
        if joined:
            label = f"Leave ({mine[a['id']]}y)" if hovered else f"Joined ({mine[a['id']]}y)"
        elif done:
            label = "Tried"
        else:
            label = "Try out" if a["kind"] == "sport" else "Join"
        draw_text(screen, label, small_font, BLACK, r.right - 10 - small_font.size(label)[0], r.y + 2)
        hits.append((a, r))
    if state.get("scholarship"):
        msg = "Sports scholarship offer (easier university entry)"
        draw_text(screen, msg, small_font, GREEN, rect.right - small_font.size(msg)[0], rect.y + 4)
    return {"acts": hits}

def handle_activities_click(mx, my, buttons, state, age, friends, make_friend, log):
    for a, r in buttons.get("acts", []):
        if not r.collidepoint(mx, my):
            continue
        mine = state["activities"]
        if a["id"] in mine:
            del mine[a["id"]]
            log(f"Left the {a['name']}.")
            return
        if (len(mine) >= MAX_ACTIVITIES or state["actions_remaining"] <= 0
                or state["actions_used"].get("__act__" + a["id"], 0) >= 1):
            return
        state["actions_remaining"] -= 1
        state["actions_used"]["__act__" + a["id"]] = 1
        if random.random() <= tryout_chance(state["stats"], a):
            mine[a["id"]] = 0
            log(f"Joined the {a['name']}." if a["kind"] != "sport" else f"Made the {a['name']}.")
            if len(friends) < 6 and random.random() < 0.6:
                f = make_friend()
                log(f"Met {f['name']} through the {a['name']}.")
        else:
            log(f"Didn't make the {a['name']} after tryouts.")
        return

def advance_activities_year(state, log):
    """Called at year end: apply each membership's boosts and cut sports
    players whose Athletic has fallen too low."""
    stats = state["stats"]
    for aid in list(state["activities"]):
        a = BY_ID[aid]
        if a["kind"] == "sport" and stats["athletic"] < a["keep"]:
            del state["activities"][aid]
            log(f"Cut from the {a['name']}: not fit enough.")
            continue
        state["activities"][aid] += 1
        for k, v in a["fx"].items():
            stats[k] = max(0, min(100, stats[k] + v))
    # a sports scholarship offer for strong players about to leave school
    if on_team(state) and stats["athletic"] >= 80 and 16 <= state["age"] <= 22 and not state.get("scholarship"):
        state["scholarship"] = True
        log("Offered a sports scholarship!")
