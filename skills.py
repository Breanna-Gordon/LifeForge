"""Skills: practise anything, as often as you like. No action cost, no yearly
limit and no slots. Each skill has levels (to 10); a level-up lifts your stats.
Also home to Social Media (followers and income) and a risky Crime category."""
import random
import pygame
from constants import (fmt, INK, MUTED, WHITE, ACCENT, GREEN, RED, OUTLINE, LIGHT_GREY, DARK_GREY,
                       font, small_font, draw_text, draw_rounded_rect)

MAX_LEVEL = 10
_TINY = pygame.font.Font(None, 17)

# key, label, category, min age, stats a level-up improves
SKILLS = [
    ("reading", "Reading", "Mind", 5, {"academic": 2, "mental": 1}),
    ("chess", "Chess", "Mind", 6, {"academic": 2, "mental": 1}),
    ("coding", "Coding", "Mind", 9, {"academic": 3}),
    ("languages", "Languages", "Mind", 8, {"academic": 2, "social": 1}),
    ("meditation", "Meditation", "Mind", 10, {"mental": 3}),
    ("fitness", "Fitness", "Body", 8, {"physical": 2, "athletic": 2}),
    ("swimming", "Swimming", "Body", 4, {"athletic": 2, "physical": 1}),
    ("martial arts", "Martial arts", "Body", 7, {"athletic": 2, "mental": 1}),
    ("yoga", "Yoga", "Body", 12, {"mental": 2, "physical": 1}),
    ("running", "Running", "Body", 8, {"athletic": 3}),
    ("art", "Art", "Creative", 5, {"mental": 2, "looks": 1}),
    ("music", "Music", "Creative", 6, {"mental": 2, "social": 1}),
    ("singing", "Singing", "Creative", 6, {"social": 2, "mental": 1}),
    ("dance", "Dance", "Creative", 5, {"looks": 2, "athletic": 1}),
    ("writing", "Writing", "Creative", 9, {"academic": 1, "mental": 2}),
    ("photography", "Photography", "Creative", 10, {"looks": 1, "social": 1, "mental": 1}),
    ("charm", "Charm", "Social", 10, {"social": 3}),
    ("speaking", "Public speaking", "Social", 12, {"social": 2, "academic": 1}),
    ("cooking", "Cooking", "Social", 8, {"physical": 1, "mental": 1, "social": 1}),
    ("fashion", "Fashion", "Social", 12, {"looks": 3}),
    ("acting", "Acting", "Acting", 8, {"social": 2, "looks": 1}),
    ("improv", "Improvisation", "Acting", 10, {"social": 2, "mental": 1}),
    ("stagecraft", "Stage presence", "Acting", 10, {"looks": 2, "social": 1}),
    ("streetwise", "Street smarts", "Crime", 14, {"social": 1, "mental": -1}),
    ("lockpicking", "Lockpicking", "Crime", 15, {"academic": 1, "mental": -1}),
    ("hacking", "Hacking", "Crime", 14, {"academic": 2, "mental": -1}),
]
BY_KEY = {s[0]: s for s in SKILLS}
CATS = ["Mind", "Body", "Creative", "Social", "Acting", "Social Media", "Crime"]
CAT_COL = {"Mind": (110, 150, 240), "Body": (230, 110, 100), "Creative": (240, 140, 190), "Social": (240, 180, 80),
           "Acting": (180, 120, 230), "Social Media": (80, 190, 210), "Crime": (150, 150, 170)}
CRIME_RISK = 0.03

def need(level):
    return 3 + level * 2

def level_of(state, key):
    return state.setdefault("skills", {}).get(key, 0)

