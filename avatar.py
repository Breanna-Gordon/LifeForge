import math
import random
import pygame

# Flat "cel" portraits: solid colours with one hard shadow per shape, almond
# eyes, a single-shape nose and a one-line smile. Hair, clothes and hats are
# plain polygons in face units (x: half face widths, y: half face heights from
# the eye line), so new styles are just new point lists. Drawn at 4x, scaled
# down and cached.
SS = 4
_cache = {}

HAIR_STYLES_F = ["Long", "Wavy", "Bangs", "Shoulder", "Bob", "Pixie", "Ponytail", "Bun", "SpaceBuns", "Curly", "Afro", "Braids", "SideSwept", "Bald"]
HAIR_STYLES_M = ["Short", "SidePart", "Quiff", "Messy", "Fade", "Buzzcut", "Undercut", "Curly", "Afro", "ManBun", "Long", "Dreads", "Mohawk", "Bald"]
FACIAL_STYLES = ["None", "Stubble", "Moustache", "Goatee", "Beard", "FullBeard"]
TOPS = ["Tee", "Hoodie", "Shirt", "Sweater", "Jacket", "Blazer", "Tank", "Turtleneck", "Overalls", "Dress"]
HATS = ["None", "Cap", "Beanie", "Bandana", "Hijab"]
GLASSES = ["None", "Round", "Square", "Sunglasses"]
EARRINGS = ["None", "Studs", "Hoops"]
EYE_COLOURS = {"Brown": (110, 74, 46), "Dark": (60, 40, 32), "Hazel": (138, 104, 52), "Green": (78, 132, 86),
               "Blue": (66, 124, 190), "Grey": (120, 132, 142), "Amber": (176, 116, 44)}
OUTFITS = {"Male": ["Coral", "Teal", "Navy", "Mustard", "Lilac", "Forest", "Grey", "Black", "Cream", "Red"]}
OUTFITS["Female"] = OUTFITS["Male"]
_OUTFIT_COLOURS = [(214, 116, 110), (78, 150, 140), (62, 84, 140), (228, 182, 70), (150, 122, 192), (62, 110, 80), (124, 128, 138),
                   (44, 42, 50), (236, 226, 204), (176, 52, 60)]
_ACCENTS = [(250, 240, 228), (240, 214, 120), (232, 120, 110), (90, 150, 210), (250, 250, 250)]

_STYLE_ALIAS = {"Spiky": "Messy", "Shaggy": "Messy", "Pompadour": "Quiff", "SlickBack": "SidePart", "Cornrows": "Braids",
                "TopKnot": "ManBun", "Pigtails": "SpaceBuns"}
_FACIAL_ALIAS = {"Sideburns": "Stubble", "ChinStrap": "Beard", "MuttonChops": "Beard", "LongBeard": "FullBeard",
                 "SoulPatch": "Goatee", "VanDyke": "Goatee", "Handlebar": "Moustache"}

def style_of(style, gender):
    style = _STYLE_ALIAS.get(style, style)
    return style if style in HAIR_STYLES_F + HAIR_STYLES_M else ("Long" if gender == "Female" else "Short")

def facial_of(facial):
    facial = _FACIAL_ALIAS.get(facial, facial)
    return facial if facial in FACIAL_STYLES else "None"

# ---------------- helpers ----------------
def _shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])

def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def _spline(pts, closed=True, n=10):
    """Catmull-Rom curve through the points."""
    out, c = [], len(pts)
    for i in range(c if closed else c - 1):
        p0 = pts[(i - 1) % c] if closed else pts[max(0, i - 1)]
        p3 = pts[(i + 2) % c] if closed else pts[min(c - 1, i + 2)]
        p1, p2 = pts[i], pts[(i + 1) % c]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out

def _mirror(half):
    """Right half (top to bottom) -> full closed outline."""
    return half + [(-x, y) for x, y in reversed(half[1:-1])]

def _mask(size, pts):
    m = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), pts)
    return m

def _clipped(S, mask, draw):
    lay = pygame.Surface(S.get_size(), pygame.SRCALPHA)
    draw(lay)
    lay.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    S.blit(lay, (0, 0))

def _silhouette(src, col, alpha=255):
    """A solid-colour copy of `src`'s shape."""
    out = src.copy()
    out.fill((*col, 0), special_flags=pygame.BLEND_RGBA_MIN)
    out.fill((*col, 0), special_flags=pygame.BLEND_RGB_MAX)
    if alpha < 255:
        out.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
    return out

def _stage(age):
    if age is None: return "adult"
    if age < 4: return "baby"
    if age < 13: return "child"
    if age < 18: return "teen"
    if age < 60: return "adult"
    return "elder"

def _hair_for_age(colour, age):
    if age is None or age < 45:
        return colour
    return _mix(colour, (206, 204, 210), min(1.0, (age - 45) / 25))

def _wave(pts, amp=0.06, below=-0.5):
    return [(x + (amp * math.sin(y * 6.0) * (1 if x >= 0 else -1) if y > below else 0), y) for x, y in pts]

# ---------------- hair shapes (face units) ----------------
_CAP = [(-1.04, -0.2), (-1.1, -0.75), (-0.7, -1.26), (0.1, -1.37), (0.85, -1.2), (1.1, -0.75), (1.04, -0.2), (0.94, -0.55),
        (0.6, -0.72), (0.0, -0.76), (-0.6, -0.72), (-0.95, -0.5)]
_LONG_FRONT = [(-1.12, 0.6), (-1.15, -0.5), (-0.8, -1.12), (0.0, -1.3), (0.8, -1.15), (1.14, -0.55), (1.12, 0.6), (0.94, 0.55),
               (0.92, -0.35), (0.62, -0.74), (0.1, -0.86), (-0.15, -0.62), (-0.5, -0.72), (-0.9, -0.35), (-0.93, 0.55)]

