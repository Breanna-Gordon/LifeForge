"""Little flat illustrations for events, drawn in code (no image files).

classify(text) picks a scene from the event's words; draw_scene() paints it
into a rect. Scenes are drawn at 3x and cached."""
import math
import pygame

SS = 3
_cache = {}

KEYWORDS = [
    ("crime", ("police", "steal", "stole", "arrest", "crime", "robbery", "burgl", "prison", "jail", "gang", "illegal", "smuggl", "fraud")),
    ("love", ("partner", "date", "kiss", "romance", "love", "wedding", "marry", "engaged", "crush", "ex ", "proposal", "propose", "admirer", "adopt", "baby", "child's")),
    ("family", ("parent", "mother", "father", "mum", "dad", "sibling", "brother", "sister", "grand", "family", "relative", "child", "toddler", "teenager", "your kid", "home")),
    ("health", ("health", "doctor", "ill", "flu", "injur", "hospital", "sick", "scare", "diet", "gym", "therapy", "burnt")),
    ("money", ("money", "inherit", "lottery", "bank", "invest", "bill", "tax", "debt", "pay rise", "raise", "payout", "windfall", "rent", "loan", "bonus")),
    ("work", ("job", "boss", "work", "company", "promotion", "career", "colleague", "coworker", "manager", "recruiter", "interview", "office", "redundan", "layoff", "retire", "headhunt", "hiring", "leadership")),
    ("school", ("school", "teacher", "exam", "class", "homework", "university", "course", "study", "grade", "student", "bully", "lesson", "degree", "scholarship")),
    ("party", ("party", "friend", "festival", "concert", "birthday", "club", "dinner", "invited", "celebrat", "night out", "social")),
    ("travel", ("trip", "holiday", "travel", "flight", "abroad", "move", "visa", "passport", "city")),
    ("fame", ("famous", "fame", "stage", "audition", "film", "viral", "honours", "knight", "peerage", "title", "award", "royal", "media")),
    ("sport", ("sport", "team", "match", "race", "coach", "football", "run", "swim", "athlet")),
]

def classify(text):
    t = " " + text.lower()
    for kind, words in KEYWORDS:
        if any(w in t for w in words):
            return kind
    return "nature"

SKY = {
    "work": ((38, 44, 92), (120, 100, 170)), "school": ((60, 50, 120), (190, 130, 150)), "love": ((70, 36, 96), (230, 110, 140)),
    "money": ((30, 50, 84), (80, 150, 150)), "health": ((34, 60, 90), (110, 170, 190)), "family": ((52, 42, 100), (230, 150, 110)),
    "party": ((56, 30, 100), (210, 90, 160)), "crime": ((18, 20, 40), (70, 60, 110)), "travel": ((40, 70, 130), (240, 170, 130)),
    "fame": ((36, 24, 70), (160, 80, 170)), "sport": ((30, 70, 90), (120, 190, 140)), "nature": ((42, 48, 100), (240, 170, 120)),
}

def _grad(S, c1, c2):
    w, h = S.get_size()
    for y in range(h):
        t = y / max(1, h - 1)
        pygame.draw.line(S, tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)), (0, y), (w, y))

def _stars(S, seed=1):
    import random
    r = random.Random(seed)
    w, h = S.get_size()
    for _ in range(26):
        pygame.draw.circle(S, (255, 255, 255, 0) if False else (255, 246, 220), (r.randint(0, w), r.randint(0, int(h * 0.55))), r.choice((1, 1, 2)))

def _hills(S, col, base=0.78, amp=0.08, ph=0.0):
    w, h = S.get_size()
    pts = [(0, h)]
    for x in range(0, w + 8, 8):
        pts.append((x, h * base + math.sin(x / w * 5 + ph) * h * amp))
    pts.append((w, h))
    pygame.draw.polygon(S, col, pts)

def _beam(S, pts, col):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = int(min(xs)), int(min(ys))
    tmp = pygame.Surface((int(max(xs)) - x0 + 2, int(max(ys)) - y0 + 2), pygame.SRCALPHA)
    pygame.draw.polygon(tmp, col, [(x - x0, y - y0) for x, y in pts])
    S.blit(tmp, (x0, y0))

def _rr(S, col, rect, r=0):
    pygame.draw.rect(S, col, rect, border_radius=int(r))

def _window(S, x, y, w, h, on=True):
    pygame.draw.rect(S, (255, 214, 130) if on else (70, 70, 110), (x, y, w, h), border_radius=2)

def _heart(S, cx, cy, s, col):
    pts = []
    for i in range(60):
        t = i / 60 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * s / 16, cy - y * s / 16))
    pygame.draw.polygon(S, col, pts)

