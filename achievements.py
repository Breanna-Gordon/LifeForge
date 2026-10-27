"""Achievements and a Belongings list, shown in the Journal tab."""
import pygame
from constants import OUTLINE, INK, MUTED
from constants import (WHITE, LIGHT_GREY, DARK_GREY, ACCENT, GREEN,
                       font, small_font, draw_text, draw_rounded_rect)
import shop

def _edu(c):
    return c.get("education", "None") not in ("None", "High School", "Secondary")

# (name, description, test(state, career, friends, partner, people))
ACHIEVEMENTS = [
    ("Straight A's",     "Academic 90+",                 lambda s, c, f, p, pe: s["stats"]["academic"] >= 90),
    ("Social Butterfly", "Have 6 friends",               lambda s, c, f, p, pe: len(f) >= 6),
    ("Best Friends",     "A friend with 90+ bond",       lambda s, c, f, p, pe: any(x["closeness"] >= 90 for x in f)),
    ("Saver",            "Hold $500",                    lambda s, c, f, p, pe: s["money"] >= 500),
    ("Rolling In It",    "Hold $2,000",                  lambda s, c, f, p, pe: s["money"] >= 2000),
    ("Tycoon",           "Hold $10,000",                 lambda s, c, f, p, pe: s["money"] >= 10000),
    ("Graduate",         "Earn a qualification",         lambda s, c, f, p, pe: _edu(c)),
    ("Homeowner",        "Own a home",                   lambda s, c, f, p, pe: bool(s.get("home"))),
    ("Behind the Wheel", "Get a driving licence",        lambda s, c, f, p, pe: "licence" in s.get("owned", ())),
    ("In Love",          "Have a partner",               lambda s, c, f, p, pe: p is not None),
    ("Married",          "Get married",                  lambda s, c, f, p, pe: bool(p and p.get("married"))),
    ("Parent",           "Have a child",                 lambda s, c, f, p, pe: any(x.get("is_child") for x in pe)),
    ("Pet Owner",        "Adopt a pet",                  lambda s, c, f, p, pe: bool(s.get("pets")) or "dog" in s.get("owned", ())),
    ("Famous",           "Reach 40 fame",                lambda s, c, f, p, pe: c.get("fame", 0) >= 40),
    ("Superstar",        "Reach 80 fame",                lambda s, c, f, p, pe: c.get("fame", 0) >= 80),
    ("Athlete",          "Athletic 85+",                 lambda s, c, f, p, pe: s["stats"]["athletic"] >= 85),
    ("Stunning",         "Looks 90+",                    lambda s, c, f, p, pe: s["stats"]["looks"] >= 90),
    ("Globetrotter",     "Take 3 holidays",              lambda s, c, f, p, pe: s.get("trips", 0) >= 3),
    ("Jailbird",         "Get a criminal record",        lambda s, c, f, p, pe: s.get("record", 0) > 0),
    ("Entrepreneur",     "Own a business",               lambda s, c, f, p, pe: bool(s.get("business"))),
    ("High Roller",      "Play the casino 5 times",      lambda s, c, f, p, pe: s.get("casino_plays", 0) >= 5),
    ("Jackpot",          "Win the lottery",              lambda s, c, f, p, pe: bool(s.get("lottery_won"))),
    ("Survivor",         "Reach age 75",                 lambda s, c, f, p, pe: s["age"] >= 75),
    ("Centenarian",      "Reach age 90",                 lambda s, c, f, p, pe: s["age"] >= 90),
    ("Dream Achieved",   "Fulfil your aspiration",       lambda s, c, f, p, pe: bool(s.get("aspiration_done"))),
    ("Climbing Ladder",  "Reach job level 3",            lambda s, c, f, p, pe: bool(c.get("job") and c["job"].get("level", 0) >= 3)),
    ("Heir",             "Inherit something",            lambda s, c, f, p, pe: any("inherit" in t.lower() for _, t in s.get("journal", ()))),
    ("Scholar",          "Win a scholarship",            lambda s, c, f, p, pe: bool(s.get("scholarship"))),
    ("Team Player",      "Join a sports team",           lambda s, c, f, p, pe: any(k in s.get("activities", {}) for k in ("football", "basket", "swim", "track", "rugby"))),
    ("Polyglot",         "Languages level 3",            lambda s, c, f, p, pe: s.get("skills", {}).get("languages", 0) >= 3),
    ("Musician",         "Music or singing level 3",     lambda s, c, f, p, pe: max(s.get("skills", {}).get("music", 0), s.get("skills", {}).get("singing", 0)) >= 3),
    ("Investor",         "Invest some money",            lambda s, c, f, p, pe: s.get("invest", 0) > 0),
    ("Freelancer",       "Finish 10 freelance gigs",     lambda s, c, f, p, pe: s.get("gigs_done", 0) >= 10),
    ("Makeover",         "Have plastic surgery",         lambda s, c, f, p, pe: s.get("surgeries", 0) > 0),
    ("Private Student",  "Go to a private school",       lambda s, c, f, p, pe: bool(s.get("private_school"))),
]

