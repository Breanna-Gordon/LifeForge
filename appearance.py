"""The look editor: used on the character creation screen and, mid-game, in a
window you open by clicking your portrait. No boxes, just labels and swatches."""
import asyncio
import pygame
from constants import (SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, ACCENT, INK, MUTED, OUTLINE, SKIN_TONES,
                       font, small_font, title_font, draw_text, draw_rounded_rect)
from avatar import draw_avatar, EYE_COLOURS, EYE_SHAPES, LIP_STYLES, BROW_STYLES, OUTFITS

HAIR_STYLES_M = ["Bald", "Buzzcut", "Short", "Undercut", "Spiky", "Mohawk", "Curly", "Afro", "Long", "Ponytail", "Bun", "Bob"]
HAIR_STYLES_F = ["Long", "Ponytail", "Bun", "Bob", "Curly", "Afro", "Short", "Undercut", "Spiky", "Buzzcut", "Mohawk", "Bald"]
FACIAL = ["None", "Stubble", "Moustache", "Goatee", "Beard", "Handlebar"]
HAIR_COLOURS = [("Black", (25, 22, 22)), ("Dark brown", (60, 40, 30)), ("Brown", (96, 62, 38)), ("Chestnut", (120, 72, 40)),
                ("Auburn", (150, 55, 32)), ("Ginger", (195, 90, 40)), ("Dark blonde", (170, 128, 60)), ("Blonde", (222, 190, 110)),
                ("Platinum", (238, 228, 200)), ("Grey", (160, 160, 165)), ("White", (240, 240, 245)), ("Pink", (232, 120, 170)),
                ("Blue", (60, 110, 200)), ("Teal", (50, 170, 160)), ("Purple", (130, 80, 190)), ("Green", (70, 160, 90))]
TABS = ["Hair", "Face", "Style"]

def default_look(gender="Female"):
    return {"hair": (60, 40, 30), "style": "Long" if gender == "Female" else "Short", "skin": SKIN_TONES[2],
            "facial": "None", "feat": {"eyes": "Brown", "eye_shape": "Almond", "lips": "Natural", "brows": "Natural", "outfit": None}}

def feat_of(look):
    f = look.get("feat") or {}
    return {k: v for k, v in f.items() if v is not None}

def _label(screen, text, x, y):
    draw_text(screen, text, small_font, MUTED, x, y)