def _hair(style, female):
    """(back, front, streaks, extras) for a style; extras are drawn by name."""
    back, front, streaks, extras = None, None, [], []
    long_back = _mirror([(0, -1.2), (0.98, -1.05), (1.3, -0.3), (1.36, 0.9), (1.2, 1.75), (0, 1.8)])
    if style == "Long":
        back, front = long_back, _LONG_FRONT
        streaks = [[(-0.55, -1.0), (-0.2, -1.15), (0.2, -1.17)], [(0.98, -0.6), (1.04, -0.1), (1.04, 0.4)]]
    elif style == "Wavy":
        back, front = _wave(long_back, 0.09), _wave(_LONG_FRONT, 0.07)
        streaks = [[(-0.55, -1.0), (-0.2, -1.15), (0.2, -1.17)]]
    elif style == "Braids":
        back, front = long_back, _LONG_FRONT
        extras = ["braids"]
    elif style == "Bangs":
        back = long_back
        front = [(-1.12, 0.6), (-1.15, -0.5), (-0.8, -1.12), (0.0, -1.3), (0.8, -1.12), (1.15, -0.5), (1.12, 0.6), (0.94, 0.55), (0.93, -0.38),
                 (0.5, -0.4), (0.0, -0.37), (-0.5, -0.4), (-0.93, -0.38), (-0.94, 0.55)]
        streaks = [[(-0.5, -1.0), (0.0, -1.14), (0.5, -1.0)]]
    elif style == "Shoulder":
        back = _mirror([(0, -1.2), (1.0, -1.05), (1.28, -0.3), (1.3, 0.7), (1.15, 1.15), (0, 1.15)])
        front = [(-1.15, 0.9), (-1.18, -0.45), (-0.82, -1.12), (0.0, -1.3), (0.82, -1.14), (1.16, -0.5), (1.15, 0.9), (0.95, 0.8), (0.92, -0.32),
                 (0.55, -0.72), (-0.35, -0.82), (-0.92, -0.4), (-0.95, 0.8)]
        streaks = [[(-0.4, -1.05), (0.1, -1.15), (0.5, -1.05)]]
    elif style == "Bob":
        back = _mirror([(0, -1.2), (1.0, -1.05), (1.25, -0.3), (1.2, 0.6), (0, 0.65)])
        front = [(-1.18, 0.62), (-1.2, -0.45), (-0.85, -1.12), (0.0, -1.28), (0.85, -1.12), (1.2, -0.45), (1.18, 0.62), (0.95, 0.6), (0.92, -0.42),
                 (0.5, -0.6), (0.0, -0.55), (-0.5, -0.6), (-0.92, -0.42), (-0.95, 0.6)]
        streaks = [[(-0.6, -0.95), (-0.15, -1.12), (0.3, -1.1)]]
    elif style == "SideSwept":
        back = long_back
        front = [(-1.12, 0.6), (-1.15, -0.5), (-0.8, -1.15), (0.0, -1.32), (0.8, -1.15), (1.14, -0.55), (1.12, 0.6), (0.94, 0.55), (0.92, -0.2),
                 (0.7, -0.3), (0.2, -0.55), (-0.4, -0.78), (-0.9, -0.5), (-0.93, 0.55)]
        streaks = [[(-0.6, -1.05), (0.0, -1.0), (0.6, -0.6)], [(-0.3, -1.2), (0.3, -1.08), (0.8, -0.75)]]
    elif style == "Pixie":
        front = [(-1.05, -0.3), (-1.1, -0.8), (-0.6, -1.27), (0.2, -1.34), (0.9, -1.12), (1.08, -0.6), (1.04, -0.25), (0.92, -0.42), (0.7, -0.36),
                 (0.3, -0.5), (-0.3, -0.68), (-0.8, -0.62), (-0.96, -0.5)]
        streaks = [[(-0.6, -1.05), (0.0, -1.1), (0.6, -0.8)]]
    elif style in ("Ponytail", "Bun", "SpaceBuns", "ManBun"):
        front = [(-1.04, -0.15), (-1.06, -0.75), (-0.62, -1.18), (0.0, -1.27), (0.62, -1.18), (1.06, -0.75), (1.04, -0.15), (0.92, -0.55),
                 (0.45, -0.78), (-0.1, -0.8), (-0.6, -0.72), (-0.94, -0.52)]
        streaks = [[(-0.5, -1.0), (-0.1, -1.13), (0.3, -1.1)]]
        if style == "Ponytail":
            back = [(0.6, -1.0), (1.2, -0.85), (1.45, 0.0), (1.38, 0.9), (1.12, 1.3), (1.04, 0.4), (0.9, -0.45)]
            extras = ["tie"]
        else:
            extras = [{"Bun": "bun", "SpaceBuns": "spacebuns", "ManBun": "manbun"}[style]]
    elif style == "Short":
        front = [(-1.04, -0.2), (-1.1, -0.75), (-0.7, -1.25), (0.1, -1.38), (0.85, -1.2), (1.1, -0.75), (1.04, -0.2), (0.94, -0.55), (0.6, -0.72),
                 (0.25, -0.66), (0.05, -0.8), (-0.35, -0.72), (-0.8, -0.62), (-0.95, -0.5)]
        streaks = [[(-0.6, -1.05), (-0.2, -1.22), (0.25, -1.24)], [(0.2, -1.05), (0.55, -1.08), (0.8, -0.9)]]
    elif style == "SidePart":
        front = [(-1.04, -0.2), (-1.1, -0.78), (-0.75, -1.32), (0.0, -1.45), (0.85, -1.25), (1.1, -0.75), (1.04, -0.2), (0.94, -0.55),
                 (0.55, -0.82), (-0.1, -0.86), (-0.42, -0.98), (-0.62, -0.72), (-0.95, -0.5)]
        streaks = [[(-0.25, -1.2), (0.3, -1.3), (0.8, -1.1)], [(-0.45, -1.08), (-0.5, -0.9)]]
    elif style == "Quiff":
        front = [(-1.04, -0.2), (-1.1, -0.8), (-0.8, -1.3), (-0.3, -1.62), (0.4, -1.66), (0.95, -1.3), (1.1, -0.75), (1.04, -0.2), (0.94, -0.55),
                 (0.6, -0.8), (0.1, -0.86), (-0.5, -0.78), (-0.95, -0.5)]
        streaks = [[(-0.5, -1.25), (0.0, -1.5), (0.5, -1.48)], [(-0.2, -1.1), (0.3, -1.3), (0.75, -1.2)]]
    elif style == "Messy":
        front = [(-1.04, -0.2), (-1.12, -0.7), (-1.0, -1.1), (-0.75, -1.3), (-0.5, -1.5), (-0.2, -1.38), (0.1, -1.55), (0.35, -1.38), (0.7, -1.45),
                 (0.85, -1.2), (1.12, -1.1), (1.08, -0.7), (1.04, -0.2), (0.92, -0.5), (0.75, -0.58), (0.55, -0.48), (0.35, -0.7), (0.1, -0.55),
                 (-0.15, -0.72), (-0.45, -0.58), (-0.7, -0.7), (-0.95, -0.5)]
        streaks = [[(-0.6, -1.1), (-0.3, -1.25)], [(0.2, -1.2), (0.55, -1.25)]]
    elif style in ("Fade", "Buzzcut"):
        front = [(-1.02, -0.4), (-1.06, -0.82), (-0.65, -1.22), (0.0, -1.3), (0.65, -1.22), (1.06, -0.82), (1.02, -0.4), (0.92, -0.62), (0.5, -0.8),
                 (0.0, -0.82), (-0.5, -0.8), (-0.92, -0.62)]
        extras = ["fade" if style == "Fade" else "buzz"]
    elif style == "Undercut":
        front = [(-0.85, -0.85), (-0.7, -1.3), (0.0, -1.5), (0.8, -1.38), (1.08, -1.0), (1.0, -0.72), (0.6, -0.82), (0.0, -0.84), (-0.6, -0.86)]
        streaks = [[(-0.4, -1.25), (0.2, -1.38), (0.8, -1.15)]]
        extras = ["sides"]
    elif style == "Mohawk":
        front = [(-0.28, -0.8), (-0.32, -1.3), (-0.18, -1.75), (0.05, -1.95), (0.22, -1.7), (0.32, -1.3), (0.28, -0.8), (0.0, -0.85)]
        extras = ["sides"]
    elif style == "Long" or style == "Dreads":
        back, front = long_back, _LONG_FRONT
    if style == "Long" and not female:
        back = _mirror([(0, -1.2), (1.0, -1.05), (1.28, -0.3), (1.3, 0.7), (1.15, 1.2), (0, 1.2)])
        front = [(-1.12, 0.8), (-1.15, -0.5), (-0.8, -1.12), (0.0, -1.3), (0.8, -1.15), (1.14, -0.55), (1.12, 0.8), (0.94, 0.7), (0.92, -0.35),
                 (0.5, -0.76), (0.0, -0.84), (-0.5, -0.76), (-0.9, -0.35), (-0.93, 0.7)]
    if style == "Dreads":
        back = _mirror([(0, -1.2), (1.0, -1.05), (1.32, -0.3), (1.36, 0.8), (1.2, 1.35), (0, 1.4)])
        front = [(-1.15, 0.9), (-1.18, -0.5), (-0.8, -1.15), (0.0, -1.32), (0.8, -1.15), (1.18, -0.5), (1.15, 0.9), (0.95, 0.8), (0.92, -0.35),
                 (0.5, -0.74), (0.0, -0.8), (-0.5, -0.74), (-0.92, -0.35), (-0.95, 0.8)]
        extras = ["dreads"]
    return back, front, streaks, extras