def practise(state, key, log):
    """One practice session. Returns a short message."""
    lvl = level_of(state, key)
    if lvl >= MAX_LEVEL:
        return "Maxed out. You're a master."
    xp = state.setdefault("skill_xp", {})
    xp[key] = xp.get(key, 0) + 1
    label, cat, fx = BY_KEY[key][1], BY_KEY[key][2], BY_KEY[key][4]
    msg = f"Practised {label.lower()}."
    if cat == "Crime" and random.random() < CRIME_RISK:
        state["record"] = state.get("record", 0) + 1
        state["stats"]["mental"] = max(0, state["stats"]["mental"] - 2)
        log(f"You were caught practising {label.lower()} and picked up a criminal record.")
        msg = "Caught! That's a criminal record."
    if xp[key] >= need(lvl):
        xp[key] = 0
        state["skills"][key] = lvl + 1
        for k, v in fx.items():
            state["stats"][k] = max(0, min(100, state["stats"][k] + v))
        log(f"{label} reached level {lvl + 1}.")
        try:
            import home
            home.feed_add(state, f"{label} reached level {lvl + 1}", ", ".join(f"{k.title()} {v:+d}" for k, v in fx.items()))
        except Exception:
            pass
        msg = f"{label} is now level {lvl + 1}!"
    return msg

