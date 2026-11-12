import math
import pygame

# Procedural avatars drawn at 4x size and scaled down, so edges are smooth.
# Results are cached, so each look is only drawn once.
SS = 4
INK = (46, 36, 44)
_cache = {}

def _shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])

def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def _ellipse(s, colour, cx, cy, rx, ry, outline=0, alpha=255):
    rect = pygame.Rect(int(cx - rx), int(cy - ry), int(rx * 2), int(ry * 2))
    if alpha < 255:
        tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.ellipse(tmp, (*colour[:3], alpha), tmp.get_rect())
        s.blit(tmp, rect.topleft)
    else:
        pygame.draw.ellipse(s, colour, rect)
    if outline:
        pygame.draw.ellipse(s, INK, rect, outline)

def _circle(s, colour, cx, cy, r, outline=0, alpha=255):
    _ellipse(s, colour, cx, cy, r, r, outline, alpha)

def _stage(age):
    if age is None:
        return "adult"
    if age < 7: return "baby"
    if age < 13: return "child"
    if age < 20: return "teen"
    if age < 65: return "adult"
    return "elder"

def _hair_colour_for_age(colour, age):
    if age is None or age < 45:
        return colour
    grey = (200, 200, 205)
    t = min(1.0, (age - 45) / 25)
    return _mix(colour, grey, t)

def _front_hair(S, colour, cx, cy, rx, ry, style, baby):
    """Hair that sits on top of the head. Drawn on its own layer: a slightly
    larger ellipse with the face area erased, so the hairline follows the
    head's curve instead of ballooning into a helmet."""
    layer = pygame.Surface(S.get_size(), pygame.SRCALPHA)
    k = 0.8 if baby else 1.0
    def cap(grow, face_y, face_rx, face_ry, col=colour):
        _ellipse(layer, col, cx, cy - ry * 0.02, rx * grow, ry * grow)
        pygame.draw.ellipse(layer, (0, 0, 0, 0),
                            pygame.Rect(int(cx - rx * face_rx), int(cy + ry * face_y - ry * face_ry),
                                        int(rx * face_rx * 2), int(ry * face_ry * 2)))
    if style == "Buzzcut":
        cap(1.04, 0.62, 0.96, 0.92, _mix(colour, (120, 120, 120), 0.0))
        layer.set_alpha(215)
    elif style == "Short":
        cap(1.08, 0.46 + (0.1 if baby else 0), 0.90, 0.80)
        pygame.draw.polygon(layer, colour, [(cx - rx * 0.95, cy - ry * 0.1), (cx - rx * 0.2, cy - ry * 0.98),
                                            (cx + rx * 0.95, cy - ry * 0.12), (cx + rx * 0.5, cy - ry * 0.55),
                                            (cx - rx * 0.1, cy - ry * 0.52)])
    elif style == "Long":
        cap(1.09, 0.42, 0.86, 0.78)
        pygame.draw.polygon(layer, colour, [(cx - rx * 1.0, cy + ry * 0.05), (cx - rx * 0.1, cy - ry * 1.0),
                                            (cx + rx * 1.0, cy + ry * 0.05), (cx + rx * 0.3, cy - ry * 0.5),
                                            (cx - rx * 0.15, cy - ry * 0.42)])
    elif style == "Ponytail":
        cap(1.07, 0.46, 0.90, 0.80)
        pygame.draw.polygon(layer, colour, [(cx - rx * 0.95, cy - ry * 0.05), (cx - rx * 0.2, cy - ry * 0.98),
                                            (cx + rx * 0.95, cy - ry * 0.05), (cx + rx * 0.2, cy - ry * 0.52)])
    elif style == "Curly":
        cap(1.08, 0.44, 0.90, 0.80)
        for i in range(9):
            a = math.pi * (0.02 + 0.96 * i / 8)
            bx = cx + math.cos(math.pi - a) * rx * 1.02
            by = cy - math.sin(a) * ry * 0.98 + ry * 0.02
            _circle(layer, colour, bx, by, rx * 0.27)
        for sx in (-1, 1):
            _circle(layer, colour, cx + sx * rx * 1.08, cy + ry * 0.08, rx * 0.22)
    elif style == "Spiky":
        cap(1.05, 0.52, 0.92, 0.84)
        for i in range(5):
            a = math.pi * (0.2 + 0.6 * i / 4)
            bx, by = cx + math.cos(math.pi - a) * rx * 0.92, cy - math.sin(a) * ry * 0.92
            tx, ty = cx + math.cos(math.pi - a) * rx * 1.5, cy - math.sin(a) * ry * 1.52
            nx, ny = -math.sin(math.pi - a), math.cos(math.pi - a)
            w = rx * 0.2
            pygame.draw.polygon(layer, colour, [(bx - nx * w, by - ny * w), (bx + nx * w, by + ny * w), (tx, ty)])
    elif style == "Mohawk":
        cap(1.02, 0.7, 0.98, 0.95)
        layer.set_alpha(110)
        fin = pygame.Surface(S.get_size(), pygame.SRCALPHA)
        for i in range(6):
            t = i / 5
            x = cx - rx * 0.12 + rx * 0.24 * t * 0
            bx = cx + (t - 0.5) * rx * 0.8
            by = cy - ry * (0.9 - 0.25 * abs(t - 0.5))
            pygame.draw.polygon(fin, colour, [(bx - rx * 0.1, by + ry * 0.12), (bx + rx * 0.1, by + ry * 0.12),
                                              (bx, by - ry * (0.55 - 0.2 * abs(t - 0.5)))])
        S.blit(layer, (0, 0))
        S.blit(fin, (0, 0))
        return
    else:
        return
    S.blit(layer, (0, 0))

