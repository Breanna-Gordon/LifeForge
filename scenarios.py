"""Starting scenarios: a family background plus stats, some of them hard."""
import random
import pygame
import asyncio
import worldjobs
from constants import (SCREEN_WIDTH, SCREEN_HEIGHT, INK, MUTED, ACCENT, GREEN, WHITE, font, small_font, title_font,
                       draw_text, draw_rounded_rect, make_vertical_gradient)

def _stats(**kw):
    base = {"physical": 60, "mental": 60, "social": 55, "academic": 55, "looks": 55, "athletic": 55, "wealth": 50}
    base.update(kw)
    return {k: max(5, min(98, v + random.randint(-4, 4))) for k, v in base.items()}

def _parents(family, titles, grand=None):
    pars = [p for p in family if p["relation"] in ("Mother", "Father")]
    for p in pars:
        worldjobs.assign_job(p, worldjobs.BY_TITLE[random.choice(titles)])
    if grand:
        for p in family:
            if p["relation"].endswith(("Grandfather", "Grandmother")):
                worldjobs.assign_job(p, worldjobs.BY_TITLE[random.choice(grand)])

def _only_younger(family, keep=None):
    """You're born at age 0, so every sibling in the starting tree is older.
    Heirs are the eldest: drop them (and a half-sibling's other parent).
    Younger brothers and sisters arrive later as babies."""
    gone = [p for p in family if "Sibling" in p["relation"] and p is not keep]
    names = {p["name"] for p in gone}
    family[:] = [p for p in family if p not in gone and p.get("for_sibling") not in names]

def _older_sibling(family, make):
    sib = make("Sibling", "family", random.choice(["Male", "Female"]), closeness=55, age=random.randint(2, 6))
    sib["first_in_line"] = True
    family.append(sib)
    return sib

def f_royal2(family, make):
    _parents(family, ["Royal Family Member"], ["Royal Family Member"])
    _only_younger(family, keep=_older_sibling(family, make))

def f_royal1(family, make):
    _parents(family, ["Royal Family Member"], ["Royal Family Member"])
    _only_younger(family)

def _holder(family, key):
    pars = [p for p in family if p["relation"] in ("Mother", "Father")]
    return random.choice(pars) if pars else None

def f_noble(family, make):
    _parents(family, ["Landowner", "Company CEO"], ["Landowner"])
    _only_younger(family)

def f_poor(family, make):
    _parents(family, ["Cleaner", "Shop Assistant", "Waiter"], ["Cleaner", "Waiter"])

def f_tycoon(family, make):
    _parents(family, ["Company CEO", "Investment Banker", "Landowner"], ["Landowner", "Company CEO"])

def f_stars(family, make):
    _parents(family, ["Actor", "Singer", "Film Director", "Model"], ["Actor", "Singer"])

def f_sport(family, make):
    _parents(family, ["Footballer", "Basketball Player"], ["Footballer"])

def f_doctor(family, make):
    _parents(family, ["Surgeon", "Doctor"], ["Doctor", "Professor"])

def f_single(family, make):
    gone = random.choice(["Mother", "Father"])
    family[:] = [p for p in family if p["relation"] != gone]
    for p in family:
        if p["relation"] in ("Mother", "Father"):
            worldjobs.assign_job(p, worldjobs.BY_TITLE[random.choice(["Waiter", "Shop Assistant", "Cleaner", "Doctor"])])
            p["closeness"] = 80