# ---------------------------------------------------------- social media
def post(state, log):
    sm = state.setdefault("social_media", {"followers": 0, "posts": 0})
    st = state["stats"]
    base = 1 + st["looks"] / 40 + st["social"] / 40 + level_of(state, "photography") + level_of(state, "charm") * 0.5
    viral = random.random() < 0.02 + min(0.05, sm["followers"] / 1_000_000)
    gain = int(base * random.uniform(0.6, 1.6) * (1 + sm["followers"] / 4000))
    if viral:
        gain += max(50, sm["followers"] // 2)
    sm["posts"] += 1
    sm["followers"] += gain
    if viral:
        log(f"A post of yours went viral: +{fmt(gain)} followers.")
        return f"Viral! +{fmt(gain)} followers."
    return f"Posted. +{fmt(gain)} followers."

def income_per_year(state):
    f = state.get("social_media", {}).get("followers", 0)
    return int(f * 0.02) if f >= 1000 else 0

def year(state, log, career=None):
    inc = income_per_year(state)
    if inc:
        state["money"] += inc
        log(f"Your social media earned ${fmt(inc)} in sponsorships and ads.")
        if career is not None:
            career["fame"] = min(100, career.get("fame", 0) + (1 if state["social_media"]["followers"] >= 20000 else 0))
    sm = state.get("social_media")
    if sm and sm["followers"] > 0:
        sm["followers"] = int(sm["followers"] * random.uniform(0.96, 1.03))    # people drift

# ------------------------------------------------------------------ draw
def _trim(text, fnt, width):
    if fnt.size(text)[0] <= width:
        return text
    while len(text) > 1 and fnt.size(text + "...")[0] > width:
        text = text[:-1]
    return text + "..."

def draw_skills(screen, rect, mouse, state, age):
    cat = state.get("_skill_cat", "Mind")
    skills = state.setdefault("skills", {})
    xp = state.setdefault("skill_xp", {})
    hits, pills = [], []
    draw_text(screen, "Skills  (practise as much as you like)", font, INK, rect.x, rect.y + 30)
    x = rect.x
    for c in CATS:
        w = small_font.size(c)[0] + 22
        r = pygame.Rect(x, rect.y + 58, w, 24)
        on = c == cat
        draw_rounded_rect(screen, CAT_COL[c] if on else (WHITE if not r.collidepoint(mouse) else (235, 235, 240)), r, radius=10)
        pygame.draw.rect(screen, OUTLINE, r, 1, border_radius=10)
        draw_text(screen, c, small_font, INK, r.centerx, r.centery, centre=True)
        pills.append((c, r))
        x += w + 6
    y = rect.y + 96
    msg = state.get("_skill_msg", "")
    if cat == "Social Media":
        sm = state.setdefault("social_media", {"followers": 0, "posts": 0})
        if age < 12:
            draw_text(screen, "You need to be 12 to have a social media account.", small_font, MUTED, rect.x, y)
        else:
            draw_text(screen, f"{fmt(sm['followers'])}", pygame.font.Font(None, 64), INK, rect.x, y)
            draw_text(screen, "followers", small_font, MUTED, rect.x + 4, y + 52)
            draw_text(screen, f"Posts: {sm['posts']}", small_font, MUTED, rect.x + 4, y + 74)
            inc = income_per_year(state)
            draw_text(screen, f"Income: ${fmt(inc)} a year" if inc else "Reach 1,000 followers to earn sponsorship money.", small_font, GREEN if inc else MUTED, rect.x + 4, y + 96)
            for i, (label, key) in enumerate((("Post a photo", "post"), ("Make a video", "video"), ("Go live", "live"))):
                r = pygame.Rect(rect.x + 4 + i * 176, y + 132, 166, 40)
                draw_rounded_rect(screen, ACCENT if r.collidepoint(mouse) else (WHITE), r, radius=12)
                pygame.draw.rect(screen, OUTLINE, r, 1, border_radius=12)
                draw_text(screen, label, small_font, INK, r.centerx, r.centery, centre=True)
                hits.append((key, r))
            draw_text(screen, "Looks, Social, Photography and Charm all help you grow. No limit on posting.", _TINY, MUTED, rect.x + 4, y + 184)
    else:
        items = [s for s in SKILLS if s[2] == cat]
        for i, (key, label, c, minage, fx) in enumerate(items):
            col, row = i % 2, i // 2
            r = pygame.Rect(rect.x + col * 334, y + row * 62, 326, 54)
            locked = age < minage
            lvl = skills.get(key, 0)
            hov = r.collidepoint(mouse) and not locked and lvl < MAX_LEVEL
            draw_rounded_rect(screen, ACCENT if hov else (LIGHT_GREY if locked else WHITE), r, radius=10)
            pygame.draw.rect(screen, OUTLINE, r, 1, border_radius=10)
            draw_text(screen, label, small_font, INK, r.x + 12, r.y + 6)
            sub = f"Needs age {minage}" if locked else ", ".join(f"{k.title()} {v:+d}" for k, v in fx.items()) + " per level"
            draw_text(screen, sub, _TINY, DARK_GREY, r.x + 12, r.y + 24)
            lv = f"Lv {lvl}" if lvl < MAX_LEVEL else "MAX"
            draw_text(screen, lv, small_font, INK, r.right - 12 - small_font.size(lv)[0], r.y + 6)
            frac = 1.0 if lvl >= MAX_LEVEL else xp.get(key, 0) / need(lvl)
            bar = pygame.Rect(r.x + 12, r.bottom - 12, r.w - 24, 5)
            pygame.draw.rect(screen, (220, 216, 230), bar, border_radius=3)
            if frac > 0:
                pygame.draw.rect(screen, CAT_COL[cat], (bar.x, bar.y, max(5, int(bar.w * frac)), 5), border_radius=3)
            if not locked and lvl < MAX_LEVEL:
                hits.append((key, r))
        if cat == "Crime":
            draw_text(screen, "Practising crime skills is risky: you can pick up a criminal record.", _TINY, RED, rect.x, y + 62 * ((len(items) + 1) // 2) + 8)
    if msg:
        draw_text(screen, msg, small_font, GREEN, rect.x, rect.bottom - 22)
    return {"skills": hits, "skill_cats": pills, "acts": [], "outs": []}

def handle_click(mx, my, buttons, state, age, log):
    for c, r in buttons.get("skill_cats", []):
        if r.collidepoint(mx, my):
            state["_skill_cat"] = c
            state["_skill_msg"] = ""
            return True
    for key, r in buttons.get("skills", []):
        if not r.collidepoint(mx, my):
            continue
        if key == "post":
            state["_skill_msg"] = post(state, log)
        elif key == "video":
            state["_skill_msg"] = post(state, log)
            state["_skill_msg"] = post(state, log)
        elif key == "live":
            state["_skill_msg"] = post(state, log)
            state["stats"]["social"] = min(100, state["stats"]["social"] + (1 if random.random() < 0.15 else 0))
        else:
            state["_skill_msg"] = practise(state, key, log)
        return True
    return False