def _render(w, h, gender, hair, style, skin, facial, age, mood):
    W, H = w * SS, h * SS
    S = pygame.Surface((W, H), pygame.SRCALPHA)
    stage = _stage(age)
    baby, elder = stage == "baby", stage == "elder"
    hs = {"baby": 1.14, "child": 1.06}.get(stage, 1.0)
    cx = W / 2
    rx = W * 0.25 * hs
    ry = rx * (1.0 if baby else 1.08)
    cy = H * (0.43 if baby else 0.40)
    hair = _hair_colour_for_age(hair, age)
    skin_d = _shade(skin, 0.86)
    skin_dd = _shade(skin, 0.72)
    ow = max(3, int(W * 0.011))
    female = gender == "Female"

    # --- back hair ---
    if style == "Long":
        pygame.draw.rect(S, hair, pygame.Rect(int(cx - rx * 1.22), int(cy - ry * 0.6), int(rx * 2.44), int(ry * 2.4)),
                         border_radius=int(rx * 0.6))
        pygame.draw.rect(S, INK, pygame.Rect(int(cx - rx * 1.22), int(cy - ry * 0.6), int(rx * 2.44), int(ry * 2.4)),
                         ow, border_radius=int(rx * 0.6))
    elif style == "Ponytail":
        _ellipse(S, hair, cx + rx * 1.12, cy + ry * 0.55, rx * 0.34, ry * 0.9, ow)
        _circle(S, (230, 90, 120), cx + rx * 0.98, cy - ry * 0.25, rx * 0.12, ow // 2 + 1)

    # --- body / clothes ---
    body_w = W * (0.62 if baby else 0.86)
    top = cy + ry * 0.92
    cloth = {"Male": (70, 120, 200), "Female": (226, 100, 150)}.get(gender, (130, 130, 150))
    if stage == "baby": cloth = (255, 226, 150)
    elif stage == "child": cloth = (96, 190, 150) if not female else (250, 170, 90)
    elif stage == "elder": cloth = _mix(cloth, (150, 150, 155), 0.45)
    # neck
    pygame.draw.rect(S, skin_d, pygame.Rect(int(cx - rx * 0.28), int(cy + ry * 0.7), int(rx * 0.56), int(ry * 0.5)))
    body = pygame.Rect(int(cx - body_w / 2), int(top), int(body_w), int(H * 0.5))
    pygame.draw.ellipse(S, cloth, body)
    pygame.draw.ellipse(S, INK, body, ow)
    # neckline
    nl = [(cx - rx * 0.42, top + ry * 0.02), (cx + rx * 0.42, top + ry * 0.02), (cx, top + ry * (0.42 if not baby else 0.3))]
    if stage in ("teen", "adult", "elder"):
        pygame.draw.polygon(S, skin_d, nl)
        pygame.draw.lines(S, _shade(cloth, 0.7), False, nl, ow)
    else:
        _ellipse(S, skin_d, cx, top + ry * 0.04, rx * 0.4, ry * 0.2)
        pygame.draw.arc(S, _shade(cloth, 0.7), pygame.Rect(int(cx - rx * 0.42), int(top - ry * 0.18), int(rx * 0.84), int(ry * 0.6)),
                        math.pi, 2 * math.pi, ow)
    # a shirt highlight
    _ellipse(S, _mix(cloth, (255, 255, 255), 0.35), cx - body_w * 0.24, top + H * 0.08, body_w * 0.12, H * 0.035, 0, 120)

    # --- ears ---
    for sx in (-1, 1):
        _ellipse(S, skin, cx + sx * rx * 0.98, cy + ry * 0.12, rx * 0.17, ry * 0.2, ow)
        _ellipse(S, skin_d, cx + sx * rx * 0.98, cy + ry * 0.12, rx * 0.07, ry * 0.1)

    # --- head ---
    _ellipse(S, skin, cx, cy, rx, ry, ow)
    # soft form shading along the jaw, and cheeks
    pygame.draw.arc(S, skin_d, pygame.Rect(int(cx - rx * 0.93), int(cy - ry * 0.93), int(rx * 1.86), int(ry * 1.86)),
                    math.pi * 1.05, math.pi * 1.5, int(rx * 0.1))
    for sx in (-1, 1):
        _circle(S, (240, 110, 120), cx + sx * rx * 0.58, cy + ry * 0.3, rx * 0.18, 0, 70)

    # --- facial hair (males, once old enough) ---
    if not female and facial != "None" and (age is None or age >= 15):
        fh = hair
        if facial == "Stubble":
            for i in range(26):
                a = math.pi * (0.1 + 0.8 * i / 25)
                for rr in (0.78, 0.9):
                    px, py = cx + math.cos(a) * rx * rr * -1 * -1, cy + math.sin(a) * ry * rr * 0.98
                    _circle(S, fh, px, py, W * 0.006, 0, 150)
        elif facial == "Beard":
            beard = [(cx - rx * 0.96, cy + ry * 0.05)]
            for i in range(0, 21):
                a = math.pi * (1 - i / 20)
                beard.append((cx + math.cos(a) * rx * 0.99, cy + math.sin(a) * ry * 0.99 + ry * 0.02 * (0 if i % 20 else 0)))
            beard.append((cx + rx * 0.96, cy + ry * 0.05))
            for i in range(20, -1, -1):
                a = math.pi * (1 - i / 20)
                beard.append((cx + math.cos(a) * rx * 0.64, cy + math.sin(a) * ry * 0.5 + ry * 0.12))
            pygame.draw.polygon(S, fh, beard)
            _ellipse(S, fh, cx, cy + ry * 0.9, rx * 0.68, ry * 0.16)
        # moustache for both "Moustache" and "Beard"
        if facial in ("Moustache", "Beard"):
            for sx in (-1, 1):
                pts = [(cx, cy + ry * 0.28), (cx + sx * rx * 0.42, cy + ry * 0.26),
                       (cx + sx * rx * 0.5, cy + ry * 0.4), (cx + sx * rx * 0.2, cy + ry * 0.36), (cx, cy + ry * 0.36)]
                pygame.draw.polygon(S, fh, pts)

    # --- eyes, brows, nose, mouth ---
    eye_dx = rx * 0.42
    eye_y = cy - ry * (0.0 if not baby else -0.08)
    ew, eh = rx * (0.2 if not baby else 0.24), rx * (0.15 if not baby else 0.2)
    sad = mood < 35
    for sx in (-1, 1):
        ex = cx + sx * eye_dx
        _ellipse(S, (255, 255, 255), ex, eye_y, ew, eh, ow // 2 + 1)
        _circle(S, (88, 62, 44), ex, eye_y + eh * 0.05, eh * 0.78)
        _circle(S, (20, 14, 14), ex, eye_y + eh * 0.05, eh * 0.4)
        _circle(S, (255, 255, 255), ex - eh * 0.25, eye_y - eh * 0.25, eh * 0.22)
        if female and stage in ("teen", "adult", "elder"):
            pygame.draw.arc(S, INK, pygame.Rect(int(ex - ew), int(eye_y - eh * 1.05), int(ew * 2), int(eh * 1.6)),
                            0.2, math.pi - 0.2, ow)
        # brows
        by = eye_y - eh * (1.9 if not baby else 1.6)
        tilt = (0.12 if sad else -0.03) * rx
        brow = hair if style != "Bald" or facial == "None" else hair
        bcol = _shade(brow, 0.8) if sum(brow) > 60 else brow
        pygame.draw.line(S, bcol, (ex - sx * ew * 0.9, by + (tilt if sad else 0) * sx * 0 + (tilt if sad else 0)),
                         (ex + sx * ew * 0.9, by - (tilt if sad else 0) * 0 + (0 if sad else tilt)), max(3, int(rx * 0.075)))
    # nose
    pygame.draw.arc(S, skin_dd, pygame.Rect(int(cx - rx * 0.14), int(cy + ry * 0.1), int(rx * 0.28), int(rx * 0.24)),
                    math.pi * 1.1, math.pi * 1.9, max(3, ow - 1))
    # mouth
    my = cy + ry * 0.5
    lip = (196, 90, 96)
    if mood >= 60:
        pygame.draw.arc(S, lip, pygame.Rect(int(cx - rx * 0.34), int(my - rx * 0.2), int(rx * 0.68), int(rx * 0.4)),
                        math.pi * 1.08, math.pi * 1.92, max(4, int(ow * 1.3)))
    elif mood >= 35:
        pygame.draw.arc(S, lip, pygame.Rect(int(cx - rx * 0.3), int(my - rx * 0.12), int(rx * 0.6), int(rx * 0.24)),
                        math.pi * 1.15, math.pi * 1.85, max(4, int(ow * 1.3)))
    else:
        pygame.draw.arc(S, lip, pygame.Rect(int(cx - rx * 0.28), int(my), int(rx * 0.56), int(rx * 0.3)),
                        math.pi * 0.2, math.pi * 0.8, max(4, int(ow * 1.3)))

    # --- age details ---
    if age is not None and age >= 50:
        for sx in (-1, 1):
            for k in range(3 if age >= 65 else 1):
                pygame.draw.line(S, skin_dd, (cx + sx * (eye_dx + ew * 1.35), eye_y + (k - 1) * eh * 0.5),
                                 (cx + sx * (eye_dx + ew * 1.9), eye_y + (k - 1) * eh * 0.9), max(2, ow // 2))
        pygame.draw.arc(S, skin_dd, pygame.Rect(int(cx - rx * 0.4), int(cy - ry * 0.7), int(rx * 0.8), int(ry * 0.3)),
                        math.pi * 0.1, math.pi * 0.9, max(2, ow // 2))
    if age is not None and age >= 65:
        for sx in (-1, 1):
            pygame.draw.circle(S, INK, (int(cx + sx * eye_dx), int(eye_y)), int(ew * 1.35), ow)
        pygame.draw.line(S, INK, (cx - eye_dx + ew * 1.35, eye_y), (cx + eye_dx - ew * 1.35, eye_y), ow)

    # --- front hair ---
    if style != "Bald":
        _front_hair(S, hair, cx, cy, rx, ry, style, baby)
        # outline the hair mass lightly by re-stroking the head's top arc
        if style not in ("Buzzcut", "Mohawk"):
            pygame.draw.arc(S, INK, pygame.Rect(int(cx - rx * 1.08), int(cy - ry * 1.1), int(rx * 2.16), int(ry * 2.16)),
                            math.pi * 0.02, math.pi * 0.98, ow)
    if style == "Long":
        # front locks fall over the shoulders
        for sx in (-1, 1):
            r = pygame.Rect(int(cx + sx * rx * 1.0 - rx * 0.2), int(cy - ry * 0.05), int(rx * 0.4), int(ry * 1.55))
            pygame.draw.rect(S, hair, r, border_radius=int(rx * 0.2))
            pygame.draw.rect(S, INK, r, ow, border_radius=int(rx * 0.2))

    return pygame.transform.smoothscale(S, (w, h))

def draw_avatar(screen, rect, gender, hair_colour, hairstyle, skin_tone, facial_hair="None", age=None, mood=60):
    """Draws a smooth, shaded avatar inside `rect`. `age` changes proportions,
    clothes, grey hair, wrinkles and glasses; `mood` (0-100) changes the face."""
    mood_bucket = 0 if mood < 35 else (1 if mood < 60 else 2)
    age_key = None if age is None else (age if age < 7 else (7 if age < 13 else (13 if age < 20 else (20 if age < 45 else (age // 5 * 5 if age < 70 else 70)))))
    key = (rect.w, rect.h, gender, tuple(hair_colour), hairstyle, tuple(skin_tone), facial_hair, age_key, mood_bucket)
    surf = _cache.get(key)
    if surf is None:
        if len(_cache) > 80:
            _cache.clear()
        surf = _render(rect.w, rect.h, gender, tuple(hair_colour), hairstyle, tuple(skin_tone), facial_hair, age, mood)
        _cache[key] = surf
    screen.blit(surf, rect.topleft)
