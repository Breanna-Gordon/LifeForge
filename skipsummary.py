"""What happened while you skipped ahead: a plain summary of the years."""
import pygame
import asyncio
from constants import fmt, INK, MUTED, WHITE, ACCENT, GREEN, RED, DARK_GREY, OUTLINE
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, font, small_font, title_font, draw_text, draw_rounded_rect

KEYWORDS = ("Promoted", "Graduated", "married", "Married", "Welcomed", "Adopted", "retired", "laid off", "let go", "passed away",
            "moved", "Moved", "bought", "Bought", "Inherited", "inherited", "started", "Started", "divorce", "broke up",
            "born", "knighted", "Knighted", "title", "Title", "found work", "changed careers", "baby", "IVF", "raise")

def snapshot(state, career, people, friends, partner, stats):
    from people import children_of
    job = career["job"]
    return {"age": state["age"], "money": state["money"], "savings": state.get("savings", 0),
            "debt": state.get("debt", 0), "invest": state.get("invest", 0),
            "job": f"{job['title']} (${fmt(job['pay'])})" if job else "No job",
            "edu": (f"Studying {career['uni_target']} (year {career['uni_years_done'] + 1})" if career["enrolled"]
                    else ("In school" if state["age"] < 18 and career["education"] == "None" else career["education"])),
            "partner": (partner["name"] + (" (spouse)" if partner.get("married") else "")) if partner else "Single",
            "kids": len(children_of(people)), "friends": len(friends), "stats": dict(stats),
            "journal_len": len(state["journal"])}

def highlights(state, before):
    entries = state["journal"][before["journal_len"]:]
    skip = ("Skipped ahead", "School report", "Stopped skipping")
    entries = [e for e in entries if not any(e[1].startswith(s) for s in skip)]
    key = [e for e in entries if any(k in e[1] for k in KEYWORDS)]
    rest = [e for e in entries if e not in key]
    out = key[:8]
    out += rest[:max(0, 8 - len(out))]
    out.sort(key=lambda e: e[0])
    return out

def _delta(a, b, money=True):
    d = b - a
    if d == 0:
        return "no change", MUTED
    s = ("+" if d > 0 else "-") + ("$" if money else "") + fmt(abs(d))
    return s, (GREEN if d > 0 else RED)

def _debt(a, b):
    d = b - a
    if d == 0:
        return "no change", MUTED
    return ("+" if d > 0 else "-") + "$" + fmt(abs(d)), (RED if d > 0 else GREEN)

async def show(screen, before, after, lines):
    clock = pygame.time.Clock()
    bg = screen.copy()
    dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    dim.fill((20, 22, 34, 205))
    panel = pygame.Rect(90, 36, SCREEN_WIDTH - 180, SCREEN_HEIGHT - 72)
    btn = pygame.Rect(panel.centerx - 90, panel.bottom - 54, 180, 38)
    years = after["age"] - before["age"]
    while True:
        mouse = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                return
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and btn.collidepoint(ev.pos):
                return
        screen.blit(bg, (0, 0))
        screen.blit(dim, (0, 0))
        draw_rounded_rect(screen, (250, 247, 240), panel, radius=18)
        draw_text(screen, f"Ages {before['age']} to {after['age']}  ({years} year{'s' if years != 1 else ''} passed)",
                  title_font, INK, panel.x + 28, panel.y + 18)
        y = panel.y + 74
        rows = [("Money", f"${fmt(before['money'])} to ${fmt(after['money'])}", *_delta(before["money"], after["money"])),
                ("Savings", f"${fmt(before['savings'])} to ${fmt(after['savings'])}", *_delta(before["savings"], after["savings"])),
                ("Investments", f"${fmt(before['invest'])} to ${fmt(after['invest'])}", *_delta(before["invest"], after["invest"])),
                ("Debt", f"${fmt(before['debt'])} to ${fmt(after['debt'])}", *_debt(before["debt"], after["debt"])),
                ("Job", f"{before['job']}  to  {after['job']}", "", MUTED),
                ("Education", f"{before['edu']}  to  {after['edu']}", "", MUTED),
                ("Partner", f"{before['partner']}  to  {after['partner']}", "", MUTED),
                ("Children / friends", f"{before['kids']} / {before['friends']}  to  {after['kids']} / {after['friends']}", "", MUTED)]
        for label, text, delta, col in rows:
            draw_text(screen, label, small_font, DARK_GREY, panel.x + 28, y)
            draw_text(screen, text, small_font, INK, panel.x + 170, y)
            if delta:
                draw_text(screen, delta, small_font, col, panel.right - 28 - small_font.size(delta)[0], y)
            y += 24
        # stat changes
        y += 6
        draw_text(screen, "How you changed", small_font, DARK_GREY, panel.x + 28, y)
        x = panel.x + 150
        names = {"physical": "Health", "mental": "Mental", "social": "Social", "academic": "Academic",
                 "looks": "Looks", "athletic": "Athletic", "wealth": "Wealth"}
        for k, nm in names.items():
            d = after["stats"][k] - before["stats"][k]
            t = f"{nm} {d:+d}"
            col = GREEN if d > 0 else RED if d < 0 else MUTED
            draw_text(screen, t, small_font, col, x, y)
            x += small_font.size(t)[0] + 9
        y += 34
        draw_text(screen, "What happened", small_font, DARK_GREY, panel.x + 28, y)
        y += 24
        for age, text in lines:
            t = text if len(text) < 88 else text[:85] + "..."
            draw_text(screen, f"{age}", small_font, ACCENT, panel.x + 28, y)
            draw_text(screen, t, small_font, INK, panel.x + 66, y)
            y += 22
        hov = btn.collidepoint(mouse)
        draw_rounded_rect(screen, ACCENT if hov else (230, 226, 216), btn, radius=12)
        draw_text(screen, "Continue", font, INK, btn.centerx, btn.centery, centre=True)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)
