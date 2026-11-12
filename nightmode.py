"""Plain text on the night sky, no light panel.

The tabs were written for a light sheet (dark ink, white cards). While the
sheet is being drawn, begin() turns on a colour mapping: dark text becomes
light text, white cards become faint glass, pale tints become soft tints and
coloured buttons stay coloured. Pictures (avatars, scenes) are never touched.
Pure pygame, no extra libraries."""
import pygame

TEXT = (238, 233, 252)
_s = {"on": False, "screen": None, "under": None, "rect": None}
_orig = {}

def _clip(v):
    return 0 if v < 0 else 255 if v > 255 else int(v)

def _bg(pos):
    u, r = _s["under"], _s["rect"]
    if u is None or pos is None:
        return (44, 38, 84)
    try:
        x = max(0, min(r.w - 1, int(pos[0]) - r.x))
        y = max(0, min(r.h - 1, int(pos[1]) - r.y))
        c = u.get_at((x, y))
        return (c[0], c[1], c[2])
    except Exception:
        return (44, 38, 84)

def _map(col, pos, text):
    """Returns the night-time colour, or None to skip drawing a sheet-coloured fill."""
    r, g, b = col[0], col[1], col[2]
    mx, mn = max(r, g, b), min(r, g, b)
    chroma = mx - mn
    lum = (r + g + b) / 3.0
    if chroma >= 30 and lum < 185:
        return (r, g, b)                      # saturated colours stay (buttons, bars, icons)
    if not text and (r, g, b) == (251, 248, 243):
        return None
    bg = _bg(pos)
    if not text and lum >= 245 and chroma < 14:
        bg = _bg(pos)
        return tuple(_clip(bg[i] + (255 - bg[i]) * 0.07) for i in range(3))
    if lum >= 185 and chroma >= 7:
        if text:
            return (r, g, b)
        k = 255.0 / max(mx, 1)
        return (_clip(bg[0] * 0.70 + r * k * 0.30), _clip(bg[1] * 0.70 + g * k * 0.30), _clip(bg[2] * 0.70 + b * k * 0.30))
    if text:
        if lum >= 200:
            return (r, g, b)                  # light text on a coloured button stays light
        t = max(0.0, min(1.0, (246.0 - lum) / 215.0))
        return tuple(_clip(bg[i] + (TEXT[i] - bg[i]) * t) for i in range(3))
    if 246 <= lum < 249.5 and chroma < 12:
        return None                           # the sheet colour itself: let the sky show
    lift = max(0.0, min(1.0, (lum - 249.0) / 6.0)) * 0.07
    t = max(0.0, min(1.0, (246.0 - lum) / 215.0))
    res = [bg[i] + (TEXT[i] - bg[i]) * t for i in range(3)]
    return tuple(_clip(res[i] + (255 - res[i]) * lift) for i in range(3))

def map_text(colour, screen, pos):
    if not _s["on"] or screen is not _s["screen"]:
        return colour
    c = _map(colour, pos, True)
    return c if c is not None else colour

def _wrap(name, posfn):
    orig = getattr(pygame.draw, name)
    _orig[name] = orig
    def f(surface, color, *a, **k):
        if _s["on"] and surface is _s["screen"]:
            try:
                c = _map(color, posfn(a), False)
            except Exception:
                c = tuple(color)[:3]
            if c is None:
                return pygame.Rect(0, 0, 0, 0)
            color = c
        return orig(surface, color, *a, **k)
    setattr(pygame.draw, name, f)

def _first_pt(a):
    p = a[0] if a else None
    if p and isinstance(p, (list, tuple)) and p and isinstance(p[0], (list, tuple)):
        return p[0]
    return p if isinstance(p, (list, tuple)) else None

def _rect_pos(a):
    r = a[0] if a else None
    try:
        r = pygame.Rect(r)
        return r.center
    except Exception:
        return None

def install():
    """Patch pygame.draw once. Does nothing until begin() is called."""
    if _orig:
        return
    _wrap("rect", _rect_pos)
    _wrap("ellipse", _rect_pos)
    _wrap("arc", _rect_pos)
    _wrap("circle", lambda a: a[0] if a else None)
    _wrap("line", lambda a: a[0] if a else None)
    _wrap("lines", lambda a: (a[1][0] if len(a) > 1 and a[1] else None))
    _wrap("polygon", lambda a: (a[0][0] if a and a[0] else None))

def keep(screen, surf, pos):
    """Kept for compatibility: pictures are never recoloured now."""
    return

def begin(screen, sheet):
    """Call just before the light sheet is painted."""
    _s["under"] = screen.subsurface(sheet).copy()
    _s["rect"] = sheet.copy()
    _s["screen"] = screen
    _s["on"] = True

def finish(screen):
    _s["on"] = False
