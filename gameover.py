"""The end of a life: obituary, final stats, ribbons and a short life in brief."""
import asyncio
import random
import pygame
from constants import (fmt, SCREEN_WIDTH, SCREEN_HEIGHT, STAT_ORDER, STAT_LABELS, STAT_COLORS, ACCENT, GREEN, RED,
                       font, small_font, title_font, draw_text, draw_rounded_rect, make_vertical_gradient)
from avatar import draw_avatar
import achievements

TXT = (240, 234, 252)
SOFT = (176, 166, 210)
PANEL = (255, 255, 255, 14)
_TINY = pygame.font.Font(None, 18)
BIG = pygame.font.Font(None, 56)

# a funny line for every ribbon (falls back to the plain description)
FUNNY = {
    "Straight A's": "Teachers wept. Parents framed the report card.",
    "Social Butterfly": "You had more friends than birthdays to remember.",
    "Best Friends": "One person would have helped you move house.",
    "Saver": "You kept money for a rainy day, and it rained.",
    "Rolling In It": "Pockets finally heavier than your worries.",
    "Tycoon": "You stopped checking prices on menus.",
    "Graduate": "A piece of paper that says you can sit still.",
    "Homeowner": "Your name is on the deed. The bank's is bigger.",
    "Behind the Wheel": "You passed the test. Pedestrians stayed nervous.",
    "In Love": "Somebody saw your whole mess and stayed.",
    "Married": "A ring, a cake, and a very long group chat.",
    "Parent": "You now own a tiny, loud, brilliant person.",
    "Pet Owner": "Unconditional love, shed all over the sofa.",
    "Famous": "Strangers knew your name and got it slightly wrong.",
    "Superstar": "You could not buy milk in peace.",
    "Athlete": "Your legs filed a complaint. You ignored it.",
    "Stunning": "Mirrors asked for your autograph.",
    "Globetrotter": "Three holidays and a suitcase that never fully unpacked.",
    "Jailbird": "You have seen the inside of a cell. The food was fine.",
    "Entrepreneur": "You bet on yourself. Sometimes it paid.",
    "High Roller": "The house always wins. You enjoyed losing anyway.",
    "Jackpot": "The lottery noticed you for once.",
    "Survivor": "You outlasted most of your group chat.",
    "Centenarian": "You saw the whole century and had notes.",
    "Dream Achieved": "The thing you wanted at the start, you actually did.",
    "Climbing Ladder": "Promoted past the person who said you wouldn't be.",
    "Heir": "Somebody left you something, and a letter.",
    "Scholar": "They paid you to learn. Suspicious, but good.",
    "Team Player": "You passed the ball, mostly to the right team.",
    "Polyglot": "You can be rude in three languages.",
    "Musician": "The neighbours know every song you learned.",
    "Investor": "Your money got a job.",
    "Freelancer": "Ten gigs, zero holidays, one very good invoice template.",
    "Makeover": "New face, same chaos.",
    "Mogul": "A million-dollar business. Your accountant smiled.",
    "Empire": "Three businesses, one sleepless person.",
    "Going Public": "Strangers now own a tiny piece of your dream.",
    "Grandparent": "Spoiled them, then handed them back.",
    "Philanthropist": "You gave it away on purpose.",
    "Dynasty": "Your story did not end with you.",
    "Private Student": "Blazers, bells and a lot of expectations.",
}