def _chips(screen, hits, kind, items, sel, x, y, w, mouse, per_row=5, cw=84, ch=24):
    for n, it in enumerate(items):
        r = pygame.Rect(x + (n % per_row) * (cw + 4), y + (n // per_row) * (ch + 4), cw, ch)
        on = it == sel
        hov = r.collidepoint(mouse)
        if on:
            draw_rounded_rect(screen, ACCENT, r, radius=8)
        elif hov:
            pygame.draw.rect(screen, (225, 218, 235), r, border_radius=8)
        draw_text(screen, it, small_font, INK if (on or hov) else (90, 84, 105), r.centerx, r.centery, centre=True)
        hits.append((kind, it, r))
    rows = -(-len(items) // per_row)
    return y + rows * (ch + 4)

def _swatches(screen, hits, kind, items, sel, x, y, mouse, per_row=8, size=26):
    for n, (name, col) in enumerate(items):
        cx_ = x + (n % per_row) * (size + 8) + size // 2
        cy_ = y + (n // per_row) * (size + 8) + size // 2
        r = pygame.Rect(cx_ - size // 2, cy_ - size // 2, size, size)
        pygame.draw.circle(screen, col, (cx_, cy_), size // 2)
        on = name == sel
        pygame.draw.circle(screen, ACCENT if on else (120, 112, 135), (cx_, cy_), size // 2 + (2 if on else 0), 3 if on else 1)
        hits.append((kind, name, r))
    rows = -(-len(items) // per_row)
    return y + rows * (size + 8)

def draw_editor(screen, rect, mouse, look, gender, ed):
    """Draws the options for the current tab; returns hit rects."""
    hits = []
    tx = rect.x
    for i, name in enumerate(TABS):
        r = pygame.Rect(tx, rect.y, 70, 26)
        on = ed["tab"] == i
        draw_text(screen, name, font, ACCENT if on else MUTED, r.centerx, r.centery, centre=True)
        if on:
            pygame.draw.line(screen, ACCENT, (r.x + 8, r.bottom), (r.right - 8, r.bottom), 3)
        hits.append(("tab", i, r))
        tx += 78
    y = rect.y + 40
    feat = look["feat"]
    if ed["tab"] == 0:
        _label(screen, "Hairstyle", rect.x, y)
        styles = HAIR_STYLES_F if gender == "Female" else HAIR_STYLES_M
        y = _chips(screen, hits, "style", styles, look["style"], rect.x, y + 18, rect.width, mouse, per_row=5)
        _label(screen, "Hair colour", rect.x, y + 6)
        cur = next((n for n, c in HAIR_COLOURS if tuple(c) == tuple(look["hair"])), None)
        y = _swatches(screen, hits, "hair", HAIR_COLOURS, cur, rect.x, y + 26, mouse, per_row=8)
        if gender == "Male":
            _label(screen, "Facial hair", rect.x, y + 4)
            _chips(screen, hits, "facial", FACIAL, look["facial"], rect.x, y + 22, rect.width, mouse, per_row=5, cw=84)
        else:
            _label(screen, "Facial hair is only offered for male characters.", rect.x, y + 4)
    elif ed["tab"] == 1:
        _label(screen, "Skin tone", rect.x, y)
        y = _swatches(screen, hits, "skin", [(str(i), c) for i, c in enumerate(SKIN_TONES)],
                      str(SKIN_TONES.index(tuple(look["skin"]))) if tuple(look["skin"]) in SKIN_TONES else None,
                      rect.x, y + 20, mouse, per_row=8)
        _label(screen, "Eye colour", rect.x, y + 4)
        y = _swatches(screen, hits, "eyes", [(n, c[0]) for n, c in EYE_COLOURS.items()], feat.get("eyes"), rect.x, y + 24, mouse, per_row=8)
        _label(screen, "Eye shape", rect.x, y + 2)
        y = _chips(screen, hits, "eye_shape", list(EYE_SHAPES), feat.get("eye_shape"), rect.x, y + 20, rect.width, mouse, per_row=5, cw=84)
        _label(screen, "Eyebrows", rect.x, y + 2)
        y = _chips(screen, hits, "brows", list(BROW_STYLES), feat.get("brows"), rect.x, y + 20, rect.width, mouse, per_row=5, cw=84)
        _label(screen, "Lips", rect.x, y + 2)
        _chips(screen, hits, "lips", list(LIP_STYLES), feat.get("lips"), rect.x, y + 20, rect.width, mouse, per_row=5, cw=84)
    else:
        _label(screen, "Clothes", rect.x, y)
        names = OUTFITS["Female" if gender == "Female" else "Male"]
        chips = ["Auto"] + [names[i] if i < len(names) else f"Outfit {i + 1}" for i in range(8)]
        sel = "Auto" if feat.get("outfit") is None else chips[(feat["outfit"] % 8) + 1]
        _chips(screen, hits, "outfit", chips, sel, rect.x, y + 20, rect.width, mouse, per_row=5, cw=84)
    return hits

def click_editor(mx, my, hits, look, gender, ed):
    for kind, val, r in hits:
        if not r.collidepoint(mx, my):
            continue
        f = look["feat"]
        if kind == "tab":
            ed["tab"] = val
        elif kind == "style":
            look["style"] = val
        elif kind == "hair":
            look["hair"] = dict(HAIR_COLOURS)[val]
        elif kind == "facial":
            look["facial"] = val
        elif kind == "skin":
            look["skin"] = SKIN_TONES[int(val)]
        elif kind in ("eyes", "eye_shape", "brows", "lips"):
            f[kind] = val
        elif kind == "outfit":
            names = OUTFITS["Female" if gender == "Female" else "Male"]
            chips = ["Auto"] + [names[i] if i < len(names) else f"Outfit {i + 1}" for i in range(8)]
            f["outfit"] = None if val == "Auto" else chips.index(val) - 1
        return True
    return False

def draw_look(screen, rect, gender, look, age=None, mood=60):
    draw_avatar(screen, rect, gender, tuple(look["hair"]), look["style"], tuple(look["skin"]),
                look["facial"] if gender == "Male" else "None", age, mood, feat_of(look))

# ---- the in-game window ------------------------------------------------------------
async def appearance_window(screen, look, gender, age, name):
    """Modal. Returns the (possibly edited) look when closed."""
    clock = pygame.time.Clock()
    backdrop = screen.copy()
    dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    dim.fill((20, 18, 30, 190))
    ed = {"tab": 0}
    look = {**look, "feat": dict(look.get("feat") or {})}
    done = pygame.Rect(SCREEN_WIDTH // 2 - 90, 628, 180, 40)
    panel = pygame.Rect(40, 40, SCREEN_WIDTH - 80, 640)
    while True:
        mouse = pygame.mouse.get_pos()
        screen.blit(backdrop, (0, 0))
        screen.blit(dim, (0, 0))
        draw_rounded_rect(screen, (252, 249, 255), panel, radius=18)
        draw_text(screen, f"{name}'s look", title_font, INK, SCREEN_WIDTH // 2, 76, centre=True)
        draw_look(screen, pygame.Rect(90, 120, 290, 360), gender, look, age)
        hits = draw_editor(screen, pygame.Rect(440, 130, 420, 440), mouse, look, gender, ed)
        draw_text(screen, "Changes show straight away.", small_font, MUTED, SCREEN_WIDTH // 2, 596, centre=True)
        draw_rounded_rect(screen, ACCENT if done.collidepoint(mouse) else (240, 130, 50), done, radius=12)
        draw_text(screen, "Done", font, WHITE, done.centerx, done.centery, centre=True)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                return look
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if done.collidepoint(e.pos):
                    return look
                click_editor(e.pos[0], e.pos[1], hits, look, gender, ed)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)
