import worldjobs
import sports
from constants import fmt
import random
import pygame
from constants import OUTLINE, INK, MUTED, draw_card, draw_pill, draw_shadow
import lifestyle
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

# Outings and lessons. Free ones cost an action but no money; paid lessons
# build a skill (level shown on the card). Under 16, family pays half.
OUTINGS = [
    {"id": "walk",    "name": "Go for a walk",       "min": 3,  "max": 99, "cost": 0,  "fx": {"physical": 2, "mental": 1}},
    {"id": "play",    "name": "Playground",          "min": 3,  "max": 12, "cost": 0,  "fx": {"physical": 1, "social": 2, "mental": 1}},
    {"id": "library", "name": "Library visit",       "min": 5,  "max": 99, "cost": 0,  "fx": {"academic": 2, "mental": 1}},
    {"id": "jog",     "name": "Go for a jog",        "min": 10, "max": 80, "cost": 0,  "fx": {"physical": 2, "athletic": 2}},
    {"id": "busk",    "name": "Busk in the street",  "min": 12, "max": 99, "cost": 0,  "fx": {"social": 1}, "needs": ("singing", "music"), "earn": True},
    {"id": "singing", "name": "Singing lessons",     "min": 5,  "max": 99, "cost": 30, "fx": {"mental": 2, "social": 1}, "skill": "singing"},
    {"id": "music",   "name": "Music lessons",       "min": 6,  "max": 99, "cost": 40, "fx": {"mental": 2, "academic": 1}, "skill": "music"},
    {"id": "dance",   "name": "Dance class",         "min": 5,  "max": 99, "cost": 30, "fx": {"physical": 1, "athletic": 1, "looks": 1}, "skill": "dance"},
    {"id": "artcls",  "name": "Art class",           "min": 5,  "max": 99, "cost": 25, "fx": {"mental": 2, "looks": 0}, "skill": "art"},
    {"id": "swim",    "name": "Swimming lessons",    "min": 4,  "max": 99, "cost": 25, "fx": {"athletic": 2, "physical": 2}, "skill": "swimming"},
    {"id": "lang",    "name": "Language class",      "min": 10, "max": 99, "cost": 35, "fx": {"academic": 3, "social": 1}, "skill": "languages"},
    {"id": "martial", "name": "Martial arts",        "min": 7,  "max": 80, "cost": 35, "fx": {"athletic": 2, "physical": 1, "mental": 1}, "skill": "martial arts"},
    {"id": "yoga",    "name": "Yoga class",          "min": 14, "max": 99, "cost": 20, "fx": {"mental": 3, "physical": 1}, "skill": "yoga"},
]
OUT_BY_ID = {o["id"]: o for o in OUTINGS}

def outing_cost(o, age):
    return o["cost"]

def outing_visible(o, age, skills):
    if not (o["min"] <= age <= o["max"]):
        return False
    return not o.get("needs") or any(skills.get(k, 0) >= 3 for k in o["needs"])

def draw_activities_tab(screen, rect, mouse_pos, state, age, career=None):
    view = state.setdefault("act_view", "clubs")
    skills = state.setdefault("skills", {})
    mine = state["activities"]
    views = lifestyle.view_rects(rect)
    only_life = state.get("_tab") == "Lifestyle"
    if only_life:
        view = state["act_view"] = "life"
    elif view == "life":
        view = state["act_view"] = "clubs"
    for key, label in (() if only_life else (("clubs", "Clubs"), ("outings", "Outings"), ("sports", "Sports"))):
        vr = views[key]
        on = view == key
        draw_rounded_rect(screen, ACCENT if on else (WHITE if not vr.collidepoint(mouse_pos) else (235, 235, 240)), vr, radius=8)
        pygame.draw.rect(screen, OUTLINE, vr, 2, border_radius=8)
        draw_text(screen, label, small_font, INK, vr.centerx, vr.centery, centre=True)
    if view == "life":
        res = lifestyle.draw_lifestyle(screen, rect, mouse_pos, state, age, career or {})
        res["views"] = views
        return res
    if view == "sports":
        res = sports.draw_sports(screen, rect, mouse_pos, state, age, career or {})
        res["views"] = views
        return res
    cols, row_h = 2, 36
    col_w = (rect.width - 12) // cols
    hits = []
    outs = []
    if view == "outings":
        draw_text(screen, f"Outings ({state['actions_remaining']} actions left)", font, INK, rect.x, rect.y)
        items = [o for o in OUTINGS if outing_visible(o, age, skills)]
        for n, o in enumerate(items):
            col, row = n % cols, n // cols
            r = pygame.Rect(rect.x + col * (col_w + 12), rect.y + 28 + row * (row_h + 3), col_w, row_h)
            cost = outing_cost(o, age)
            done = False
            can = state["actions_remaining"] > 0 and not done and (state["money"] >= cost or age < 18)
            hovered = r.collidepoint(mouse_pos) and can
            draw_rounded_rect(screen, ACCENT if hovered else (WHITE if can else LIGHT_GREY), r, radius=8)
            pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
            draw_text(screen, o["name"], small_font, INK, r.x + 10, r.y + 2)
            if o.get("earn"):
                sub = "Earn a little cash from your talent"
            else:
                sub = ", ".join(f"{k.title()} +{v}" for k, v in o["fx"].items() if v)
                if o.get("skill") and skills.get(o["skill"]):
                    sub += f"  ({o['skill'].title()} lvl {skills[o['skill']]})"
            draw_text(screen, sub, small_font, DARK_GREY, r.x + 10, r.y + 18)
            n_done = state["actions_used"].get("__out__" + o["id"], 0)
            label = ("Free" if cost == 0 else (("Parents pay" if o["id"] in state.get("parent_pays", []) else "Ask parents") if age < 18 else f"${fmt(cost)}")) + (f"  x{n_done}" if n_done else "")
            draw_text(screen, label, small_font, GREEN if cost == 0 and not done else BLACK,
                      r.right - 10 - small_font.size(label)[0], r.y + 2)
            outs.append((o, r))
        return {"acts": [], "views": views, "outs": outs}
    items = available(age)
    draw_text(screen, f"Clubs ({len(mine)}/{MAX_ACTIVITIES})", font, INK, rect.x, rect.y)
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
        pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
        draw_text(screen, a["name"], small_font, INK, r.x + 10, r.y + 2)
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
        draw_text(screen, label, small_font, INK, r.right - 10 - small_font.size(label)[0], r.y + 2)
        hits.append((a, r))
    if state.get("scholarship"):
        msg = "Sports scholarship offer (easier university entry)"
        draw_text(screen, msg, small_font, GREEN, rect.right - small_font.size(msg)[0], rect.bottom - 18)
    return {"acts": hits, "views": views, "outs": []}