def obituary(ctx):
    st, career, name, age = ctx["state"], ctx["career"], ctx["name"], ctx["age"]
    people, friends, partner = ctx["people"], ctx["friends"], ctx["partner"]
    kids = [p for p in people if p.get("is_child")]
    edu = career.get("education", "None")
    job = career.get("job")
    net = st.get("money", 0) + st.get("savings", 0) + st.get("invest", 0) - st.get("debt", 0)
    L = [f"{name} was born into a {st.get('family_wealth', 'comfortable').lower()} family and died aged {age}."]
    if age < 18:
        L.append("They never finished school. There was so much left to try.")
    elif edu in ("None", "High School"):
        L.append("They were a high school graduate with plenty of street sense.")
    else:
        L.append(f"They earned a {edu}" + (f" in {career['course']}." if career.get("course") else "."))
    if job:
        L.append(f"They finished as a {job['title']}.")
    elif age >= 30:
        L.append("Their relationship with employment was... complicated.")
    L.append(f"They left behind a net worth of ${fmt(max(0, net))}." if net > 0 else "They left behind more debts than assets.")
    if partner and partner.get("married"):
        L.append(f"They were married to {partner['name']}.")
    elif partner:
        L.append(f"They were with {partner['name']} at the end.")
    else:
        L.append("They went through life single, on their own terms.")
    L.append(f"They had {len(kids)} child{'ren' if len(kids) != 1 else ''}." if kids else "They never had children.")
    if st.get("record", 0) > 0:
        L.append("Their criminal record was not short.")
    if st.get("aspiration_done"):
        L.append(f"They achieved their dream: {st['aspiration']}.")
    return L

def quip(ctx):
    st = ctx["state"]
    if ctx["reason"].startswith("You gave up"):
        return "They walked away from it all. The story, at least, was theirs."
    if st.get("record", 0) > 2:
        return "The obituary committee chose to focus on other aspects of this person's life."
    if ctx["life_score"] > 700:
        return "A life people will tell stories about."
    if ctx["age"] < 30:
        return "Gone far too soon. The world is cruel."
    return "A life with plenty of chapters."

def _tile(S, x, y, w, title, text, col=ACCENT):
    h = 92
    pygame.draw.rect(S, (255, 255, 255, 16), (x, y, w, h), border_radius=12)
    pygame.draw.rect(S, col, (x, y + 14, 4, h - 28), border_radius=2)
    draw_text(S, title, font, TXT, x + 16, y + 10)
    words, line, yy = text.split(), "", y + 38
    for wd in words:
        if _TINY.size(line + " " + wd)[0] > w - 28:
            draw_text(S, line, _TINY, SOFT, x + 16, yy)
            yy += 15
            line = wd
        else:
            line = (line + " " + wd).strip()
    draw_text(S, line, _TINY, SOFT, x + 16, yy)