def _star(S, cx, cy, r, col, n=5):
    pts = []
    for i in range(n * 2):
        a = -math.pi / 2 + i * math.pi / n
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    pygame.draw.polygon(S, col, pts)

def _paint(kind, S):
    w, h = S.get_size()
    u = h / 100.0
    c1, c2 = SKY.get(kind, SKY["nature"])
    _grad(S, c1, c2)
    _stars(S, hash(kind) % 50)
    if kind == "work":
        for x, bw, bh in ((0.04, 0.12, 0.45), (0.17, 0.1, 0.6), (0.7, 0.13, 0.5), (0.85, 0.12, 0.62)):
            _rr(S, (34, 34, 78), (w * x, h * (1 - bh), w * bw, h * bh))
            for k in range(4):
                _window(S, w * x + w * bw * 0.2, h * (1 - bh) + u * (8 + k * 12), w * bw * 0.25, u * 6, k % 2 == 0)
        _rr(S, (60, 44, 96), (0, h * 0.78, w, h * 0.22))
        _rr(S, (42, 150, 160), (w * 0.28, h * 0.30, w * 0.34, h * 0.32), u * 3)
        _rr(S, (22, 30, 60), (w * 0.29, h * 0.32, w * 0.32, h * 0.26), u * 2)
        for k in range(4):
            pygame.draw.line(S, (130, 220, 200), (w * 0.32, h * (0.37 + 0.05 * k)), (w * (0.40 + 0.07 * (k % 3)), h * (0.37 + 0.05 * k)), max(1, int(u * 1.4)))
        _rr(S, (42, 150, 160), (w * 0.44, h * 0.62, w * 0.04, h * 0.14))
        _rr(S, (42, 150, 160), (w * 0.38, h * 0.74, w * 0.16, h * 0.04), u)
        _rr(S, (240, 240, 240), (w * 0.70, h * 0.62, w * 0.08, h * 0.12), u * 2)
        pygame.draw.arc(S, (240, 240, 240), (w * 0.76, h * 0.64, w * 0.04, h * 0.07), -1.5, 1.5, max(1, int(u)))
        pygame.draw.line(S, (255, 214, 130), (w * 0.15, h * 0.78), (w * 0.15, h * 0.52), int(u * 2))
        pygame.draw.polygon(S, (255, 214, 130), [(w * 0.11, h * 0.52), (w * 0.19, h * 0.52), (w * 0.17, h * 0.42), (w * 0.13, h * 0.42)])
    elif kind == "school":
        _hills(S, (50, 40, 96), 0.8, 0.05)
        _rr(S, (240, 220, 200), (w * 0.28, h * 0.4, w * 0.44, h * 0.42))
        pygame.draw.polygon(S, (200, 90, 90), [(w * 0.25, h * 0.4), (w * 0.5, h * 0.18), (w * 0.75, h * 0.4)])
        for k in range(4):
            _window(S, w * (0.33 + 0.1 * k), h * 0.5, w * 0.06, h * 0.12, True)
        _rr(S, (120, 70, 60), (w * 0.46, h * 0.64, w * 0.08, h * 0.18), 3)
        pygame.draw.line(S, (230, 230, 230), (w * 0.5, h * 0.18), (w * 0.5, h * 0.05), int(u * 1.5))
        pygame.draw.polygon(S, (255, 190, 80), [(w * 0.5, h * 0.05), (w * 0.62, h * 0.09), (w * 0.5, h * 0.13)])
        _hills(S, (34, 70, 70), 0.9, 0.03, 2)
    elif kind == "love":
        pygame.draw.circle(S, (255, 236, 190), (int(w * 0.8), int(h * 0.22)), int(u * 12))
        _heart(S, w * 0.5, h * 0.5, u * 52, (240, 90, 120))
        _heart(S, w * 0.5 - u * 6, h * 0.46 - u * 7, u * 18, (255, 170, 190))
        for x, y, s in ((0.2, 0.3, 14), (0.78, 0.6, 18), (0.3, 0.72, 10), (0.68, 0.22, 10)):
            _heart(S, w * x, h * y, u * s, (255, 150, 180))
    elif kind == "money":
        _hills(S, (28, 60, 70), 0.85, 0.04)
        for i in range(5):
            _rr(S, (240, 190, 70), (w * 0.2, h * (0.74 - i * 0.075), w * 0.2, h * 0.065), u * 3)
            _rr(S, (255, 220, 120), (w * 0.2, h * (0.74 - i * 0.075), w * 0.2, h * 0.025), u * 2)
        for i in range(3):
            _rr(S, (240, 190, 70), (w * 0.47, h * (0.74 - i * 0.075), w * 0.2, h * 0.065), u * 3)
        _rr(S, (110, 200, 140), (w * 0.62, h * 0.3, w * 0.26, h * 0.16), u * 2)
        pygame.draw.circle(S, (70, 150, 100), (int(w * 0.75), int(h * 0.38)), int(u * 5))
        pygame.draw.circle(S, (255, 220, 120), (int(w * 0.8), int(h * 0.22)), int(u * 10))
        pygame.draw.circle(S, (230, 170, 50), (int(w * 0.8), int(h * 0.22)), int(u * 10), max(1, int(u)))
    elif kind == "health":
        _hills(S, (30, 70, 96), 0.86, 0.03)
        _rr(S, (250, 250, 250), (w * 0.38, h * 0.2, w * 0.24, h * 0.5), u * 6)
        _rr(S, (230, 80, 90), (w * 0.47, h * 0.28, w * 0.06, h * 0.34), u)
        _rr(S, (230, 80, 90), (w * 0.41, h * 0.4, w * 0.18, h * 0.1), u)
        pts = [(w * 0.05, h * 0.82), (w * 0.2, h * 0.82), (w * 0.26, h * 0.66), (w * 0.32, h * 0.92), (w * 0.38, h * 0.82), (w * 0.95, h * 0.82)]
        pygame.draw.lines(S, (130, 230, 200), False, pts, max(2, int(u * 2)))
    elif kind == "family":
        _hills(S, (60, 50, 100), 0.82, 0.05)
        pygame.draw.polygon(S, (200, 90, 80), [(w * 0.28, h * 0.42), (w * 0.5, h * 0.2), (w * 0.72, h * 0.42)])
        _rr(S, (246, 226, 200), (w * 0.31, h * 0.42, w * 0.38, h * 0.38))
        _window(S, w * 0.36, h * 0.52, w * 0.09, h * 0.14)
        _window(S, w * 0.55, h * 0.52, w * 0.09, h * 0.14)
        _rr(S, (120, 70, 60), (w * 0.47, h * 0.6, w * 0.06, h * 0.2), 2)
        _rr(S, (150, 100, 70), (w * 0.62, h * 0.24, w * 0.05, h * 0.12))
        for x in (0.1, 0.9):
            pygame.draw.circle(S, (46, 110, 90), (int(w * x), int(h * 0.58)), int(u * 14))
            _rr(S, (90, 60, 50), (w * x - u * 2, h * 0.64, u * 4, h * 0.18))
        _hills(S, (36, 80, 70), 0.9, 0.03, 1)
    elif kind == "party":
        for i, col in enumerate(((255, 120, 150), (255, 200, 90), (120, 200, 255), (170, 130, 255), (120, 230, 170))):
            x = w * (0.14 + i * 0.18)
            pygame.draw.circle(S, col, (int(x), int(h * (0.3 + (i % 2) * 0.12))), int(u * 13))
            pygame.draw.line(S, (230, 230, 240), (x, h * (0.3 + (i % 2) * 0.12) + u * 13), (w * 0.5, h * 0.95), max(1, int(u * 0.8)))
        for k in range(14):
            pygame.draw.circle(S, [(255, 214, 130), (255, 130, 170), (130, 220, 255)][k % 3], (int(w * (k + 0.5) / 14), int(h * 0.08 + math.sin(k) * u * 3)), int(u * 2.2))
        pygame.draw.line(S, (200, 190, 230), (0, h * 0.08), (w, h * 0.08), 1)
        _hills(S, (40, 28, 80), 0.88, 0.03)
    elif kind == "crime":
        for x, bw, bh in ((0.0, 0.2, 0.6), (0.22, 0.16, 0.45), (0.64, 0.18, 0.55), (0.84, 0.16, 0.7)):
            _rr(S, (22, 22, 50), (w * x, h * (1 - bh), w * bw, h * bh))
        pygame.draw.line(S, (110, 110, 140), (w * 0.5, h * 0.9), (w * 0.5, h * 0.3), int(u * 2))
        pygame.draw.circle(S, (255, 220, 140), (int(w * 0.5), int(h * 0.27)), int(u * 6))
        _beam(S, [(w * 0.5, h * 0.3), (w * 0.4, h * 0.9), (w * 0.6, h * 0.9)], (255, 220, 140, 60))
        _rr(S, (30, 30, 60), (0, h * 0.9, w, h * 0.1))
        _rr(S, (230, 60, 70), (w * 0.8, h * 0.18, w * 0.08, h * 0.07), 2)
        _rr(S, (70, 120, 255), (w * 0.88, h * 0.18, w * 0.08, h * 0.07), 2)
    elif kind == "travel":
        _hills(S, (60, 70, 130), 0.86, 0.06)
        for x, y, s in ((0.2, 0.7, 16), (0.7, 0.8, 20), (0.45, 0.3, 12)):
            for dx in (-1, 0, 1):
                pygame.draw.circle(S, (250, 230, 240), (int(w * x + dx * u * s * 0.7), int(h * y)), int(u * s * 0.55))
        pygame.draw.polygon(S, (250, 250, 255), [(w * 0.3, h * 0.5), (w * 0.62, h * 0.43), (w * 0.72, h * 0.46), (w * 0.62, h * 0.5)])
        pygame.draw.polygon(S, (200, 210, 235), [(w * 0.44, h * 0.48), (w * 0.52, h * 0.3), (w * 0.56, h * 0.31), (w * 0.52, h * 0.49)])
        pygame.draw.polygon(S, (200, 210, 235), [(w * 0.44, h * 0.5), (w * 0.52, h * 0.66), (w * 0.56, h * 0.65), (w * 0.52, h * 0.49)])
        pygame.draw.circle(S, (255, 214, 140), (int(w * 0.82), int(h * 0.22)), int(u * 11))
    elif kind == "fame":
        for dx in (-0.22, 0, 0.22):
            _beam(S, [(w * (0.5 + dx * 0.25), 0), (w * (0.5 + dx * 0.25) + u * 6, 0), (w * (0.5 + dx * 1.2) + u * 20, h * 0.85), (w * (0.5 + dx * 1.2) - u * 20, h * 0.85)], (255, 240, 200, 60))
        _rr(S, (60, 30, 80), (0, h * 0.82, w, h * 0.18))
        _rr(S, (150, 70, 140), (w * 0.2, h * 0.78, w * 0.6, h * 0.06), u * 2)
        _star(S, w * 0.5, h * 0.44, u * 22, (255, 214, 100))
        _star(S, w * 0.22, h * 0.3, u * 8, (255, 230, 160))
        _star(S, w * 0.8, h * 0.34, u * 10, (255, 230, 160))
    elif kind == "sport":
        _rr(S, (50, 150, 100), (0, h * 0.68, w, h * 0.32))
        for k in range(5):
            pygame.draw.line(S, (230, 240, 230), (w * (0.1 + 0.2 * k), h * 0.68), (w * (0.0 + 0.25 * k), h), max(1, int(u)))
        pygame.draw.circle(S, (250, 250, 250), (int(w * 0.5), int(h * 0.44)), int(u * 20))
        for a in range(0, 360, 72):
            pygame.draw.circle(S, (40, 40, 60), (int(w * 0.5 + math.cos(math.radians(a)) * u * 10), int(h * 0.44 + math.sin(math.radians(a)) * u * 10)), int(u * 4))
        pygame.draw.line(S, (240, 240, 240), (w * 0.08, h * 0.68), (w * 0.08, h * 0.3), int(u * 2))
        pygame.draw.line(S, (240, 240, 240), (w * 0.08, h * 0.3), (w * 0.24, h * 0.3), int(u * 2))
    else:  # nature
        pygame.draw.circle(S, (255, 214, 140), (int(w * 0.72), int(h * 0.38)), int(u * 18))
        _hills(S, (80, 80, 150), 0.62, 0.07)
        _hills(S, (56, 90, 120), 0.74, 0.06, 2)
        _hills(S, (34, 78, 80), 0.86, 0.05, 4)
        for x in (0.15, 0.25, 0.85):
            _rr(S, (80, 56, 50), (w * x - u * 1.5, h * 0.74, u * 3, h * 0.14))
            pygame.draw.polygon(S, (30, 100, 80), [(w * x, h * 0.5), (w * x - u * 9, h * 0.78), (w * x + u * 9, h * 0.78)])

def draw_scene(screen, rect, kind, radius=14):
    key = (kind, rect.w, rect.h)
    surf = _cache.get(key)
    if surf is None:
        big = pygame.Surface((rect.w * SS, rect.h * SS), pygame.SRCALPHA)
        _paint(kind, big)
        small = pygame.transform.smoothscale(big, (rect.w, rect.h))
        mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.w, rect.h), border_radius=radius)
        small.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf = small
        if len(_cache) > 60:
            _cache.clear()
        _cache[key] = surf
    screen.blit(surf, rect.topleft)
    try:
        import nightmode
        nightmode.keep(screen, surf, rect.topleft)
    except Exception:
        pass
