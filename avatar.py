import math
import pygame

# Stylised illustrated avatars: shaped faces, almond eyes, defined noses and
# lips, layered hair with highlights, and layered clothes. Everything is drawn
# at 4x and scaled down for smooth edges, and cached.
SS = 4
_cache = {}

def _shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])

def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def _spline(pts, closed=True, n=8):
    """Catmull-Rom curve through the points, so shapes are smooth."""
    out = []
    count = len(pts)
    rng = range(count) if closed else range(count - 1)
    for i in rng:
        p0 = pts[(i - 1) % count] if closed or i > 0 else pts[0]
        p1 = pts[i]
        p2 = pts[(i + 1) % count]
        p3 = pts[(i + 2) % count] if closed or i + 2 < count else pts[-1]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append((0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                        0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)))
    if not closed:
        out.append(pts[-1])
    return out

def _mirror(half):
    """half: points with x>=0 from the top-centre down to the bottom-centre."""
    left = [(-x, y) for x, y in reversed(half) if x != 0]
    return half + left

def _shape(S, pts, fill, line=0.55, w=3, alpha=255):
    if alpha < 255:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0, y0 = int(min(xs)) - 2, int(min(ys)) - 2
        tmp = pygame.Surface((int(max(xs)) - x0 + 4, int(max(ys)) - y0 + 4), pygame.SRCALPHA)
        shifted = [(x - x0, y - y0) for x, y in pts]
        pygame.draw.polygon(tmp, (*fill[:3], alpha), shifted)
        S.blit(tmp, (x0, y0))
        return
    pygame.draw.polygon(S, fill, pts)
    if line and w:
        pygame.draw.lines(S, _shade(fill, line), True, pts, w)

def _stage(age):
    if age is None: return "adult"
    if age < 7: return "baby"
    if age < 13: return "child"
    if age < 20: return "teen"
    if age < 65: return "adult"
    return "elder"

def _hair_for_age(colour, age):
    if age is None or age < 45:
        return colour
    return _mix(colour, (205, 205, 210), min(1.0, (age - 45) / 25))

PALETTES = {
    "Male": [((70, 98, 62), (150, 190, 230), (120, 170, 220)),     # olive jacket, blue shirt
             ((60, 70, 110), (235, 235, 240), (200, 200, 215)),     # navy, white shirt
             ((120, 60, 60), (230, 215, 190), (200, 180, 150))],    # maroon, cream
    "Female": [((226, 160, 130), (210, 220, 190), (200, 165, 130)),   # peach knit, sage collar, beige
               ((120, 90, 150), (240, 235, 245), (200, 190, 220)),     # purple, white
               ((70, 120, 120), (240, 225, 200), (225, 205, 170))],    # teal, cream
}