def build(ctx):
    """Draws the whole page on one tall surface."""
    W = SCREEN_WIDTH
    st = ctx["state"]
    got = [n for n in st.get("achievements", [])]
    desc = {n: d for n, d, _ in achievements.ACHIEVEMENTS}
    rows = (len(got) + 2) // 3
    H = 880 + rows * 102
    S = pygame.Surface((W, H), pygame.SRCALPHA)
    lk = ctx["look"]
    # header
    draw_avatar(S, pygame.Rect(40, 36, 150, 190), ctx["gender"], tuple(lk["hair"]), lk["style"], tuple(lk["skin"]), lk["facial"], ctx["age"], 30, lk.get("feat"))
    draw_text(S, "GAME OVER", _TINY, ACCENT, 220, 44)
    draw_text(S, ctx["name"], BIG, TXT, 220, 62)
    draw_text(S, f"Died aged {ctx['age']}  ·  {ctx['reason']}", font, SOFT, 220, 122)
    draw_text(S, f"Life score  {ctx['life_score']}", title_font, (255, 206, 120), 220, 160)
    if st.get("generation", 1) > 1:
        draw_text(S, f"Generation {st['generation']} of the family", _TINY, SOFT, 220, 205)
    # obituary
    y = 250
    draw_text(S, "OBITUARY", _TINY, SOFT, 40, y)
    pygame.draw.rect(S, (255, 255, 255, 14), (30, y + 20, 520, 250), border_radius=14)
    yy = y + 36
    for line in obituary(ctx):
        draw_text(S, line, small_font, TXT, 50, yy)
        yy += 24
    draw_text(S, quip(ctx), _TINY, SOFT, 50, y + 252)
    # final stats
    draw_text(S, "FINAL STATS", _TINY, SOFT, 580, y)
    pygame.draw.rect(S, (255, 255, 255, 14), (570, y + 20, 290, 250), border_radius=14)
    yy = y + 34
    for k in STAT_ORDER:
        v = int(ctx["stats"][k])
        draw_text(S, STAT_LABELS[k], _TINY, TXT, 586, yy)
        draw_text(S, str(v), _TINY, STAT_COLORS[k], 836 - _TINY.size(str(v))[0], yy)
        pygame.draw.rect(S, (255, 255, 255, 30), (586, yy + 15, 250, 5), border_radius=3)
        pygame.draw.rect(S, STAT_COLORS[k], (586, yy + 15, max(5, int(250 * v / 100)), 5), border_radius=3)
        yy += 30
    # ribbons
    ry = y + 300
    draw_text(S, f"RIBBONS & ACHIEVEMENTS  ({len(got)})", _TINY, SOFT, 40, ry)
    cols = ((110, 150, 240), (180, 120, 230), (150, 150, 180), (90, 200, 170), (240, 140, 110))
    if not got:
        draw_text(S, "No ribbons this time. Next life.", small_font, SOFT, 40, ry + 28)
    for i, n in enumerate(got):
        x, yy = 40 + (i % 3) * 280, ry + 24 + (i // 3) * 102
        _tile(S, x, yy, 268, n, FUNNY.get(n) or desc.get(n, ""), cols[i % 5])
    # life in brief
    by = ry + 34 + rows * 102 + 18
    draw_text(S, "LIFE IN BRIEF", _TINY, SOFT, 40, by)
    pygame.draw.rect(S, (255, 255, 255, 14), (30, by + 20, 830, 230), border_radius=14)
    yy = by + 32
    for a, t in st.get("journal", [])[-8:]:
        draw_text(S, f"Age {a}", _TINY, ACCENT, 50, yy)
        draw_text(S, t if len(t) < 100 else t[:97] + "...", _TINY, TXT, 110, yy)
        yy += 24
    return S, by + 270

async def show(screen, ctx):
    clock = pygame.time.Clock()
    page, h = build(ctx)
    bg = make_vertical_gradient(SCREEN_WIDTH, SCREEN_HEIGHT, (44, 36, 86), (18, 16, 44))
    rnd = random.Random(5)
    for _ in range(60):
        pygame.draw.circle(bg, (255, 255, 255), (rnd.randint(0, SCREEN_WIDTH), rnd.randint(0, SCREEN_HEIGHT)), rnd.choice((1, 1, 2)))
    scroll = 0
    maxs = max(0, h - SCREEN_HEIGHT + 70)
    btn = pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT - 56, 220, 40)
    while True:
        mouse = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEWHEEL:
                scroll = max(0, min(maxs, scroll - ev.y * 50))
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    return
                if ev.key == pygame.K_DOWN:
                    scroll = min(maxs, scroll + 50)
                if ev.key == pygame.K_UP:
                    scroll = max(0, scroll - 50)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and btn.collidepoint(ev.pos):
                return
        screen.blit(bg, (0, 0))
        screen.blit(page, (0, -scroll))
        shade = pygame.Surface((SCREEN_WIDTH, 70), pygame.SRCALPHA)
        shade.fill((18, 16, 44, 235))
        screen.blit(shade, (0, SCREEN_HEIGHT - 70))
        draw_rounded_rect(screen, ACCENT if btn.collidepoint(mouse) else (240, 130, 50), btn, radius=14)
        draw_text(screen, "Continue", font, (255, 255, 255), btn.centerx, btn.centery, centre=True)
        if maxs:
            draw_text(screen, "scroll for more", _TINY, SOFT, 14, SCREEN_HEIGHT - 28)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)