SCENARIOS = [
    {"id": "normal", "name": "Ordinary life", "blurb": "A random family and random stats. You can re-roll the stats.", "stats": None, "family": None,
     "intro": ""},
    {"id": "royal2", "name": "The spare", "blurb": "Born royal and gifted, but second in line. Your older sibling gets the crown. What will you do with yours?",
     "stats": lambda: _stats(looks=82, social=84, academic=80, mental=78, wealth=95), "family": f_royal2,
     "intro": "Born into the royal family, second in line behind your older sibling.", "title": "prince"},
    {"id": "royal1", "name": "The reluctant heir", "blurb": "First in line to the throne, but born frail, shy and not very bright. The palace expects a lot.",
     "stats": lambda: _stats(physical=38, mental=34, social=36, academic=36, looks=45, athletic=35, wealth=95), "family": f_royal1,
     "intro": "Born first in line to the throne, with everyone watching.", "title": "prince", "heir_to": "king"},
    {"id": "noble", "name": "The noble heir", "blurb": "Eldest child of an old titled family. A grand estate, a title waiting for you, and a lot of rules.",
     "stats": lambda: _stats(looks=68, social=72, academic=65, mental=55, wealth=90), "family": f_noble,
     "intro": "Born into an old titled family, heir to the title.", "heir_to": "peer"},
    {"id": "blessed_poor", "name": "Gifted but poor", "blurb": "Brilliant, beautiful and athletic, in a family that can barely pay the rent.",
     "stats": lambda: _stats(physical=88, mental=82, social=80, academic=90, looks=88, athletic=84, wealth=15), "family": f_poor,
     "intro": "Born with every gift except money."},
    {"id": "tycoon", "name": "Tycoon's child", "blurb": "Rich parents, huge expectations. You are social and polished but the pressure shows.",
     "stats": lambda: _stats(mental=38, social=75, academic=60, looks=70, wealth=90), "family": f_tycoon,
     "intro": "Born into money and expectation."},
    {"id": "stars", "name": "Child of stars", "blurb": "Your parents are famous performers. Great looks and charm, weak at school.",
     "stats": lambda: _stats(looks=88, social=85, academic=35, athletic=45, wealth=80), "family": f_stars,
     "intro": "Your parents are famous. Everyone knows your name before you do."},
    {"id": "sport", "name": "Sports dynasty", "blurb": "Both parents are pro athletes. You are strong and fast, less so with books.",
     "stats": lambda: _stats(physical=88, athletic=90, academic=40, looks=65, wealth=75), "family": f_sport,
     "intro": "Born into a family of pro athletes."},
    {"id": "doctor", "name": "The doctors' kid", "blurb": "Clever and driven, but stressed and a bit lonely. Medicine is the family business.",
     "stats": lambda: _stats(academic=88, mental=40, social=38, athletic=40, wealth=70), "family": f_doctor,
     "intro": "Your parents are doctors, and they have plans for you."},
    {"id": "single", "name": "Single parent", "blurb": "One parent raising you, working long hours. Close, but money is tight.",
     "stats": None, "family": f_single, "intro": "Raised by one parent who gave you everything they had."},
    {"id": "underdog", "name": "Underdog (hard)", "blurb": "Weak stats and a poor family. Everything has to be earned.",
     "stats": lambda: _stats(physical=45, mental=42, social=38, academic=38, looks=35, athletic=36, wealth=10), "family": f_poor,
     "intro": "Nothing was handed to you."},
]
BY_ID = {s["id"]: s for s in SCENARIOS}

def pick_random():
    return random.choice(SCENARIOS)

async def scenario_screen(screen):
    """Returns a scenario dict (a random one if 'Surprise me' is picked)."""
    clock = pygame.time.Clock()
    bg = make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, (236, 228, 250), (255, 255, 255))
    rows = [{"id": "random", "name": "Surprise me", "blurb": "A random scenario, family and stats. You won't know until you start."}] + SCENARIOS
    sel = 1
    start = pygame.Rect(SCREEN_WIDTH // 2 - 130, 636, 260, 44)
    while True:
        mouse = pygame.mouse.get_pos()
        rects = [pygame.Rect(40, 86 + i * 41, 360, 37) for i in range(len(rows))]
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_DOWN:
                    sel = (sel + 1) % len(rows)
                elif e.key == pygame.K_UP:
                    sel = (sel - 1) % len(rows)
                elif e.key == pygame.K_RETURN:
                    return pick_random() if rows[sel]["id"] == "random" else rows[sel]
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(rects):
                    if r.collidepoint(e.pos):
                        sel = i
                if start.collidepoint(e.pos):
                    return pick_random() if rows[sel]["id"] == "random" else rows[sel]
        screen.blit(bg, (0, 0))
        draw_text(screen, "Choose your start", title_font, INK, SCREEN_WIDTH // 2, 40, centre=True)
        for i, (r, row) in enumerate(zip(rects, rows)):
            on = i == sel
            if on:
                draw_rounded_rect(screen, ACCENT, r, radius=10)
            draw_text(screen, row["name"], font, INK if on or r.collidepoint(mouse) else MUTED, r.x + 14, r.centery - 10)
        cur = rows[sel]
        draw_text(screen, cur["name"], title_font, INK, 440, 110)
        words = cur["blurb"].split()
        line, y = "", 160
        for w in words:
            if font.size(line + " " + w)[0] > 410:
                draw_text(screen, line, font, (70, 64, 85), 440, y)
                y += 28
                line = w
            else:
                line = (line + " " + w).strip()
        draw_text(screen, line, font, (70, 64, 85), 440, y)
        y += 50
        if cur["id"] not in ("random",):
            fam = {"normal": "Random", "royal2": "Royal family, older sibling first in line", "royal1": "Royal family, you are first in line",
                   "blessed_poor": "Low-paid parents, struggling", "tycoon": "Wealthy business parents", "stars": "Parents are performers",
                   "sport": "Parents are pro athletes", "doctor": "Parents are doctors", "single": "One parent",
                   "underdog": "Low-paid parents, struggling"}.get(cur["id"], "")
            draw_text(screen, "Family: " + fam, small_font, MUTED, 440, y)
            st = "Random, you can re-roll" if not cur.get("stats") else "Set by the scenario"
            draw_text(screen, "Stats: " + st, small_font, MUTED, 440, y + 24)
        draw_rounded_rect(screen, (255, 140, 50) if start.collidepoint(mouse) else (240, 120, 40), start, radius=12)
        draw_text(screen, "Start", font, WHITE, start.centerx, start.centery, centre=True)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)