def _render(w, h, gender, hair, style, skin, facial, age, mood, seed, feat):
    W, H = w * SS, h * SS
    female = gender == "Female"
    stage = _stage(age)
    baby, child, teen, elder = stage == "baby", stage == "child", stage == "teen", stage == "elder"
    young = baby or child
    rng = random.Random(seed)

    hair = _hair_for_age(hair, age)
    hair_dk = _shade(hair, 0.7) if sum(hair) > 120 else _mix(hair, (0, 0, 0), 0.35)
    hair_hi = _mix(hair, (255, 255, 255), 0.42 if sum(hair) > 120 else 0.3)
    sk_sh = _mix(_shade(skin, 0.8), (170, 70, 70), 0.18)
    sk_dk = _shade(sk_sh, 0.85)
    ink = _mix(_shade(skin, 0.35), (40, 20, 30), 0.5)

    base = min(W, H * 0.72)
    fw = base * 0.23 * (1.15 if baby else 1.08 if child else 1.0)
    fh = fw * (1.1 if baby else 1.18 if child else 1.24 if teen else 1.27)
    cx = W / 2
    cy = H * (0.44 if H >= W * 1.12 else 0.46)
    lw = max(2, int(fw * 0.045))

    def F(x, y):
        return (cx + x * fw, cy + y * fh)
    def P(pts, closed=True):
        return [F(x, y) for x, y in _spline(pts, closed)]

    hat = feat.get("hat", "None") if not baby else "None"
    s_ = "Baby" if baby else style
    back, front, streaks, extras = _hair("Short" if baby else style, female)
    if s_ == "Baby" or s_ == "Bald" or hat == "Hijab":
        back, front, streaks, extras = None, None, [], []

    out = pygame.Surface((W, H), pygame.SRCALPHA)
    back_l = pygame.Surface((W, H), pygame.SRCALPHA)
    front_l = pygame.Surface((W, H), pygame.SRCALPHA)

    def curls(S, top, rx, ry, n, r, ring=False, col=hair):
        for k in range(n):
            a = (math.pi * 2 * k / n) if ring else math.pi * (1.02 + 0.96 * k / (n - 1))
            c = F(math.cos(a) * rx, top + math.sin(a) * ry)
            pygame.draw.circle(S, _shade(col, 0.72), (c[0] + fw * 0.04, c[1] + fw * 0.05), fw * r)
            pygame.draw.circle(S, col, c, fw * r)
            pygame.draw.arc(S, hair_hi, pygame.Rect(c[0] - fw * r * 0.6, c[1] - fw * r * 0.6, fw * r * 1.2, fw * r * 1.2),
                            math.pi * 0.55, math.pi * 1.0, max(2, int(fw * 0.05)))

    # ---------------- back hair ----------------
    if style in ("Curly", "Afro") and not baby and hat != "Hijab":
        if style == "Afro":
            curls(back_l, -0.35, 1.45, 1.25, 18, 0.46, ring=True, col=_shade(hair, 0.85))
        elif female:
            curls(back_l, -0.1, 1.3, 1.2, 16, 0.4, ring=True, col=_shade(hair, 0.85))
    if back:
        pygame.draw.polygon(back_l, hair_dk, P(back))
        if "dreads" in extras or "braids" in extras:
            for k in range(9):
                x = -1.15 + 2.3 * k / 8
                pts = [F(x, -0.2), F(x * 1.05, 0.6), F(x * 1.02, 1.5 if back[-1][1] > 1.5 else 1.25)]
                pygame.draw.lines(back_l, _shade(hair_dk, 0.75), False, pts, max(2, int(fw * 0.05)))

    # ---------------- body & clothes ----------------
    oi = feat.get("outfit")
    col = _OUTFIT_COLOURS[(oi if oi is not None else seed) % len(_OUTFIT_COLOURS)]
    top = feat.get("top")
    if top not in TOPS:
        top = ["Tee", "Hoodie", "Shirt", "Sweater", "Jacket"][(oi if oi is not None else seed // 3) % 5]
    if baby:
        top, col = "Tee", (250, 214, 150)
    elif child and top in ("Blazer", "Dress", "Tank"):
        top = "Tee"
    if not female and top == "Dress":
        top = "Tank"
    accent = _ACCENTS[(seed // 2) % len(_ACCENTS)]
    col_sh = _shade(col, 0.84)
    sw = fw * (1.9 if young else 2.3) * (0.9 if female else 1.0)
    sy = cy + fh * (1.3 if young else 1.45)
    body = _spline([(cx - sw, H + 10), (cx - sw * 0.94, sy + fh * 0.55), (cx - sw * 0.66, sy), (cx + sw * 0.66, sy),
                    (cx + sw * 0.94, sy + fh * 0.55), (cx + sw, H + 10)], False) + [(cx + sw, H + 10), (cx - sw, H + 10)]
    bmask = _mask((W, H), body)
    neck = [F(-0.4, 0.6), F(0.4, 0.6), F(0.44, (1.4 if young else 1.55)), F(-0.44, (1.4 if young else 1.55))]

    def garment(colour, shadow=True):
        pygame.draw.polygon(out, colour, body)
        if shadow:
            _clipped(out, bmask, lambda L: pygame.draw.polygon(L, _shade(colour, 0.84), [(cx + fw * 0.9, sy - 10), (W, sy - 10), (W, H), (cx + fw * 1.4, H)]))
    def crew(colour, depth=0.42, band=0.1):
        r = pygame.Rect(0, 0, fw * 1.0, fh * depth); r.center = F(0, (1.33 if young else 1.48))
        pygame.draw.ellipse(out, sk_sh, r)
        pygame.draw.arc(out, colour, r.inflate(fw * 0.16, fh * 0.12), math.pi * 1.0, math.pi * 2.0, int(fw * band))
    def vneck(depth, width=0.5):
        pygame.draw.polygon(out, sk_sh, [(cx - fw * width, sy - fh * 0.05), (cx + fw * width, sy - fh * 0.05), (cx, sy + fh * depth)])

    if top == "Tank" or top == "Dress":
        pygame.draw.polygon(out, skin, body)
        _clipped(out, bmask, lambda L: pygame.draw.polygon(L, sk_sh, [(cx + fw * 1.0, sy - 10), (W, sy - 10), (W, H), (cx + fw * 1.4, H)]))
    pygame.draw.polygon(out, skin, neck)
    _clipped(out, _mask((W, H), neck), lambda L: pygame.draw.polygon(L, sk_sh, [(x, y + fh * 0.42) for x, y in P(_mirror([(0, 0.4), (0.9, 0.4), (0.7, 0.8), (0.35, 1.0), (0, 1.02)]))]))

    if top == "Tee":
        garment(col); crew(col_sh)
    elif top == "Sweater":
        garment(col)
        for k in range(-3, 4):
            pygame.draw.line(out, col_sh, (cx + k * fw * 0.5, sy + fh * 0.6), (cx + k * fw * 0.52, H), max(2, lw))
        crew(_shade(col, 0.78), 0.42, 0.16)
    elif top == "Hoodie":
        garment(col)
        hood = _spline([(cx - fw * 1.25, sy + fh * 0.45), (cx - fw * 1.0, sy - fh * 0.12), (cx, sy + fh * 0.12), (cx + fw * 1.0, sy - fh * 0.12),
                        (cx + fw * 1.25, sy + fh * 0.45), (cx + fw * 0.4, sy + fh * 0.9), (cx - fw * 0.4, sy + fh * 0.9)])
        hcol = _shade(col, 0.82) if oi is None or oi % 2 else accent if sum(accent) < 600 else _shade(col, 0.82)
        pygame.draw.polygon(out, hcol, hood)
        pygame.draw.polygon(out, _shade(hcol, 0.6), _spline([(cx - fw * 0.75, sy + fh * 0.05), (cx, sy + fh * 0.32), (cx + fw * 0.75, sy + fh * 0.05),
                                                             (cx + fw * 0.3, sy + fh * 0.6), (cx - fw * 0.3, sy + fh * 0.6)]))
        for sx in (-1, 1):
            pygame.draw.line(out, _mix(hcol, (255, 255, 255), 0.5), (cx + sx * fw * 0.35, sy + fh * 0.5), (cx + sx * fw * 0.4, sy + fh * 1.3), int(fw * 0.07))
    elif top == "Shirt":
        garment(col); vneck(0.42, 0.42)
        for sx in (-1, 1):
            pygame.draw.polygon(out, _mix(col, (255, 255, 255), 0.25), [(cx + sx * fw * 0.42, sy - fh * 0.18), (cx + sx * fw * 0.95, sy + fh * 0.05),
                                                                         (cx + sx * fw * 0.7, sy + fh * 0.38), (cx + sx * fw * 0.03, sy + fh * 0.42)])
        pygame.draw.line(out, col_sh, (cx, sy + fh * 0.42), (cx, H), lw)
        for k in range(3):
            pygame.draw.circle(out, _mix(col, (255, 255, 255), 0.6), (cx + fw * 0.06, sy + fh * (0.7 + 0.45 * k)), fw * 0.045)
    elif top == "Turtleneck":
        garment(col)
        tn = [F(-0.5, 0.95), F(0.5, 0.95), F(0.62, 1.62), F(-0.62, 1.62)]
        pygame.draw.polygon(out, col_sh, tn)
        for k in range(1, 4):
            y = 0.95 + 0.17 * k
            pygame.draw.line(out, _shade(col, 0.72), F(-0.52, y), F(0.52, y), max(2, lw - 1))
    elif top in ("Jacket", "Blazer"):
        inner = (246, 244, 240) if top == "Blazer" else accent
        garment(inner, shadow=False)
        if top == "Blazer":
            vneck(0.3, 0.38)
            for sx in (-1, 1):
                pygame.draw.polygon(out, (250, 250, 250), [(cx + sx * fw * 0.38, sy - fh * 0.14), (cx + sx * fw * 0.8, sy + fh * 0.02),
                                                          (cx + sx * fw * 0.55, sy + fh * 0.3), (cx + sx * fw * 0.02, sy + fh * 0.32)])
            tie = _ACCENTS[2] if col != _ACCENTS[2] else (60, 80, 140)
            pygame.draw.polygon(out, tie, [(cx - fw * 0.1, sy + fh * 0.3), (cx + fw * 0.1, sy + fh * 0.3), (cx + fw * 0.16, sy + fh * 1.4), (cx, sy + fh * 1.6), (cx - fw * 0.16, sy + fh * 1.4)])
        else:
            crew(_shade(inner, 0.85), 0.4, 0.08)
        for sx in (-1, 1):
            lap = [(cx + sx * fw * 0.62, sy - fh * 0.04), (cx + sx * sw * 0.7, sy + fh * 0.05), (cx + sx * sw * 0.94, sy + fh * 0.6), (cx + sx * sw, H + 10),
                   (cx + sx * fw * 0.5, H + 10), (cx + sx * fw * 0.42, sy + fh * 0.9), (cx + sx * fw * 0.7, sy + fh * 0.5)]
            pygame.draw.polygon(out, col if sx < 0 else col_sh, lap)
            pygame.draw.polygon(out, _shade(col, 0.72), [(cx + sx * fw * 0.62, sy - fh * 0.04), (cx + sx * fw * 0.9, sy + fh * 0.08), (cx + sx * fw * 0.72, sy + fh * 0.5)])
    elif top == "Overalls":
        garment(accent if sum(accent) < 700 else (240, 236, 226))
        crew(_shade(accent, 0.85), 0.4, 0.08)
        denim = col if oi is not None else (90, 120, 160)
        bib = [(cx - fw * 0.9, sy + fh * 0.7), (cx + fw * 0.9, sy + fh * 0.7), (cx + fw * 1.0, H + 10), (cx - fw * 1.0, H + 10)]
        pygame.draw.polygon(out, denim, bib)
        for sx in (-1, 1):
            pygame.draw.polygon(out, _shade(denim, 0.9), [(cx + sx * fw * 0.7, sy + fh * 0.72), (cx + sx * fw * 0.95, sy + fh * 0.72), (cx + sx * fw * 1.5, sy), (cx + sx * fw * 1.2, sy)])
            pygame.draw.circle(out, (230, 200, 120), (cx + sx * fw * 0.78, sy + fh * 0.85), fw * 0.07)
        pygame.draw.rect(out, _shade(denim, 0.85), pygame.Rect(cx - fw * 0.35, sy + fh * 1.05, fw * 0.7, fh * 0.45), max(2, lw))
    elif top in ("Tank", "Dress"):
        neckline = sy + fh * (0.55 if top == "Tank" else 0.65)
        cloth = [(cx - sw * 0.8, neckline + fh * 0.1), (cx - fw * 0.6, neckline), (cx, neckline + fh * (0.25 if top == "Dress" else 0.15)),
                 (cx + fw * 0.6, neckline), (cx + sw * 0.8, neckline + fh * 0.1), (cx + sw, H + 10), (cx - sw, H + 10)]
        pygame.draw.polygon(out, col, _spline(cloth[:5], False) + cloth[5:])
        _clipped(out, bmask, lambda L: pygame.draw.polygon(L, col_sh, [(cx + fw * 1.0, neckline), (W, neckline), (W, H), (cx + fw * 1.4, H)]))
        for sx in (-1, 1):
            st = (cx + sx * fw * (0.95 if top == "Tank" else 0.9), neckline + fh * 0.02)
            pygame.draw.line(out, col, st, (cx + sx * fw * (1.15 if top == "Tank" else 1.0), sy - fh * 0.02), int(fw * (0.22 if top == "Tank" else 0.06)))

    # ---------------- head ----------------
    out.blit(back_l, (0, 0))   # long hair sits behind the head but over the clothes
    for sx in (-1, 1):
        e = pygame.Rect(0, 0, fw * 0.34, fh * 0.36); e.center = F(sx * 1.0, 0.02)
        pygame.draw.ellipse(out, skin if sx < 0 else sk_sh, e)
        pygame.draw.ellipse(out, sk_dk, e.inflate(-e.w * 0.5, -e.h * 0.45).move(sx * e.w * 0.05, 0))
    if young:
        jaw = [(0.98, 0.35), (0.78, 0.78), (0.4, 1.0)]
    elif female:
        jaw = [(0.88, 0.4), (0.64, 0.8), (0.3, 1.0)]
    else:
        jaw = [(0.94, 0.42), (0.72, 0.82), (0.38, 1.0)]
    face = P(_mirror([(0, -1.02), (0.7, -0.96), (0.98, -0.55), (1.0, -0.05)] + jaw + [(0, 1.03)]))
    fm = _mask((W, H), face)
    pygame.draw.polygon(out, skin, face)
    _clipped(out, fm, lambda L: pygame.draw.polygon(L, sk_sh, [(x + fw * 1.72, y + fh * 0.02) for x, y in face]))

    # ---------------- hair (front layer, so it can shade the forehead) ----------------
    if s_ == "Baby":
        pygame.draw.polygon(front_l, hair, P([(-0.1, -0.98), (0.0, -1.2), (0.18, -1.24), (0.12, -1.1), (0.08, -0.98)]))
    if front:
        fp = P(front)
        pygame.draw.polygon(front_l, hair, fp)
        _clipped(front_l, _mask((W, H), fp), lambda L: pygame.draw.polygon(L, hair_dk, [(x + fw * 1.6, y) for x, y in fp]))
        for st in streaks:
            pygame.draw.lines(front_l, hair_hi, False, P(st, False), max(2, int(fw * 0.05)))
    if style == "Curly" and not baby:
        curls(front_l, -0.42, 1.0, 0.85, 11, 0.33)
    elif style == "Afro" and not baby:
        curls(front_l, -0.5, 1.05, 0.95, 12, 0.38)
    for ex_ in extras:
        if ex_ in ("bun", "manbun"):
            c = F(0, -1.38 if ex_ == "bun" else -1.32)
            r = fw * (0.42 if ex_ == "bun" else 0.3)
            pygame.draw.circle(front_l, hair, c, r)
            pygame.draw.arc(front_l, hair_hi, pygame.Rect(c[0] - r * 0.65, c[1] - r * 0.65, r * 1.3, r * 1.3), math.pi * 0.5, math.pi * 0.95, max(2, int(fw * 0.05)))
            pygame.draw.line(front_l, hair_dk, (c[0] - r * 0.7, c[1] + r * 0.75), (c[0] + r * 0.7, c[1] + r * 0.75), max(2, int(fw * 0.06)))
        elif ex_ == "spacebuns":
            for sx in (-1, 1):
                c = F(sx * 0.78, -1.15)
                pygame.draw.circle(front_l, hair, c, fw * 0.36)
                pygame.draw.arc(front_l, hair_hi, pygame.Rect(c[0] - fw * 0.22, c[1] - fw * 0.22, fw * 0.44, fw * 0.44), math.pi * 0.5, math.pi * 0.95, max(2, int(fw * 0.05)))
        elif ex_ == "tie":
            pygame.draw.circle(front_l, _ACCENTS[(seed + 2) % len(_ACCENTS)], F(0.95, -0.9), fw * 0.1)
        elif ex_ in ("fade", "buzz", "sides"):
            lay = pygame.Surface((W, H), pygame.SRCALPHA)
            sides = P([(-1.03, -0.3), (-1.08, -0.85), (-0.7, -1.25), (0.0, -1.33), (0.7, -1.25), (1.08, -0.85), (1.03, -0.3), (0.92, -0.6), (0.5, -0.82),
                       (0.0, -0.85), (-0.5, -0.82), (-0.92, -0.6)])
            pygame.draw.polygon(lay, (*hair, 120 if ex_ != "buzz" else 150), sides)
            front_l.blit(lay, (0, 0))
            if ex_ == "buzz":
                fp = P(front)
                dots = pygame.Surface((W, H), pygame.SRCALPHA)
                x0, y0 = F(-1.1, -1.35)
                for _ in range(int(fw * fw * 0.6)):
                    pygame.draw.circle(dots, (*hair_dk, 160), (x0 + rng.random() * fw * 2.2, y0 + rng.random() * fh * 0.75), max(1, fw * 0.012))
                dots.blit(_mask((W, H), fp), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                front_l.blit(dots, (0, 0))
        elif ex_ == "braids":
            for sx in (-1, 1):
                for x in (0.98, 1.08):
                    for j in range(7):
                        c = F(sx * x, -0.25 + 0.13 * j)
                        pygame.draw.lines(front_l, hair_dk, False, [(c[0] - fw * 0.05, c[1] - fh * 0.05), c, (c[0] + fw * 0.05, c[1] - fh * 0.05)], max(2, lw - 1))
        elif ex_ == "dreads":
            for sx in (-1, 1):
                for k in range(3):
                    x = sx * (0.95 + 0.07 * k)
                    pygame.draw.lines(front_l, hair_dk, False, [F(x, -0.4), F(x + sx * 0.04, 0.2), F(x, 0.8)], max(2, int(fw * 0.07)))
    if hat in ("Cap", "Beanie"):
        line_y = F(0, -0.62)[1]
        front_l.fill((0, 0, 0, 0), pygame.Rect(0, 0, W, int(line_y)))
        back_l.fill((0, 0, 0, 0), pygame.Rect(0, 0, W, int(line_y)))

    # hair casts a hard shadow on the forehead
    sh = pygame.Surface((W, H), pygame.SRCALPHA)
    sh.blit(_silhouette(front_l, sk_sh), (int(fw * 0.04), int(fh * 0.16)))
    sh.blit(fm, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    out.blit(sh, (0, 0))

    # ---------------- face ----------------
    happy, sad, beam = mood >= 60, mood < 35, mood >= 85
    blush = pygame.Surface((W, H), pygame.SRCALPHA)
    for sx in (-1, 1):
        pygame.draw.ellipse(blush, (235, 110, 120, 75 if (female or young) else 40), pygame.Rect(F(sx * 0.58 - 0.2, 0.22), (fw * 0.4, fh * 0.16)))
    out.blit(blush, (0, 0))
    ea = fw * (0.26 if young else 0.22)
    eb = fh * (0.13 if young else 0.1)
    eye_c = EYE_COLOURS.get(feat.get("eyes"), EYE_COLOURS["Brown"])
    brow_c = _shade(hair, 0.72) if sum(hair) > 200 else hair
    for sx in (-1, 1):
        ex, ey = F(sx * (0.44 if young else 0.42), 0.08 if young else 0.0)
        if beam and not young:
            pygame.draw.arc(out, ink, pygame.Rect(ex - ea, ey - eb * 0.6, ea * 2, eb * 2.2), math.pi * 0.12, math.pi * 0.88, int(fw * 0.07))
        else:
            shape = _spline([(ex - ea, ey + eb * 0.1), (ex - ea * 0.4, ey - eb), (ex + ea * 0.4, ey - eb), (ex + ea, ey + eb * 0.05),
                             (ex + ea * 0.4, ey + eb * 0.85), (ex - ea * 0.4, ey + eb * 0.85)])
            pygame.draw.polygon(out, (252, 250, 248), shape)
            def iris(L, ex=ex, ey=ey):
                r = eb * 1.05
                pygame.draw.circle(L, _shade(eye_c, 0.6), (ex, ey + eb * 0.05), r)
                pygame.draw.circle(L, eye_c, (ex, ey + eb * 0.12), r * 0.8)
                pygame.draw.circle(L, (24, 18, 22), (ex, ey + eb * 0.08), r * 0.45)
                pygame.draw.circle(L, (255, 255, 255), (ex - r * 0.35, ey - r * 0.3), r * 0.25)
            _clipped(out, _mask((W, H), shape), iris)
            up = _spline([(ex - ea * 1.02, ey + eb * 0.12), (ex - ea * 0.4, ey - eb * 1.02), (ex + ea * 0.4, ey - eb * 1.02), (ex + ea * 1.08, ey)], False)
            pygame.draw.lines(out, ink, False, up, int(fw * (0.075 if female else 0.055)))
            if female and not baby:
                pygame.draw.line(out, ink, up[-1], (up[-1][0] + sx * ea * 0.35, up[-1][1] - eb * 0.6), int(fw * 0.06))
            if happy and not young:
                pygame.draw.arc(out, sk_sh, pygame.Rect(ex - ea * 0.8, ey + eb * 0.8, ea * 1.6, eb * 1.0), math.pi * 0.15, math.pi * 0.85, max(2, lw))
        lift = 0.07 if sad else 0.0
        b = _spline([(cx + sx * fw * 0.18, cy - fh * (0.25 + lift)), (cx + sx * fw * 0.42, cy - fh * (0.34 if not sad else 0.29)),
                     (cx + sx * fw * 0.66, cy - fh * 0.27)], False)
        if young:
            b = [(x, y + fh * 0.04) for x, y in b]
        pygame.draw.lines(out, brow_c, False, b, int(fw * (0.11 if not female else 0.08) * (0.8 if young else 1.0)))
        if elder:
            pygame.draw.line(out, sk_dk, (ex + sx * ea * 1.25, ey - eb * 0.1), (ex + sx * ea * 1.6, ey - eb * 0.5), max(2, lw - 1))
            pygame.draw.line(out, sk_dk, (ex + sx * ea * 1.25, ey + eb * 0.3), (ex + sx * ea * 1.6, ey + eb * 0.6), max(2, lw - 1))
    nk = 0.7 if young else 1.0
    nose = _spline([(cx - fw * 0.03, cy + fh * 0.08), (cx + fw * 0.03, cy + fh * 0.08), (cx + fw * 0.15 * nk, cy + fh * 0.32), (cx + fw * 0.06 * nk, cy + fh * 0.39),
                    (cx - fw * 0.06 * nk, cy + fh * 0.39), (cx - fw * 0.15 * nk, cy + fh * 0.32)])
    pygame.draw.polygon(out, _mix(sk_sh, (220, 110, 90), 0.2), nose)
    if elder:
        for sx in (-1, 1):
            pygame.draw.lines(out, sk_dk, False, _spline([F(sx * 0.24, 0.3), F(sx * 0.38, 0.5), F(sx * 0.36, 0.68)], False), max(2, lw - 1))
        for k in range(2):
            pygame.draw.lines(out, sk_dk, False, _spline([F(-0.4, -0.55 - k * 0.1), F(0, -0.6 - k * 0.1), F(0.4, -0.55 - k * 0.1)], False), max(2, lw - 1))

    # facial hair (under the mouth line)
    fstyle = facial_of(facial) if (not female and not young and (age is None or age >= 16)) else "None"
    beard = _spline([(-0.98, -0.05), (-0.85, 0.5), (-0.5, 0.95), (0, 1.12), (0.5, 0.95), (0.85, 0.5), (0.98, -0.05), (0.75, 0.25), (0.35, 0.5),
                     (0.32, 0.78), (0, 0.84), (-0.32, 0.78), (-0.35, 0.5), (-0.75, 0.25)])
    mous = _spline([(-0.42, 0.56), (-0.2, 0.46), (0, 0.48), (0.2, 0.46), (0.42, 0.56), (0.3, 0.6), (0, 0.55), (-0.3, 0.6)])
    if fstyle == "Stubble":
        lay = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(lay, (*hair_dk, 70), [F(x, y) for x, y in beard])
        pygame.draw.polygon(lay, (*hair_dk, 70), [F(x, y) for x, y in mous])
        out.blit(lay, (0, 0))
    elif fstyle in ("Beard", "FullBeard"):
        pts = [(x, y + (0.25 * max(0.0, y - 0.6) if fstyle == "FullBeard" else 0)) for x, y in beard]
        if fstyle == "FullBeard":
            pts = [(x, y * 1.18 if y > 0.9 else y) for x, y in pts]
        bp = [F(x, y) for x, y in pts]
        pygame.draw.polygon(out, hair, bp)
        _clipped(out, _mask((W, H), bp), lambda L: pygame.draw.polygon(L, hair_dk, [(x + fw * 1.6, y) for x, y in bp]))
    elif fstyle == "Goatee":
        pygame.draw.polygon(out, hair, P([(-0.3, 0.72), (0, 0.68), (0.3, 0.72), (0.25, 0.98), (0, 1.06), (-0.25, 0.98)]))

    # mouth
    lip_c = _mix(skin, (210, 80, 100), 0.45)
    if beam:
        m = P([(-0.32, 0.56), (0, 0.6), (0.32, 0.56), (0.2, 0.78), (0, 0.84), (-0.2, 0.78)])
        pygame.draw.polygon(out, (120, 40, 52), m)
        _clipped(out, _mask((W, H), m), lambda L: pygame.draw.rect(L, (252, 250, 246), pygame.Rect(F(-0.4, 0.5), (fw * 0.8, fh * 0.13))))
    else:
        if female and not young:
            pygame.draw.polygon(out, lip_c, P([(-0.22, 0.61), (0, 0.74), (0.22, 0.61), (0, 0.66)]))
        depth = 0.66 if happy else (0.6 if not sad else 0.54)
        ends = 0.58 if not sad else 0.64
        pygame.draw.lines(out, ink, False, _spline([F(-0.3, ends), F(0, depth), F(0.3, ends)], False), int(fw * 0.045))
    if fstyle in ("Moustache", "Beard", "FullBeard", "Goatee"):
        pygame.draw.polygon(out, hair, [F(x, y) for x, y in mous])

    # earrings sit on the ears, under the hair
    ear_r = feat.get("earrings", "None")
    if ear_r in ("Studs", "Hoops") and not baby:
        for sx in (-1, 1):
            c = F(sx * 1.0, 0.2)
            if ear_r == "Studs":
                pygame.draw.circle(out, (240, 210, 120), c, fw * 0.06)
            else:
                pygame.draw.circle(out, (230, 196, 100), (c[0], c[1] + fh * 0.12), fw * 0.13, max(2, int(fw * 0.04)))

    out.blit(front_l, (0, 0))

    # ---------------- hats ----------------
    if hat == "Hijab":
        hc = col if feat.get("outfit") is not None else _OUTFIT_COLOURS[(seed + 4) % len(_OUTFIT_COLOURS)]
        wrap = P(_mirror([(0, -1.45), (0.95, -1.3), (1.32, -0.6), (1.35, 0.3), (1.2, 1.05), (1.7, 1.75), (0, 1.9)]))
        face_hole = P(_mirror([(0, -0.9), (0.72, -0.86), (0.96, -0.45), (0.98, 0.0)] + jaw + [(0, 1.04)]))
        lay = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(lay, hc, wrap)
        _clipped(lay, _mask((W, H), wrap), lambda L: pygame.draw.polygon(L, _shade(hc, 0.82), [(x + fw * 1.9, y) for x, y in wrap]))
        pygame.draw.polygon(lay, (0, 0, 0, 0), face_hole)
        pygame.draw.lines(lay, _shade(hc, 0.75), True, face_hole, max(2, lw))
        out.blit(lay, (0, 0))
    elif hat == "Cap":
        hc = _OUTFIT_COLOURS[(seed + 2) % len(_OUTFIT_COLOURS)] if feat.get("outfit") is None else _shade(col, 0.9)
        dome = P([(-1.1, -0.6), (-1.0, -1.15), (-0.5, -1.48), (0.2, -1.55), (0.85, -1.35), (1.12, -0.9), (1.1, -0.6)])
        pygame.draw.polygon(out, hc, dome)
        _clipped(out, _mask((W, H), dome), lambda L: pygame.draw.polygon(L, _shade(hc, 0.82), [(x + fw * 1.6, y) for x, y in dome]))
        pygame.draw.circle(out, _shade(hc, 0.75), F(0.0, -1.5), fw * 0.07)
        brim = P([(-1.05, -0.62), (0.0, -0.72), (1.1, -0.62), (0.9, -0.42), (0.0, -0.48), (-0.85, -0.42)])
        pygame.draw.polygon(out, _shade(hc, 0.7), brim)
        sh = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(sh, (*sk_sh, 255), [(x, y + fh * 0.12) for x, y in brim])
        sh.blit(fm, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        out.blit(sh, (0, 0))
        pygame.draw.polygon(out, _shade(hc, 0.7), brim)
    elif hat == "Beanie":
        hc = _OUTFIT_COLOURS[(seed + 5) % len(_OUTFIT_COLOURS)] if feat.get("outfit") is None else _shade(col, 0.9)
        dome = P([(-1.12, -0.55), (-1.05, -1.15), (-0.5, -1.5), (0.0, -1.56), (0.5, -1.5), (1.05, -1.15), (1.12, -0.55)])
        pygame.draw.polygon(out, hc, dome)
        _clipped(out, _mask((W, H), dome), lambda L: pygame.draw.polygon(L, _shade(hc, 0.82), [(x + fw * 1.6, y) for x, y in dome]))
        band = pygame.Rect(0, 0, fw * 2.3, fh * 0.32); band.center = F(0, -0.66)
        pygame.draw.rect(out, _shade(hc, 0.85), band, border_radius=int(fw * 0.12))
        for k in range(1, 11):
            x = band.x + band.w * k / 11
            pygame.draw.line(out, _shade(hc, 0.7), (x, band.y + 4), (x, band.bottom - 4), max(2, lw - 1))
        pygame.draw.circle(out, _mix(hc, (255, 255, 255), 0.4), F(0, -1.6), fw * 0.2)
    elif hat == "Bandana":
        hc = _ACCENTS[2] if feat.get("outfit") is None else col
        band = P([(-1.08, -0.62), (-0.9, -0.95), (0.0, -1.05), (0.9, -0.95), (1.08, -0.62), (0.0, -0.72)])
        pygame.draw.polygon(out, hc, band)
        for k in range(5):
            pygame.draw.circle(out, _mix(hc, (255, 255, 255), 0.7), F(-0.7 + 0.35 * k, -0.86 + (0.04 if k % 2 else 0)), fw * 0.04)
        pygame.draw.polygon(out, _shade(hc, 0.85), [F(1.0, -0.7), F(1.35, -0.6), F(1.25, -0.25), F(1.05, -0.5)])

    # ---------------- glasses ----------------
    gl = feat.get("glasses", "None")
    if gl in ("Round", "Square", "Sunglasses") and not baby:
        fc = (40, 36, 44)
        for sx in (-1, 1):
            c = F(sx * (0.44 if young else 0.42), 0.0)
            if gl == "Round":
                pygame.draw.circle(out, fc, c, fw * 0.28, max(2, int(fw * 0.05)))
            else:
                r = pygame.Rect(0, 0, fw * 0.6, fh * 0.36); r.center = c
                if gl == "Sunglasses":
                    pygame.draw.rect(out, (30, 30, 38), r, border_radius=int(fw * 0.12))
                    pygame.draw.line(out, (110, 110, 130), (r.x + r.w * 0.2, r.y + r.h * 0.65), (r.x + r.w * 0.45, r.y + r.h * 0.25), max(2, lw))
                pygame.draw.rect(out, fc, r, max(2, int(fw * 0.05)), border_radius=int(fw * 0.12))
            pygame.draw.line(out, fc, (c[0] + sx * fw * 0.28, c[1] - fh * 0.03), (cx + sx * fw * 1.0, c[1] - fh * 0.06), max(2, int(fw * 0.04)))
        pygame.draw.line(out, fc, F(-0.15, -0.02), F(0.15, -0.02), max(2, int(fw * 0.05)))

    return pygame.transform.smoothscale(out, (w, h))

def male_like(gender):
    return gender != "Female"

def draw_avatar(screen, rect, gender, hair_colour, hairstyle, skin_tone, facial_hair="None", age=None, mood=60, feat=None):
    """Draws a flat cel-shaded portrait inside `rect`. `age` changes proportions,
    hair colour and lines; `mood` (0-100) changes the expression. `feat` may
    hold "eyes", "outfit" (colour 0-9), "top", "hat", "glasses", "earrings"."""
    feat = {k: v for k, v in (feat or {}).items() if k in ("eyes", "outfit", "top", "hat", "glasses", "earrings") and v is not None}
    style = style_of(hairstyle, gender)
    mood_bucket = 0 if mood < 35 else (1 if mood < 60 else (2 if mood < 85 else 3))
    age_key = None if age is None else (age if age < 4 else (4 if age < 13 else (13 if age < 18 else (18 if age < 45 else (age // 5 * 5 if age < 70 else 70)))))
    seed = (sum(hair_colour) * 7 + sum(skin_tone) * 3 + len(hairstyle)) % 97
    key = (rect.w, rect.h, gender, tuple(hair_colour), style, tuple(skin_tone), facial_hair, age_key, mood_bucket, tuple(sorted(feat.items())))
    surf = _cache.get(key)
    if surf is None:
        if len(_cache) > 160:
            _cache.clear()
        surf = _render(rect.w, rect.h, gender, tuple(hair_colour), style, tuple(skin_tone), facial_hair, age, mood, seed, feat)
        _cache[key] = surf
    screen.blit(surf, rect.topleft)