def _render(w, h, gender, hair, style, skin, facial, age, mood, seed):
    W, H = w * SS, h * SS
    u = min(W, H)
    female = gender == "Female"
    stage = _stage(age)
    baby, child, elder = stage == "baby", stage == "child", stage == "elder"
    young = baby or child
    hair = _hair_for_age(hair, age)
    hair_hi = _mix(hair, (255, 255, 255), 0.28)
    hair_lo = _shade(hair, 0.6)
    skin_l = _mix(skin, (255, 255, 255), 0.18)
    skin_d = _shade(skin, 0.86)
    skin_dd = _shade(skin, 0.7)
    lw = max(2, int(u * 0.0055))

    cx = W / 2
    cy = H * 0.40
    # proportions
    fw = u * (0.205 if not female else 0.19) * (1.4 if baby else 1.2 if child else 0.97 if stage=='teen' else 1.0)
    fsc = 1.0 if not young else (0.82 if baby else 0.92)   # face length scale (kids have rounder faces)
    sc = u * fsc

    def P(x, y):
        return (cx + x, cy + y)

    body = pygame.Surface((W, H), pygame.SRCALPHA)
    head = pygame.Surface((W, H), pygame.SRCALPHA)

    # ---------------- body & clothes ----------------
    pal = PALETTES[gender if gender in PALETTES else "Male"][seed % 3]
    outer, inner, under = pal
    if stage == "baby": outer, inner, under = (255, 226, 150), (255, 240, 200), (255, 226, 150)
    elif stage == "child": outer, inner, under = ((96, 190, 150) if not female else (250, 170, 90)), (255, 255, 255), (255, 255, 255)
    elif elder: outer = _mix(outer, (150, 150, 158), 0.4)
    shoulder_w = 0.62 if not baby else 0.46
    top = cy + (0.34 if baby else 0.39 if child else 0.44 if elder else 0.42) * u
    bust = [(cx - shoulder_w * u, H + 4), (cx - (shoulder_w - 0.04) * u, top + 0.2 * u), (cx - 0.38 * u, top + 0.07 * u),
            (cx - 0.16 * u, top - 0.02 * u), (cx + 0.16 * u, top - 0.02 * u), (cx + 0.38 * u, top + 0.07 * u),
            (cx + (shoulder_w - 0.04) * u, top + 0.2 * u), (cx + shoulder_w * u, H + 4)]
    if stage == "teen":        # hoodie bulk behind the neck
        hood = _spline([(cx - 0.3 * u, top + 0.05 * u), (cx - 0.2 * u, top - 0.08 * u), (cx + 0.2 * u, top - 0.08 * u), (cx + 0.3 * u, top + 0.05 * u),
                        (cx, top + 0.16 * u)], True, 8)
        _shape(body, hood, _shade(outer, 0.85), 0.5, lw)
    _shape(body, _spline(bust, False, 8) + [(cx + shoulder_w * u, H + 4), (cx - shoulder_w * u, H + 4)], outer, 0.55, lw)
    # neck
    nk = 0.095 * u if female else 0.118 * u
    neck = [(cx - nk, cy + 0.2 * u), (cx - nk * 1.05, top + 0.02 * u), (cx + nk * 1.05, top + 0.02 * u), (cx + nk, cy + 0.2 * u)]
    if stage in ("teen", "adult", "elder") and under != inner:
        # turtleneck / undershirt, collar of the inner shirt, open outer layer
        _shape(body, _spline([(cx - nk * 1.2, top - 0.02 * u), (cx - nk * 1.1, top - 0.08 * u), (cx + nk * 1.1, top - 0.08 * u),
                              (cx + nk * 1.2, top - 0.02 * u), (cx, top + 0.24 * u)], True, 6), under, 0.6, lw)
    _shape(body, neck, skin_d, 0.8, lw)
    if stage in ("teen", "adult", "elder"):
        # V opening: skin, undershirt, shirt collar, outer lapels
        v = [(cx - nk * 1.1, top - 0.02 * u), (cx + nk * 1.1, top - 0.02 * u), (cx, top + 0.26 * u)]
        _shape(body, v, skin_d if under == inner else under, 0.6, lw)
        for sx in (-1, 1):
            collar = [(cx + sx * nk * 0.9, top - 0.05 * u), (cx + sx * nk * 2.4, top + 0.02 * u), (cx + sx * nk * 1.7, top + 0.17 * u),
                      (cx + sx * 0.02 * u, top + 0.2 * u)]
            _shape(body, collar, inner, 0.7, lw)
            lap = [(cx + sx * nk * 2.1, top + 0.0 * u), (cx + sx * nk * 3.4, top + 0.12 * u), (cx + sx * nk * 2.4, top + 0.32 * u),
                   (cx + sx * nk * 1.1, top + 0.3 * u)]
            _shape(body, lap, _shade(outer, 0.88), 0.55, lw)
        # plaid hint on the inner shirt for men
        if not female and inner != (235, 235, 240):
            for k in range(4):
                for sx in (-1, 1):
                    pygame.draw.line(body, _shade(inner, 0.85), (cx + sx * nk * (1.1 + k * 0.5), top + 0.02 * u),
                                     (cx + sx * nk * (0.8 + k * 0.35), top + 0.15 * u), max(1, lw - 1))
    else:
        _shape(body, _spline([(cx - nk * 1.4, top + 0.01 * u), (cx, top + 0.1 * u), (cx + nk * 1.4, top + 0.01 * u),
                              (cx, top - 0.04 * u)], True, 6), skin_d, 0.7, lw)
    # a soft shadow under the chin on the neck
    sh = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (*skin_dd, 110), pygame.Rect(int(cx - nk * 1.2), int(cy + 0.2 * u), int(nk * 2.4), int(0.12 * u)))
    body.blit(sh, (0, 0))
    # fabric fold lines
    for sx in (-1, 1):
        pygame.draw.arc(body, _shade(outer, 0.8), pygame.Rect(int(cx + sx * 0.3 * u - 0.1 * u), int(top + 0.22 * u), int(0.2 * u), int(0.28 * u)),
                        math.pi * (0.1 if sx > 0 else 0.55), math.pi * (0.45 if sx > 0 else 0.9), lw)
    if age is not None and age >= 25 and not young and not female and seed % 3 == 0:
        for k in range(9):    # a chain necklace
            a = math.pi * (0.1 + 0.8 * k / 8)
            pygame.draw.circle(body, (210, 210, 220), (int(cx + math.cos(a) * nk * 1.7), int(top + 0.03 * u + math.sin(a) * 0.19 * u)), max(2, lw))

    # ---------------- back hair ----------------
    def hair_shape(pts, fill=hair, line=0.5, alpha=255):
        _shape(head, pts, fill, line, lw, alpha)

    hair_scale = 0.9 if baby else 1.0
    if style == "Long" and not baby:
        half = [(0, -0.345), (0.17, -0.335), (0.275, -0.26), (0.32, -0.12), (0.34, 0.1), (0.37, 0.3), (0.36, 0.46), (0.3, 0.5), (0.21, 0.46), (0.0, 0.46)]
        back = [P(x, y) for x, y in _spline(_mirror([(x * u, y * sc) for x, y in half]), True, 8)]
        hair_shape(back, hair_lo)
    elif style == "Ponytail" and not baby:
        tail = _spline([(0.17 * u, -0.17 * sc), (0.33 * u, -0.1 * sc), (0.4 * u, 0.12 * sc), (0.37 * u, 0.38 * sc), (0.3 * u, 0.46 * sc),
                        (0.28 * u, 0.3 * sc), (0.24 * u, 0.1 * sc)], True, 8)
        hair_shape([P(x, y) for x, y in tail], hair_lo)
    elif style == "Curly" and not baby:
        for a in range(0, 360, 28):
            r = u * 0.075
            x = math.cos(math.radians(a)) * u * 0.265
            y = -math.sin(math.radians(a)) * u * 0.27 * (sc / u) - 0.02 * u
            if a > 180 and a < 360 and y > -0.02 * u: continue
            pygame.draw.circle(head, hair_lo, (int(cx + x), int(cy + y)), int(r))

    # ---------------- face ----------------
    chin = 0.325 if female else 0.335
    half = [(0, -0.27), (0.74, -0.255), (0.96, -0.15), (1.0, -0.02), (0.97, 0.1), (0.86 if not female else 0.78, 0.2),
            (0.55 if not female else 0.46, 0.285), (0.24 if not female else 0.16, chin - 0.012), (0, chin)]
    if young:
        half = [(0, -0.26), (0.8, -0.24), (1.02, -0.1), (1.04, 0.03), (0.96, 0.14), (0.78, 0.22), (0.5, 0.275), (0.22, 0.3), (0, 0.305)]
    face_pts = _mirror([(x * fw, y * sc) for x, y in half])
    face = _spline([P(x, y) for x, y in face_pts], True, 8)
    # ears first (behind the face)
    for sx in (-1, 1):
        ear = _spline([P(sx * fw * 0.96, -0.03 * u), P(sx * fw * 1.12, -0.04 * u), P(sx * fw * 1.17, 0.04 * u), P(sx * fw * 1.08, 0.11 * u),
                       P(sx * fw * 0.98, 0.1 * u)], True, 6)
        _shape(head, ear, skin, 0.6, lw)
        pygame.draw.arc(head, skin_d, pygame.Rect(int(cx + sx * fw * 1.07 - 0.015 * u), int(cy + 0.0 * u), int(0.03 * u), int(0.07 * u)),
                        math.pi * (1.5 if sx > 0 else 0.5), math.pi * (2.5 if sx > 0 else 1.5), lw)
    _shape(head, face, skin, 0.6, lw)
    # form shadow along the right side and under the cheek, light on the left
    shade_layer = pygame.Surface((W, H), pygame.SRCALPHA)
    right = [P(x * fw, y * sc) for x, y in half[2:]]
    inner_pts = [P(x * fw * 0.8, y * sc) for x, y in reversed(half[2:])]
    pygame.draw.polygon(shade_layer, (*skin_dd, 70), _spline(right + inner_pts, True, 5))
    pygame.draw.ellipse(shade_layer, (*skin_l, 70), pygame.Rect(int(cx - fw * 0.75), int(cy - 0.2 * u), int(fw * 0.7), int(0.1 * u)))
    for sx in (-1, 1):   # blush
        pygame.draw.circle(shade_layer, (235, 100, 110, 60 if not male_like(gender) else 40), (int(cx + sx * fw * 0.58), int(cy + 0.095 * u)), int(0.045 * u))
    head.blit(shade_layer, (0, 0))

    # ---------------- eyes ----------------
    ex = fw * 0.47
    ey = cy + (0.032 if baby else 0.014 if child else -0.015) * u
    a_ = u * (0.058 if not young else (0.072 if baby else 0.065)) * (1.08 if female else 1.0)
    b_ = u * (0.026 if not young else (0.047 if baby else 0.038)) * (1.12 if female else 1.0)
    for sx in (-1, 1):
        def E(x, y):   # x: toward outer corner
            return (cx + sx * (ex + x * a_), ey + y * b_)
        shape_pts = _spline([E(-1.0, 0.1), E(-0.55, -0.85), E(0.2, -1.05), E(0.8, -0.65), E(1.05, -0.2), E(0.7, 0.45), E(0.0, 0.85), E(-0.6, 0.55)], True, 8)
        layer = pygame.Surface((W, H), pygame.SRCALPHA)
        mask = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(layer, (250, 248, 245), shape_pts)
        pygame.draw.polygon(mask, (255, 255, 255, 255), shape_pts)
        ic = E(0.05, 0.0)
        pygame.draw.circle(layer, (84, 58, 42), ic, int(b_ * 0.98))
        pygame.draw.circle(layer, (36, 24, 20), ic, int(b_ * 0.52))
        pygame.draw.circle(layer, (255, 255, 255), (int(ic[0] - b_ * 0.3), int(ic[1] - b_ * 0.3)), max(2, int(b_ * 0.22)))
        pygame.draw.ellipse(layer, (0, 0, 0, 50), pygame.Rect(int(ic[0] - b_), int(ic[1] - b_), int(b_ * 2), int(b_ * 0.9)))   # lid shadow on the iris
        layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        head.blit(layer, (0, 0))
        upper = _spline([E(-1.0, 0.1), E(-0.55, -0.85), E(0.2, -1.05), E(0.8, -0.65), E(1.05, -0.2)], False, 8)
        pygame.draw.lines(head, _shade(hair if sum(hair) > 90 else (50, 38, 36), 0.5), False, upper, max(lw + 2, int(u * 0.0085)))
        if female and not baby:      # wing + lashes
            pygame.draw.line(head, (40, 30, 30), E(1.05, -0.2), E(1.4, -0.5), max(lw, 3))
        lower = _spline([E(-0.6, 0.55), E(0.0, 0.85), E(0.7, 0.45)], False, 6)
        pygame.draw.lines(head, skin_dd, False, lower, max(2, lw - 1))
        # crease above the eye
        crease = _spline([E(-0.7, -1.35), E(0.1, -1.55), E(0.9, -1.15)], False, 6)
        pygame.draw.lines(head, skin_d, False, crease, max(2, lw - 1))
        # eyebrows
        thick = u * (0.0165 if not female else 0.011) * (1.0 if not young else 0.8)
        by = ey - (u * 0.058 if not young else b_ * 2.1)
        sad = mood < 35
        bx0, bx1 = ex - a_ * 1.0, ex + a_ * 1.15
        lift = u * 0.014 * (1 if sad else 0)
        up = [(cx + sx * bx0, by - lift * 1.2 + (0.003 * u)), (cx + sx * (ex - a_ * 0.1), by - u * 0.012 - thick * 0.8 - lift * 0.4),
              (cx + sx * (ex + a_ * 0.7), by - u * 0.014 - thick * 0.9 + lift * 0.4), (cx + sx * bx1, by + u * 0.01 + lift * 0.5)]
        lo = [(cx + sx * bx1, by + u * 0.012 + lift * 0.5), (cx + sx * (ex + a_ * 0.7), by - u * 0.004 + lift * 0.4), (cx + sx * (ex - a_ * 0.1), by - u * 0.002 - lift * 0.3),
              (cx + sx * bx0, by + thick * 0.8 - lift * 1.2)]
        brow = _spline(up + lo, True, 6)
        _shape(head, brow, _shade(hair, 0.55) if sum(hair) > 120 else hair, None, 0)

    # ---------------- nose ----------------
    nb = cy - 0.025 * u
    ntip = cy + (0.075 if not young else (0.085 if baby else 0.072)) * u
    nw = u * (0.04 if not young else 0.022)
    pygame.draw.lines(head, skin_dd, False, _spline([(cx + 0.012 * u, nb), (cx + 0.02 * u, cy + 0.02 * u), (cx + 0.016 * u, ntip - 0.012 * u)], False, 6), max(2, lw - 1))
    nl = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.polygon(nl, (*skin_dd, 55), [(cx + 0.012 * u, nb), (cx + 0.05 * u, cy + 0.03 * u), (cx + nw, ntip), (cx + 0.016 * u, ntip - 0.012 * u)])
    pygame.draw.ellipse(nl, (*skin_l, 110), pygame.Rect(int(cx - 0.016 * u), int(ntip - 0.03 * u), int(0.026 * u), int(0.022 * u)))
    head.blit(nl, (0, 0))
    for sx in (-1, 1):
        pygame.draw.arc(head, skin_dd, pygame.Rect(int(cx + sx * nw * 0.9 - 0.014 * u), int(ntip - 0.018 * u), int(0.028 * u), int(0.026 * u)),
                        math.pi * 0.9, math.pi * 2.1, max(2, lw))
    pygame.draw.arc(head, skin_dd, pygame.Rect(int(cx - nw * 0.9), int(ntip - 0.015 * u), int(nw * 1.8), int(0.026 * u)), math.pi * 1.1, math.pi * 1.9, max(2, lw))

    # ---------------- facial hair under the mouth ----------------
    my = cy + (0.168 if not young else (0.155 if baby else 0.16)) * u
    mw = u * (0.058 if not young else 0.04)
    has_fh = (not female) and facial != "None" and (age is None or age >= 15)
    if has_fh and facial == "Beard":
        outer_edge = [P(x * fw * 0.99, y * sc * 0.99) for x, y in half[4:]]
        beard_top = [(cx + mw * 1.9, my - 0.02 * u), (cx + mw * 1.3, my + 0.045 * u), (cx, my + 0.05 * u)]
        right_b = outer_edge + [(cx + mw * 1.2, my + 0.055 * u), (cx + mw * 1.6, my + 0.01 * u), (cx + mw * 2.0, my - 0.03 * u)]
        for sx in (-1, 1):
            pts = [(cx + sx * (p[0] - cx), p[1]) for p in right_b]
            _shape(head, _spline(pts, True, 5) if False else pts, hair, 0.5, lw)
        _shape(head, [(cx - fw * 0.5, my + 0.05 * u), (cx + fw * 0.5, my + 0.05 * u), (cx + fw * 0.22, cy + chin * sc), (cx - fw * 0.22, cy + chin * sc)], hair, 0.5, lw)
    elif has_fh and facial == "Stubble":
        st = pygame.Surface((W, H), pygame.SRCALPHA)
        sub = [P(x * fw * 0.97, y * sc * 0.98) for x, y in half[4:]]
        inner_s = [P(x * fw * 0.62, (y - 0.03) * sc) for x, y in reversed(half[4:])]
        poly = sub + inner_s
        pygame.draw.polygon(st, (*hair, 75), poly)
        pygame.draw.polygon(st, (*hair, 75), [(2 * cx - p[0], p[1]) for p in poly])
        pygame.draw.polygon(st, (*hair, 70), [(cx - mw * 1.6, my - 0.03 * u), (cx + mw * 1.6, my - 0.03 * u), (cx + mw * 1.2, my + 0.02 * u), (cx - mw * 1.2, my + 0.02 * u)])
        head.blit(st, (0, 0))

    # ---------------- mouth ----------------
    corner = (-0.012 if mood >= 60 else (-0.004 if mood >= 35 else 0.012)) * u
    lipc = _mix(skin, (196, 84, 96), 0.62 if female else 0.38)
    upper = _spline([(cx - mw, my + corner), (cx - mw * 0.45, my - 0.014 * u), (cx, my - 0.009 * u), (cx + mw * 0.45, my - 0.014 * u),
                     (cx + mw, my + corner), (cx, my + 0.003 * u)], True, 6)
    lower = _spline([(cx - mw, my + corner), (cx, my + 0.003 * u), (cx + mw, my + corner), (cx + mw * 0.5, my + 0.026 * u + corner * -0.3),
                     (cx, my + 0.03 * u), (cx - mw * 0.5, my + 0.026 * u + corner * -0.3)], True, 6)
    _shape(head, lower, _mix(lipc, (255, 255, 255), 0.08), 0.7, max(1, lw - 1))
    _shape(head, upper, _shade(lipc, 0.9), 0.7, max(1, lw - 1))
    pygame.draw.ellipse(head, _mix(lipc, (255, 255, 255), 0.45), pygame.Rect(int(cx - mw * 0.3), int(my + 0.01 * u), int(mw * 0.6), int(0.009 * u)))
    if has_fh and facial in ("Moustache", "Beard"):
        for sx in (-1, 1):
            mp = _spline([(cx, my - 0.026 * u), (cx + sx * mw * 1.0, my - 0.032 * u), (cx + sx * mw * 1.9, my - 0.006 * u),
                          (cx + sx * mw * 1.5, my + 0.018 * u), (cx + sx * mw * 0.6, my - 0.012 * u)], True, 6)
            _shape(head, mp, hair, 0.5, lw)

    # ---------------- age lines & glasses ----------------
    if age is not None and age >= 50:
        for sx in (-1, 1):
            for k in range(3 if age >= 65 else 1):
                pygame.draw.line(head, skin_dd, (cx + sx * (ex + a_ * 1.2), ey + (k - 1) * b_ * 0.4), (cx + sx * (ex + a_ * 1.9), ey + (k - 1) * b_ * 0.9), max(1, lw - 1))
            pygame.draw.arc(head, skin_dd, pygame.Rect(int(cx + sx * 0.07 * u - 0.05 * u), int(cy + 0.1 * u), int(0.1 * u), int(0.12 * u)),
                            math.pi * (1.55 if sx > 0 else 1.0), math.pi * (2.0 if sx > 0 else 1.45), max(1, lw - 1))
        pygame.draw.arc(head, skin_dd, pygame.Rect(int(cx - fw * 0.5), int(cy - 0.2 * u), int(fw), int(0.08 * u)), math.pi * 0.15, math.pi * 0.85, max(1, lw - 1))
    if elder:
        for sx in (-1, 1):
            pygame.draw.arc(head, skin_dd, pygame.Rect(int(cx + sx * ex - a_ * 0.9), int(ey + b_ * 0.9), int(a_ * 1.8), int(b_ * 1.6)), math.pi * 1.05, math.pi * 1.95, max(1, lw - 1))
            for k in range(4):
                pygame.draw.circle(head, _shade(skin, 0.75), (int(cx + sx * fw * (0.55 + 0.1 * k)), int(ey + b_ * (3 + k % 2))), max(2, lw - 1))
            pygame.draw.line(head, skin_dd, (cx + sx * mw * 1.6, my - 0.01 * u), (cx + sx * mw * 2.2, my + 0.05 * u), max(1, lw - 1))
    if age is not None and age >= 65:
        for sx in (-1, 1):
            r = pygame.Rect(int(cx + sx * ex - a_ * 1.4), int(ey - b_ * 1.9), int(a_ * 2.8), int(b_ * 3.6))
            pygame.draw.rect(head, (70, 64, 70), r, max(2, lw), border_radius=int(b_ * 1.2))
        pygame.draw.line(head, (70, 64, 70), (cx - ex + a_ * 1.4, ey - b_ * 0.4), (cx + ex - a_ * 1.4, ey - b_ * 0.4), max(2, lw))

    # ---------------- front hair ----------------
    def R(x, y):
        return (cx + x * u, cy + y * sc)
    def strands(curves, w=None, col=hair_hi, alpha=120):
        lay = pygame.Surface((W, H), pygame.SRCALPHA)
        for c in curves:
            pygame.draw.lines(lay, (*col, alpha), False, _spline([R(*p) for p in c], False, 8), w or max(2, lw))
        head.blit(lay, (0, 0))

    if baby:
        tuft = _spline([R(-0.05, -0.24), R(-0.02, -0.33), R(0.05, -0.34), R(0.08, -0.29), R(0.03, -0.3), R(0.0, -0.25)], True, 6)
        hair_shape(tuft)
    elif style == "Buzzcut":
        cap = _spline([R(-0.215, -0.07), R(-0.225, -0.2), R(-0.12, -0.31), R(0, -0.335), R(0.12, -0.31), R(0.225, -0.2), R(0.215, -0.07),
                       R(0.17, -0.13), R(0.1, -0.21), R(0, -0.225), R(-0.1, -0.21), R(-0.17, -0.13)], True, 6)
        _shape(head, cap, hair, None, 0, alpha=200)
    elif style == "Short":
        # faded sides, swept wavy top
        for sx in (-1, 1):
            side = _spline([R(sx * 0.2, -0.07), R(sx * 0.225, -0.18), R(sx * 0.17, -0.26), R(sx * 0.15, -0.16), R(sx * 0.17, -0.09)], True, 6)
            _shape(head, side, hair, None, 0, alpha=150)
        top_pts = _spline([R(-0.2, -0.12), R(-0.235, -0.22), R(-0.17, -0.32), R(-0.05, -0.375), R(0.1, -0.37), R(0.21, -0.31), R(0.215, -0.22), R(0.16, -0.18),
                           R(0.1, -0.24), R(-0.02, -0.255), R(-0.12, -0.21)], True, 7)
        hair_shape(top_pts)
        strands([[(-0.16, -0.27), (-0.06, -0.33), (0.08, -0.34)], [(-0.12, -0.23), (0.0, -0.3), (0.14, -0.3)], [(0.0, -0.27), (0.1, -0.29), (0.17, -0.26)]])
    elif style == "Long":
        for sx in (-1, 1):
            curtain = _spline([R(0, -0.285), R(sx * 0.12, -0.275), R(sx * 0.215, -0.17), R(sx * 0.25, -0.04), R(sx * 0.31, 0.18), R(sx * 0.35, 0.42),
                               R(sx * 0.27, 0.48), R(sx * 0.2, 0.4), R(sx * 0.2, 0.18), R(sx * 0.19, 0.03), R(sx * 0.15, -0.09), R(sx * 0.07, -0.2)], True, 6)
            hair_shape(curtain)
            strands([[(sx * 0.1, -0.27), (sx * 0.2, -0.12), (sx * 0.24, 0.1), (sx * 0.29, 0.38)], [(sx * 0.06, -0.24), (sx * 0.15, -0.08), (sx * 0.2, 0.15), (sx * 0.24, 0.4)]])
        top_c = _spline([R(-0.22, -0.2), R(-0.14, -0.33), R(0, -0.36), R(0.14, -0.33), R(0.22, -0.2), R(0.1, -0.28), R(0, -0.285), R(-0.1, -0.28)], True, 6)
        hair_shape(top_c)
    elif style == "Ponytail":
        cap = _spline([R(-0.215, -0.08), R(-0.235, -0.2), R(-0.14, -0.33), R(0, -0.365), R(0.14, -0.33), R(0.235, -0.2), R(0.215, -0.08), R(0.17, -0.14),
                       R(0.08, -0.23), R(-0.05, -0.245), R(-0.14, -0.2)], True, 7)
        hair_shape(cap)
        strands([[(-0.15, -0.26), (-0.04, -0.33), (0.1, -0.33)], [(-0.1, -0.22), (0.02, -0.3), (0.16, -0.27)]])
        pygame.draw.circle(head, (230, 90, 120), (int(R(0.2, -0.13)[0]), int(R(0.2, -0.13)[1])), int(u * 0.018))
    elif style == "Spiky":
        base = _spline([R(-0.215, -0.08), R(-0.235, -0.2), R(-0.13, -0.3), R(0, -0.32), R(0.13, -0.3), R(0.235, -0.2), R(0.215, -0.08), R(0.17, -0.15),
                        R(0.0, -0.2), R(-0.17, -0.15)], True, 6)
        hair_shape(base)
        for i in range(6):
            t = i / 5
            bx = -0.2 + 0.4 * t
            by = -0.28 - 0.04 * math.sin(math.pi * t)
            tip = (bx * 1.35 + (t - 0.5) * 0.05, by - 0.11 - 0.04 * math.sin(math.pi * t))
            pts = [R(bx - 0.05, by + 0.02), R(*tip), R(bx + 0.05, by + 0.02)]
            hair_shape(pts)
    elif style == "Mohawk":
        for sx in (-1, 1):
            side = _spline([R(sx * 0.2, -0.07), R(sx * 0.225, -0.18), R(sx * 0.14, -0.26), R(sx * 0.13, -0.16), R(sx * 0.17, -0.09)], True, 6)
            _shape(head, side, hair, None, 0, alpha=110)
        fin = _spline([R(-0.055, -0.22), R(-0.07, -0.34), R(-0.045, -0.47), R(0.0, -0.52), R(0.05, -0.46), R(0.07, -0.33), R(0.055, -0.22), R(0, -0.25)], True, 6)
        hair_shape(fin)
        strands([[(0, -0.25), (0.0, -0.37), (0.0, -0.49)]], col=hair_hi, alpha=140)
    elif style == "Curly":
        rr = u * 0.062
        for a in range(0, 181, 22):
            x = math.cos(math.radians(a)) * u * 0.232
            y = -math.sin(math.radians(a)) * (0.3 * sc) - 0.0 * u
            pygame.draw.circle(head, hair, (int(cx + x), int(cy + y - 0.03 * u)), int(rr))
            pygame.draw.circle(head, _shade(hair, 0.5), (int(cx + x), int(cy + y - 0.03 * u)), int(rr), lw)
        for k in range(7):
            x = -0.19 + 0.38 * k / 6
            y = -0.255 - 0.015 * math.sin(math.pi * k / 6)
            pygame.draw.circle(head, hair, (int(R(x, y)[0]), int(R(x, y)[1])), int(rr * 0.95))
            pygame.draw.circle(head, _shade(hair, 0.5), (int(R(x, y)[0]), int(R(x, y)[1])), int(rr * 0.95), lw)
        strands([[(-0.15, -0.3), (-0.05, -0.34)], [(0.04, -0.34), (0.15, -0.29)]], col=hair_hi, alpha=110)

    # ---------------- assemble with a slight head tilt ----------------
    angle = ((seed * 7) % 9 - 4) * 0.9
    pivot = (cx, cy + 0.36 * u)
    rot = pygame.transform.rotate(head, angle)
    # keep the neck pivot fixed after rotation
    vx, vy = (W / 2 - pivot[0]), (H / 2 - pivot[1])
    rad = math.radians(-angle)
    nx = vx * math.cos(rad) - vy * math.sin(rad)
    ny = vx * math.sin(rad) + vy * math.cos(rad)
    center = (pivot[0] + nx, pivot[1] + ny)
    out = pygame.Surface((W, H), pygame.SRCALPHA)
    out.blit(body, (0, 0))
    out.blit(rot, rot.get_rect(center=center))
    return pygame.transform.smoothscale(out, (w, h))

def male_like(gender):
    return gender != "Female"

def draw_avatar(screen, rect, gender, hair_colour, hairstyle, skin_tone, facial_hair="None", age=None, mood=60):
    """Draws a stylised illustrated avatar inside `rect`. `age` changes the
    face shape, clothes, hair colour and wrinkles; `mood` (0-100) changes the
    expression."""
    mood_bucket = 0 if mood < 35 else (1 if mood < 60 else 2)
    age_key = None if age is None else (age if age < 7 else (7 if age < 13 else (13 if age < 20 else (20 if age < 45 else (age // 5 * 5 if age < 70 else 70)))))
    seed = (sum(hair_colour) + sum(skin_tone) + len(hairstyle)) % 97
    key = (rect.w, rect.h, gender, tuple(hair_colour), hairstyle, tuple(skin_tone), facial_hair, age_key, mood_bucket)
    surf = _cache.get(key)
    if surf is None:
        if len(_cache) > 60:
            _cache.clear()
        surf = _render(rect.w, rect.h, gender, tuple(hair_colour), hairstyle, tuple(skin_tone), facial_hair, age, mood, seed)
        _cache[key] = surf
    screen.blit(surf, rect.topleft)