def handle_activities_click(mx, my, buttons, state, age, friends, make_friend, log, career=None):
    for key, vr in buttons.get("views", {}).items():
        if vr.collidepoint(mx, my):
            state["act_view"] = key
            return
    if state.get("act_view") == "sports":
        sports.handle_sports_click(mx, my, buttons, state, age, career or {}, log)
        return
    if state.get("act_view") == "life":
        lifestyle.handle_lifestyle_click(mx, my, buttons, state, age, career or {}, friends, make_friend, log)
        return
    skills = state.setdefault("skills", {})
    for o, r in buttons.get("outs", []):
        if not r.collidepoint(mx, my):
            continue
        cost = outing_cost(o, age)
        flag = "__out__" + o["id"]
        if state["actions_remaining"] <= 0:
            return
        if cost and age < 18:
            # a young person asks their parents to pay for lessons
            ask = "__askpay__" + o["id"]
            if o["id"] in state.get("parent_pays", []):
                cost = 0
            elif state["actions_used"].get(ask) == "no":
                log(f"Your parents already said no to {o['name'].lower()} this year.")
                return
            if cost:
                if not state.get("parents_ok"):
                    log("There's nobody to pay for lessons right now.")
                    return
                chance = worldjobs.tier_value(state, {"Struggling": 0.35, "Comfortable": 0.75, "Wealthy": 0.95})
                if random.random() > chance:
                    state["actions_used"][ask] = "no"
                    log(f"You asked your parents to pay for {o['name'].lower()}, but they said not this year.")
                    return
                state.setdefault("parent_pays", []).append(o["id"])
                log(f"Your parents agreed to pay for {o['name'].lower()}, and will keep paying for it.")
                cost = 0
        elif state["money"] < cost:
            return
        n_before = state["actions_used"].get(flag, 0)
        dim = max(0.3, 1 / (1 + 0.5 * n_before))   # repeats give less
        state["actions_remaining"] -= 1
        state["actions_used"][flag] = n_before + 1
        state["money"] -= cost
        stats = state["stats"]
        for k, v in o["fx"].items():
            stats[k] = max(0, min(100, stats[k] + (max(1, round(v * dim)) if v > 0 else v)))
        if o.get("earn"):
            lvl = max(skills.get("singing", 0), skills.get("music", 0))
            got = random.randint(6, 12) + 5 * lvl
            state["money"] += got
            log(f"Busked in the street and earned ${fmt(got)}.")
        elif o.get("skill"):
            skills[o["skill"]] = skills.get(o["skill"], 0) + 1
            log(f"{o['name']}: {o['skill'].title()} is now level {skills[o['skill']]}.")
        else:
            log(f"{o['name']}.")
            if o["id"] in ("walk", "play") and friends and random.random() < 0.3:
                f = random.choice(friends)
                f["closeness"] = min(100, f["closeness"] + 3)
            elif o["id"] == "play" and len(friends) < 6 and random.random() < 0.4:
                nf = make_friend()
                log(f"Made friends with {nf['name']} at the playground.")
        return
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
    for sk, lvl in state.get("skills", {}).items():
        if lvl >= 3:     # a developed skill keeps lifting your spirits
            stats["mental"] = min(100, stats["mental"] + 1)
    # a sports scholarship offer for strong players about to leave school
    if on_team(state) and stats["athletic"] >= 80 and 16 <= state["age"] <= 22 and not state.get("scholarship"):
        state["scholarship"] = True
        log("Offered a sports scholarship!")