def check_achievements(state, career, friends, partner, people, log):
    got = state.setdefault("achievements", [])
    for name, desc, test in ACHIEVEMENTS:
        if name in got:
            continue
        try:
            ok = bool(test(state, career, friends, partner, people))
        except Exception:
            ok = False
        if ok:
            got.append(name)
            state["stats"]["mental"] = min(100, state["stats"]["mental"] + 1)
            log(f"Achievement unlocked: {name}!")

def view_buttons(rect):
    out, x = {}, rect.right
    for key, label, w in reversed([("log", "Log", 60), ("awards", "Achievements", 120), ("stuff", "Belongings", 100)]):
        x -= w
        out[key] = (pygame.Rect(x, rect.y - 2, w, 24), label)
        x -= 4
    return out

def draw_view_toggle(screen, rect, mouse_pos, current):
    for key, (r, label) in view_buttons(rect).items():
        draw_rounded_rect(screen, ACCENT if key == current else (WHITE if not r.collidepoint(mouse_pos) else (235, 235, 240)), r, radius=8)
        pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
        draw_text(screen, label, small_font, INK, r.centerx, r.centery, centre=True)

def handle_toggle_click(mx, my, rect, state):
    for key, (r, _) in view_buttons(rect).items():
        if r.collidepoint(mx, my):
            state["_jview"] = key
            return True
    return False

def draw_awards(screen, rect, state, scroll=0):
    got = set(state.get("achievements", []))
    draw_text(screen, f"Achievements ({len(got)}/{len(ACHIEVEMENTS)})", font, INK, rect.x, rect.y)
    cols = 3
    col_w = (rect.width - 12 * (cols - 1)) // cols
    rows_vis = 7
    row_h = 38
    total_rows = (len(ACHIEVEMENTS) + cols - 1) // cols
    scroll = max(0, min(scroll, total_rows - rows_vis))
    for n, (name, desc, _) in enumerate(ACHIEVEMENTS):
        col, row = n % cols, n // cols - scroll
        if row < 0 or row >= rows_vis:
            continue
        r = pygame.Rect(rect.x + col * (col_w + 12), rect.y + 28 + row * (row_h + 2), col_w, row_h)
        have = name in got
        draw_rounded_rect(screen, (255, 244, 205) if have else LIGHT_GREY, r, radius=8)
        pygame.draw.rect(screen, (214, 170, 60) if have else OUTLINE, r, 2, border_radius=8)
        pygame.draw.circle(screen, (232, 183, 60) if have else (200, 200, 205), (r.x + 18, r.centery), 9)
        draw_text(screen, name, small_font, INK if have else MUTED, r.x + 34, r.y + 3)
        draw_text(screen, desc, small_font, DARK_GREY, r.x + 34, r.y + 20)
    if total_rows > rows_vis:
        draw_text(screen, "Scroll for more", small_font, DARK_GREY, rect.x + 200, rect.y + 2)
    return scroll

def belongings(state):
    lines = []
    by_id = {i["id"]: i for i in shop.ITEMS}
    for iid in sorted(state.get("owned", ())):
        it = by_id.get(iid)
        if it and it.get("perm"):
            lines.append((it["name"], it.get("note", "")))
    h = state.get("home")
    if h:
        lines.append(("Home", f"Worth about ${h.get('value', 0) if isinstance(h, dict) else h}"))
    for p in state.get("pets", []):
        lines.append((f"{p['name']} the {p['kind']}", f"{p['age']} years old"))
    b = state.get("business")
    if b:
        lines.append((f"{b['name']} business", f"Owned {b['years']} years"))
    if state.get("private_school"):
        lines.append(("Private school place", "+1 Academic a year"))
    if state.get("record"):
        lines.append(("Criminal record", f"{state['record']} offence(s)"))
    return lines

def draw_belongings(screen, rect, state):
    draw_text(screen, "Belongings", font, INK, rect.x, rect.y)
    box = pygame.Rect(rect.x, rect.y + 28, rect.width, rect.height - 32)
    draw_rounded_rect(screen, WHITE, box, radius=8)
    pygame.draw.rect(screen, OUTLINE, box, 2, border_radius=8)
    lines = belongings(state)
    if not lines:
        draw_text(screen, "Nothing yet. Buy things in the Shop or adopt a pet.", small_font, DARK_GREY, box.x + 12, box.y + 10)
    for n, (a, b) in enumerate(lines[:12]):
        y = box.y + 8 + n * 22
        draw_text(screen, a, small_font, INK, box.x + 12, y)
        draw_text(screen, b, small_font, DARK_GREY, box.x + 240, y)
