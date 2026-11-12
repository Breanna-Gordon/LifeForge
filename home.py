"""The Life tab's lower half: life at a glance (key people), goals, and a feed
of what just happened with the stat changes. Also the cost chips on event
choices and the little feeling line after you choose."""
import pygame
from constants import (fmt, INK, MUTED, WHITE, ACCENT, GREEN, RED, DARK_GREY, OUTLINE, STAT_LABELS,
                       font, small_font, draw_text, draw_rounded_rect)
from avatar import draw_avatar

_TINY = pygame.font.Font(None, 17)
TRACK = (226, 222, 234)
NAMES = {"physical": "Health", "mental": "Mental", "social": "Social", "academic": "Academic", "looks": "Looks",
         "athletic": "Athletic", "wealth": "Wealth"}

# ------------------------------------------------------------------ feed
def feed_add(state, text, delta=""):
    f = state.setdefault("feed", [])
    f.append([state.get("age", 0), text, delta])
    del f[:-40]

def chips(state, consequence):
    """Short list of (text, colour) for an option's visible effects."""
    if "gamble" in consequence:
        return [("Risky", MUTED)]
    out = []
    age = state.get("age", 0)
    for k, v in consequence.items():
        if k == "money" and v:
            if age < 18:
                continue
            amt = int(v * max(2, state.get("_income", 0) // 2000))
            out.append((("+" if amt > 0 else "-") + "$" + fmt(abs(amt)), GREEN if amt > 0 else RED))
        elif k in NAMES and v:
            out.append((f"{NAMES[k]} {v:+d}", GREEN if v > 0 else RED))
        elif k == "skill" and v:
            out.append(("Skill up", GREEN))
        elif k == "new_enemy":
            out.append(("Makes a rival", RED))
    return out[:3]

def feeling(outcome):
    up = sum(v for k, v in outcome.items() if k in NAMES and isinstance(v, (int, float)) and v > 0)
    down = sum(-v for k, v in outcome.items() if k in NAMES and isinstance(v, (int, float)) and v < 0)
    mental = outcome.get("mental", 0) if isinstance(outcome.get("mental", 0), (int, float)) else 0
    if mental >= 2:
        return "You feel a little happier for it."
    if mental <= -2:
        return "That weighs on you for a while."
    if up > down + 2:
        return "That went well."
    if down > up + 2:
        return "That cost you."
    return "Life goes on."

# ----------------------------------------------------------------- goals
def goals(state, career, partner, people, friends, aspirations):
    stats = state["stats"]
    age = state["age"]
    out = []
    asp = state.get("aspiration")
    if asp in aspirations:
        desc = aspirations[asp][0]
        kids = len([p for p in people if p.get("is_child")])
        sk = state.get("skills", {})
        prog = {"Wealthy": state["money"] / 100000, "Family-minded": kids / 2, "Scholar": stats["academic"] / 80,
                "Athlete": stats["athletic"] / 80, "Social butterfly": min(len(friends) / 4, stats["social"] / 70),
                "Soulmate": 1.0 if (partner and partner.get("married")) else (0.5 if partner else 0.0),
                "Performer": max([sk.get(k, 0) for k in ("singing", "music", "dance")] + [0]) / 4}.get(asp, 0)
        if state.get("aspiration_done"):
            prog = 1.0
        out.append((asp + ": " + desc, min(1.0, prog), "done" if prog >= 1 else f"{int(min(1, prog) * 100)}%"))
    net = state["money"] + state.get("savings", 0) + state.get("invest", 0) - state.get("debt", 0)
    tgt = next((t for t in (1000, 5000, 20000, 100000, 500000, 1000000, 5000000, 20000000) if t > net), 100000000)
    out.append((f"Be worth ${fmt(tgt)}", max(0.0, min(1.0, net / tgt)), f"${fmt(max(0, net))}"))
    if age < 18:
        out.append(("Finish school", age / 18, f"{age} / 18"))
    elif career.get("enrolled"):
        import education as ED
        dur = ED.UNI_DURATION.get(career.get("uni_target"), 3)
        out.append((f"Finish your {career.get('uni_target')}", career.get("uni_years_done", 0) / dur, f"{career.get('uni_years_done', 0)} / {dur}"))
    elif career.get("job"):
        j = career["job"]
        out.append((f"Get promoted: {j['title']}", min(1.0, j.get("perf", 55) / 62), f"{int(min(100, j.get('perf', 55)))}%"))
    else:
        out.append(("Find a job or go to university", 0.0, "0%"))
    kids = len([p for p in people if p.get("is_child")])
    if not partner:
        out.append(("Find someone to love", 0.0, "single"))
    elif not partner.get("married"):
        out.append(("Get married", 0.5, "together"))
    elif not kids:
        out.append(("Start a family", 0.5, "married"))
    else:
        out.append(("Raise your family", min(1.0, kids / 3), f"{kids} child{'ren' if kids != 1 else ''}"))
    return out[:4]

# ------------------------------------------------------------------ draw
def _bar(screen, rect, frac, col):
    pygame.draw.rect(screen, TRACK, rect, border_radius=rect.h // 2)
    if frac > 0:
        pygame.draw.rect(screen, col, (rect.x, rect.y, max(rect.h, int(rect.w * min(1, frac))), rect.h), border_radius=rect.h // 2)

def _trim(text, fnt, width):
    if fnt.size(text)[0] <= width:
        return text
    while len(text) > 1 and fnt.size(text + "...")[0] > width:
        text = text[:-1]
    return text + "..."

def key_people(people, friends, partner):
    out = []
    if partner:
        out.append((partner, "Spouse" if partner.get("married") else "Partner"))
    mum = next((p for p in people if p["relation"] == "Mother"), None)
    dad = next((p for p in people if p["relation"] == "Father"), None)
    for p in (mum, dad):
        if p:
            out.append((p, "Mum" if p is mum else "Dad"))
    kids = sorted([p for p in people if p.get("is_child")], key=lambda q: -q.get("age", 0))
    for k in kids[:2]:
        out.append((k, "Child"))
    fr = sorted([f for f in friends if f.get("category") != "enemy"], key=lambda q: -q["closeness"])
    for f in fr[:2]:
        out.append((f, "Friend"))
    sib = [p for p in people if "Sibling" in p["relation"] or p["relation"] in ("Brother", "Sister")]
    if sib:
        out.append((sib[0], "Sibling"))
    en = [f for f in friends if f.get("category") == "enemy"]
    if en:
        out.append((max(en, key=lambda q: q.get("conflict", 0)), "Rival"))
    return out[:6]

def draw_glance(screen, rect, state, career, people, friends, partner, mouse, aspirations, y0):
    """Returns {"surrender": rect, "people": [(person, rect)]}."""
    regions = {"people": []}
    traits = ", ".join(state.get("player_traits", []))
    draw_text(screen, "LIFE AT A GLANCE", small_font, MUTED, rect.x + 8, y0)
    if traits:
        draw_text(screen, traits.capitalize(), _TINY, MUTED, rect.x + 168, y0 + 3)
    sur = pygame.Rect(rect.right - 124, y0 - 3, 120, 22)
    if state.get("_surrender_ask"):
        draw_text(screen, "End this life?", small_font, RED, rect.right - 250, y0)
        yes, no = pygame.Rect(rect.right - 124, y0 - 3, 56, 22), pygame.Rect(rect.right - 62, y0 - 3, 56, 22)
        for r, lab in ((yes, "Yes"), (no, "No")):
            draw_rounded_rect(screen, ACCENT if r.collidepoint(mouse) else (240, 236, 246), r, radius=9)
            draw_text(screen, lab, small_font, INK, r.centerx, r.centery, centre=True)
        regions["sur_yes"], regions["sur_no"] = yes, no
    else:
        draw_text(screen, "Give up this life", small_font, (200, 110, 110) if sur.collidepoint(mouse) else MUTED, sur.centerx, sur.centery, centre=True)
        regions["surrender"] = sur
    kp = key_people(people, friends, partner)
    cw = rect.width // 6
    for i, (p, tag) in enumerate(kp):
        cx = rect.x + cw * i + cw // 2
        lk = p.get("look") or {}
        if lk:
            ar = pygame.Rect(cx - 24, y0 + 22, 48, 48)
            draw_avatar(screen, ar, p["gender"], tuple(lk["hair"]), lk["style"], tuple(lk["skin"]), lk.get("facial", "None"), p.get("age", 30), 60, lk.get("feat"))
        draw_text(screen, _trim(p["name"].split()[0], _TINY, cw - 8), _TINY, INK, cx, y0 + 76, centre=True)
        draw_text(screen, f"{tag} · {p.get('age', '?')}", _TINY, MUTED, cx, y0 + 90, centre=True)
        c = p.get("closeness", 50)
        col = (225, 85, 90) if tag == "Rival" else (88, 190, 130) if c >= 60 else (240, 180, 70) if c >= 35 else (225, 85, 90)
        _bar(screen, pygame.Rect(cx - 28, y0 + 105, 56, 5), (p.get("conflict", 50) if tag == "Rival" else c) / 100, col)
        regions["people"].append((p, pygame.Rect(cx - cw // 2, y0 + 18, cw, 96)))
    if not kp:
        draw_text(screen, "Meet people in the People tab.", small_font, MUTED, rect.x + 8, y0 + 40)
    y1 = y0 + 128
    draw_text(screen, "GOALS", small_font, MUTED, rect.x + 8, y1)
    draw_text(screen, "RECENT", small_font, MUTED, rect.x + 360, y1)
    gy = y1 + 22
    for label, frac, right in goals(state, career, partner, people, friends, aspirations):
        draw_text(screen, _trim(label, _TINY, 250), _TINY, INK, rect.x + 8, gy)
        draw_text(screen, right, _TINY, MUTED, rect.x + 332 - _TINY.size(right)[0], gy)
        _bar(screen, pygame.Rect(rect.x + 8, gy + 15, 324, 6), frac, (88, 190, 130) if frac < 1 else (240, 180, 70))
        gy += 32
    fy = y1 + 22
    feed = state.get("feed", [])[-4:]
    if not feed:
        draw_text(screen, "Your choices will show up here.", _TINY, MUTED, rect.x + 360, fy)
    for age, text, delta in reversed(feed):
        draw_text(screen, _trim(text, _TINY, 300), _TINY, INK, rect.x + 360, fy)
        if delta:
            first = delta.split(",")[0]
            dcol = RED if first.startswith("-") or " -" in first else GREEN
            draw_text(screen, _trim(delta, _TINY, 300), _TINY, dcol, rect.x + 360, fy + 13)
        else:
            draw_text(screen, f"age {age}", _TINY, MUTED, rect.x + 360, fy + 13)
        fy += 32
    return regions
