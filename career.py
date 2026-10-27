import random
import pygame
from constants import OUTLINE, INK, MUTED, draw_card, draw_pill, draw_shadow
from constants import (
    WHITE, BLACK, LIGHT_GREY, DARK_GREY, ACCENT,
    font, small_font, draw_text, draw_rounded_rect
)
from education import UNI_DURATION

EDUCATION_RANK = {"None": 0, "Diploma": 0.5, "Bachelor's": 1, "Master's": 2, "PhD": 3}

# Jobs now care about how old you are, your qualifications AND course, your
# stats, and sometimes the clubs or teams you belong to.
#   courses: degree subjects that qualify (None = any)
#   stats:   minimum stat levels
#   any_of:  you must be in at least one of these clubs/teams
def J(title, age, edu, pay, wealth, prestige=0, courses=None, stats=None, any_of=None, skills=None, fame=False):
    return {"title": title, "min_age": age, "min_education": edu, "min_prestige": prestige,
            "courses": courses, "stats": stats or {}, "any_of": any_of, "wealth": wealth, "pay": pay,
            "skills": skills or {}, "fame": fame}

JOB_TIERS = [
    J("Cashier", 16, "None", 15, 3),
    J("Waiter", 16, "None", 14, 3, stats={"social": 40}),
    J("Warehouse Worker", 18, "None", 18, 4, stats={"physical": 45}),
    J("Office Assistant", 18, "None", 22, 5),
    J("Fitness Instructor", 18, "None", 24, 5, stats={"athletic": 60}),
    J("Musician", 16, "None", 20, 4, stats={"social": 45}, any_of=["band"], fame=True),
    J("Singer", 16, "None", 22, 4, stats={"social": 45}, skills={"singing": 3}, fame=True),
    J("Music Producer", 18, "None", 30, 6, stats={"academic": 45}, skills={"music": 3}, fame=True),
    J("Influencer", 16, "None", 18, 3, stats={"looks": 55, "social": 55}, fame=True),
    J("Model", 18, "None", 40, 8, stats={"looks": 75}, fame=True),
    J("Actor", 18, "None", 38, 7, stats={"looks": 60, "social": 60}, any_of=["drama"], fame=True),
    J("Professional Athlete", 18, "None", 70, 12, stats={"athletic": 85},
      any_of=["football", "basket", "swim", "track", "rugby"], fame=True),
    J("Electrician", 18, "Diploma", 38, 8, courses=["Electrician"]),
    J("Plumber", 18, "Diploma", 36, 8, courses=["Plumber"]),
    J("Chef", 18, "Diploma", 30, 6, courses=["Chef"]),
    J("Mechanic", 18, "Diploma", 34, 7, courses=["Mechanic"], stats={"physical": 40}),
    J("Hairdresser", 18, "Diploma", 26, 5, courses=["Hairdresser"], stats={"looks": 40}),
    J("Nursing Assistant", 18, "Diploma", 28, 6, courses=["Nursing Assistant"]),
    J("Teacher", 21, "Bachelor's", 35, 8, courses=["Education", "Arts", "Sport Science"]),
    J("Sports Coach", 21, "Bachelor's", 34, 7, courses=["Sport Science"], stats={"athletic": 50}),
    J("Designer", 21, "Bachelor's", 38, 8, courses=["Arts"]),
    J("Accountant", 21, "Bachelor's", 40, 9, courses=["Business"]),
    J("Engineer", 21, "Bachelor's", 52, 10, courses=["Engineering"]),
    J("Software Engineer", 21, "Bachelor's", 55, 11, prestige=2, courses=["Computer Science", "Engineering"]),
    J("Manager", 24, "Master's", 65, 14, prestige=2, courses=["Business", "Engineering", "Computer Science"]),
    J("Lawyer", 24, "Master's", 80, 16, prestige=3, courses=["Law"]),
    J("Doctor", 26, "PhD", 100, 20, prestige=3, courses=["Medicine"]),
    J("University Professor", 27, "PhD", 70, 15, prestige=2),
]

def P(title, age, pay, stats=None, enrolled=False, intern=False):
    return {"title": title, "base": title, "min_age": age, "pay": pay, "wealth": 1, "stats": stats or {},
            "enrolled": enrolled, "intern": intern, "part": True}

# Part-time and student jobs: you can do one alongside school, study or a main job.
PART_TIME = [
    P("Paper Round", 13, 6),
    P("Babysitter", 14, 8, {"social": 40}),
    P("Cafe Assistant", 16, 12),
    P("Retail Assistant", 16, 12, {"social": 35}),
    P("Tutor", 16, 14, {"academic": 60}),
    P("Lifeguard", 16, 13, {"athletic": 55}),
    P("Delivery Rider", 17, 14, {"physical": 45}),
    P("Weekend Bar Work", 18, 16, {"social": 45}),
    P("Campus Library Assistant", 18, 12, enrolled=True),
    P("Research Assistant", 18, 22, {"academic": 65}, enrolled=True),
    P("Internship", 18, 15, enrolled=True, intern=True),
]
TITLE_PREFIX = ["", "Senior ", "Lead ", "Head of "]

def _log(state, text):
    state["journal"].append((state["age"], text))

def stats_ok(job, stats):
    return all(stats[k] >= v for k, v in job["stats"].items())

def eligible_jobs(career, state):
    """Returns (jobs you can take now, count of age-appropriate jobs you
    can't yet qualify for)."""
    age = state["age"]
    rank = EDUCATION_RANK[career["education"]]
    prestige = career.get("prestige", 0)
    course = career.get("course")
    current = (career["job"].get("base") or career["job"]["title"]) if career["job"] else None
    trade = career.get("trade")
    ok, locked = [], 0
    for j in JOB_TIERS:
        if j["min_age"] > age or j["title"] == current:
            continue
        need_prestige = max(0, j["min_prestige"] - (1 if career.get("experience", 0) >= 2 else 0))
        qualified = (EDUCATION_RANK[j["min_education"]] <= rank
                     and need_prestige <= prestige
                     and (j["courses"] is None or course in j["courses"] or trade in j["courses"])
                     and stats_ok(j, state["stats"])
                     and all(state.get("skills", {}).get(k, 0) >= v for k, v in j["skills"].items())
                     and (j["any_of"] is None or any(a in state["activities"] for a in j["any_of"])))
        if qualified:
            ok.append(j)
        else:
            locked += 1
    ok.sort(key=lambda j: -j["pay"])
    return ok, locked

def eligible_side_jobs(career, state):
    cur = career.get("side_job")
    out = []
    for j in PART_TIME:
        if j["min_age"] > state["age"] or (cur and cur["title"] == j["title"]):
            continue
        if j["enrolled"] and not career["enrolled"]:
            continue
        if stats_ok(j, state["stats"]):
            out.append(j)
    return out

def get_button_layout(rect, count, y=60, w=220):
    gap = 10
    total_w = count * w + (count - 1) * gap
    start_x = rect.x
    return [pygame.Rect(start_x + i * (w + gap), rect.y + y, w, 34) for i in range(count)]

def draw_button(screen, rect, label, mouse_pos, disabled=False):
    hovered = rect.collidepoint(mouse_pos)
    fill = LIGHT_GREY if disabled else (ACCENT if hovered else WHITE)
    draw_rounded_rect(screen, fill, rect, radius=8)
    pygame.draw.rect(screen, OUTLINE, rect, 2, border_radius=8)
    text_colour = DARK_GREY if disabled else BLACK
    draw_text(screen, label, small_font, text_colour, rect.centerx, rect.centery, centre=True)

def H(title, base, age, pay, stats=None, skills_any=None):
    return {"title": title, "base": base, "min_age": age, "pay": pay, "stats": stats or {}, "skills_any": skills_any,
            "fame": True, "wealth": 0}

# Side careers: chase fame while you work full time or study.
HUSTLES = [
    H("Content Creator", "Influencer", 10, 8, {"social": 40}),
    H("Streamer", "Influencer", 14, 10, {"social": 45}),
    H("Gigging Musician", "Musician", 12, 10, skills_any={"singing": 2, "music": 2}),
    H("Community Theatre", "Actor", 12, 8, {"social": 50}),
    H("Part-time Modelling", "Model", 16, 12, {"looks": 65}),
    H("Amateur Athlete", "Professional Athlete", 12, 10, {"athletic": 65}),
]

def eligible_hustles(career, state):
    out = []
    for h in HUSTLES:
        if h["min_age"] > state["age"] or not stats_ok(h, state["stats"]):
            continue
        if h["skills_any"] and not any(state.get("skills", {}).get(k, 0) >= v for k, v in h["skills_any"].items()):
            continue
        out.append(h)
    return out

def active_fame_job(career):
    job = career.get("job")
    if job and job.get("fame"):
        return job
    return career.get("hustle")

FAME_TIERS = [(80, "Superstar"), (60, "Famous"), (40, "Rising star"), (20, "Local name"), (0, "Unknown")]

def fame_tier(fame):
    return next(name for lim, name in FAME_TIERS if fame >= lim)

SPECIAL = {
    "Model": ("Fashion week", "Walk at fashion week"),
    "Actor": ("Audition", "Audition for a lead role"),
    "Professional Athlete": ("Big match", "Play a championship match"),
    "Musician": ("Release", "Release a single"),
    "Singer": ("Release", "Release a single"),
    "Music Producer": ("Release", "Produce a hit track"),
    "Influencer": ("Go viral", "Try to go viral"),
}
FAME_BUTTONS = [("promo", "Promo campaign"), ("talk", "Talk show"), ("brand", "Brand deal (fame 30+)"),
                ("post", "Post online"), ("gala", "Charity gala ($10)"), ("special", None)]

def fame_button_rects(rect, y):
    out = {}
    for n, (key, _l) in enumerate(FAME_BUTTONS):
        out[key] = pygame.Rect(rect.x + (n % 3) * 225, rect.y + y + (n // 3) * 38, 215, 32)
    return out

def do_fame_action(key, career, state, job):
    """Costs an action. Repeats in the same year give less. Returns a log line."""
    stats = state["stats"]
    used = state["actions_used"]
    n = used.get("__fame_" + key, 0)
    used["__fame_" + key] = n + 1
    state["actions_remaining"] -= 1
    dim = max(0.3, 1 / (1 + 0.4 * n))
    fame = career.get("fame", 0)
    def gain(v):
        career["fame"] = max(0, min(100, career.get("fame", 0) + max(1, round(v * dim))))
    pay = job["pay"]
    if key == "promo":
        got = max(2, int(pay * 0.15 * dim)); state["money"] += got; gain(4)
        return f"Fronted a promo campaign (+${got}, fame up)."
    if key == "talk":
        chance = 0.45 + (stats["social"] + stats["looks"] - 100) / 300
        if random.random() < max(0.15, min(0.9, chance)):
            gain(6); stats["social"] = min(100, stats["social"] + 2)
            return "Charmed the audience on a talk show."
        career["fame"] = max(0, fame - 2); stats["mental"] = max(0, stats["mental"] - 3)
        return "An awkward talk show interview went viral for the wrong reasons."
    if key == "brand":
        if fame < 30:
            used["__fame_" + key] = n
            state["actions_remaining"] += 1
            return "Brands weren't interested yet. You need fame 30+."
        got = int(pay * (0.3 + fame / 150) * dim) + 5; state["money"] += got; gain(1)
        return f"Signed a brand deal worth ${got}."
    if key == "post":
        gain(2); stats["social"] = min(100, stats["social"] + 1)
        return "Posted online and picked up followers."
    if key == "gala":
        if state["money"] < 10:
            used["__fame_" + key] = n
            state["actions_remaining"] += 1
            return "You can't afford the gala ticket."
        state["money"] -= 10; gain(3); stats["social"] = min(100, stats["social"] + 2)
        return "Attended a charity gala and was photographed."
    # job-specific
    base = job.get("base", job["title"])
    if base == "Model":
        gain(5); got = max(3, int(pay * 0.2 * dim)); state["money"] += got
        return f"Walked at fashion week (+${got})."
    if base == "Actor":
        if random.random() < 0.3 + stats["social"] / 300 + stats["looks"] / 400:
            gain(8); job["pay"] = int(pay * 1.1) + 1
            return "Landed a lead role! Your fee went up."
        stats["mental"] = max(0, stats["mental"] - 1)
        return "Didn't get the part this time."
    if base == "Professional Athlete":
        if random.random() < 0.25 + stats["athletic"] / 200:
            gain(7); got = int(pay * 0.2) + 3; state["money"] += got
            return f"Won the championship match (+${got})!"
        career["fame"] = max(0, career.get("fame", 0) - 1)
        return "Lost the championship match."
    if base in ("Musician", "Singer", "Music Producer"):
        hit = random.random() < 0.35 + max(state.get("skills", {}).get("singing", 0), state.get("skills", {}).get("music", 0)) * 0.08
        if hit:
            gain(8); got = int(pay * 0.4) + 4; state["money"] += got
            return f"Your release was a hit (+${got})."
        gain(2)
        return "Your release got a lukewarm response."
    if random.random() < 0.3:
        gain(9)
        return "A post went viral!"
    gain(1)
    return "Your post didn't catch on."

def can_promote(job):
    return job.get("level", 0) < 3 and job.get("since", 0) >= 2

def draw_side_job_row(screen, rect, mouse_pos, career, state, y, buttons):
    side = career.get("side_job")
    if state["age"] < 13:
        return
    if side:
        draw_text(screen, f"Part-time: {side['title']} (${side['pay']}/yr)", small_font, INK, rect.x, rect.y + y + 8)
        q = pygame.Rect(rect.x + 360, rect.y + y, 150, 30)
        draw_button(screen, q, "Quit part-time", mouse_pos)
        buttons["side_quit"] = q
    else:
        draw_text(screen, "No part-time job.", small_font, DARK_GREY, rect.x, rect.y + y + 8)
    f = pygame.Rect(rect.x + 520, rect.y + y, 150, 30)
    draw_button(screen, f, "Part-time jobs", mouse_pos)
    buttons["side_find"] = f

def draw_career_tab(screen, rect, mouse_pos, career, state):
    no_budget = state["actions_remaining"] <= 0
    mode = career.get("browsing_jobs")

    if mode:
        side = mode == "side"
        draw_text(screen, "Choose a part-time or student job:" if side else "Choose a job:", font, INK, rect.x, rect.y)
        back_rect = pygame.Rect(rect.x, rect.y + 30, 120, 30)
        draw_button(screen, back_rect, "Back", mouse_pos)
        if side:
            jobs, locked = eligible_side_jobs(career, state), 0
        else:
            jobs, locked = eligible_jobs(career, state)
        rows = 6
        scroll = max(0, min(career.get("scroll", 0), max(0, len(jobs) - rows)))
        career["scroll"] = scroll
        if locked:
            draw_text(screen, f"{locked} more jobs need better stats, a course, or a club or team.",
                      small_font, DARK_GREY, rect.x + 130, rect.y + 37)
        elif side:
            draw_text(screen, "Some need you to be studying. Part-time work costs a little Mental a year.",
                      small_font, DARK_GREY, rect.x + 130, rect.y + 37)
        y = rect.y + 70
        job_rects = []
        if not jobs:
            draw_text(screen, "Nothing available yet. Improve your stats, join clubs, or study.",
                      small_font, DARK_GREY, rect.x, y)
        for job in jobs[scroll:scroll + rows]:
            row_rect = pygame.Rect(rect.x, y, rect.width, 34)
            draw_rounded_rect(screen, WHITE, row_rect, radius=6)
            pygame.draw.rect(screen, OUTLINE, row_rect, 1, border_radius=6)
            draw_text(screen, f"{job['title']}  (${job['pay']}/yr)", small_font, INK,
                      row_rect.x + 10, row_rect.y + 8)
            take_rect = pygame.Rect(row_rect.right - 90, row_rect.y + 4, 80, 26)
            hovered = take_rect.collidepoint(mouse_pos)
            fill = LIGHT_GREY if no_budget else (ACCENT if hovered else LIGHT_GREY)
            draw_rounded_rect(screen, fill, take_rect, radius=6)
            pygame.draw.rect(screen, OUTLINE, take_rect, 1, border_radius=6)
            draw_text(screen, "Take", small_font, INK, take_rect.centerx, take_rect.centery, centre=True)
            job_rects.append((job, take_rect))
            y += 40
        if len(jobs) > rows:
            draw_text(screen, "Scroll for more", small_font, DARK_GREY, rect.right - 120, rect.y + 2)
        return {"back": back_rect, "jobs": job_rects}

    buttons = {}
    view = career.setdefault("view", "work")
    vw = pygame.Rect(rect.right - 170, rect.y - 4, 80, 24)
    vf = pygame.Rect(rect.right - 84, rect.y - 4, 84, 24)
    for key, vr, lab in (("work", vw, "Work"), ("fame", vf, "Fame")):
        draw_rounded_rect(screen, ACCENT if view == key else (WHITE if not vr.collidepoint(mouse_pos) else (255, 236, 218)), vr, radius=10)
        pygame.draw.rect(screen, OUTLINE, vr, 1, border_radius=10)
        draw_text(screen, lab, small_font, WHITE if view == key else INK, vr.centerx, vr.centery, centre=True)
        buttons["view_" + key] = vr
    if view == "fame":
        fj = active_fame_job(career)
        fame = career.get("fame", 0)
        draw_text(screen, f"Fame: {fame}  ({fame_tier(fame)})", font, INK, rect.x, rect.y)
        fbar = pygame.Rect(rect.x + 250, rect.y + 6, 220, 14)
        draw_rounded_rect(screen, LIGHT_GREY, fbar, radius=7)
        draw_rounded_rect(screen, (236, 130, 178), (fbar.x, fbar.y, int(fbar.w * fame / 100), fbar.h), radius=7)
        if fj is None:
            draw_text(screen, "Start a side career. You can do it alongside school or a full-time job.", small_font, MUTED, rect.x, rect.y + 32)
            hs = eligible_hustles(career, state)
            if not hs:
                draw_text(screen, "Nothing open yet. Build your Social, Looks or Athletic stats, or learn singing or music.",
                          small_font, DARK_GREY, rect.x, rect.y + 60)
            rows = []
            for n, h in enumerate(hs[:6]):
                r2 = pygame.Rect(rect.x + (n % 2) * 340, rect.y + 58 + (n // 2) * 44, 330, 38)
                draw_button(screen, r2, f"{h['title']} (age {h['min_age']}+)", mouse_pos, disabled=no_budget)
                rows.append((h, r2))
            buttons["hustles"] = rows
            return buttons
        title = fj["title"] + ("  (side career)" if fj is career.get("hustle") else "")
        draw_text(screen, title, small_font, MUTED, rect.x, rect.y + 30)
        rects = fame_button_rects(rect, 58)
        for key, label in FAME_BUTTONS:
            lab = label or SPECIAL.get(fj.get("base", fj["title"]), ("", "Career move"))[1]
            n = state["actions_used"].get("__fame_" + key, 0)
            draw_button(screen, rects[key], lab + (f" ({n})" if n else ""), mouse_pos, disabled=no_budget)
            buttons["f_" + key] = rects[key]
        draw_text(screen, "Fame lifts your pay, your dating odds and your invitations. It fades if you stop.",
                  small_font, MUTED, rect.x, rect.y + 142)
        if fj is career.get("hustle"):
            q2 = pygame.Rect(rect.x, rect.y + 170, 200, 32)
            draw_button(screen, q2, "Stop side career", mouse_pos)
            buttons["hustle_quit"] = q2
        return buttons
    if career["job"]:
        job = career["job"]
        lvl = job.get("level", 0)
        draw_text(screen, f"Working as {job['title']}", font, INK, rect.x, rect.y)
        draw_text(screen, f"Pay: ${job['pay']}/yr   Years: {job.get('years', 0)}   Experience: {career.get('experience', 0)}",
                  small_font, DARK_GREY, rect.x, rect.y + 26)
        perf = job.get("perf", 55)
        bar = pygame.Rect(rect.x + 510, rect.y + 8, 150, 12)
        draw_text(screen, "Performance", small_font, DARK_GREY, rect.x + 392, rect.y + 5)
        draw_rounded_rect(screen, LIGHT_GREY, bar, radius=6)
        draw_rounded_rect(screen, (76, 175, 120) if perf >= 40 else (215, 80, 80), (bar.x, bar.y, int(bar.w * perf / 100), bar.h), radius=6)

        better, quit_r = get_button_layout(rect, 2, 56, 220)
        draw_button(screen, better, "Look for a Better Job", mouse_pos, disabled=no_budget)
        draw_button(screen, quit_r, "Quit Job", mouse_pos, disabled=no_budget)
        ot, net, promo = get_button_layout(rect, 3, 98, 215)
        n_ot = state["actions_used"].get("__ot__", 0)
        draw_button(screen, ot, "Work overtime" + (f" ({n_ot})" if n_ot else ""), mouse_pos, disabled=no_budget)
        draw_button(screen, net, "Network at work", mouse_pos, disabled=no_budget)
        pl = "Ask for promotion" if can_promote(job) else ("Top of the ladder" if lvl >= 3 else "Promotion (2+ yrs since last)")
        draw_button(screen, promo, pl, mouse_pos, disabled=no_budget or not can_promote(job))
        buttons.update({"better": better, "quit": quit_r, "ot": ot, "net": net, "promo": promo})
        side_y = 148
        draw_side_job_row(screen, rect, mouse_pos, career, state, side_y, buttons)
        return buttons

    if state["age"] < 13:
        draw_text(screen, "You're too young for a job, but you can try a side career in the Fame tab.", small_font, DARK_GREY, rect.x, rect.y + 28)
        return buttons
    draw_text(screen, "You're not in a full-time job." + (" (Studying full-time.)" if career["enrolled"] else ""),
              small_font, DARK_GREY, rect.x, rect.y)
    if state["age"] >= 16:
        search_rect = pygame.Rect(rect.x, rect.y + 36, 220, 34)
        draw_button(screen, search_rect, "Search for a Job", mouse_pos, disabled=no_budget)
        buttons["search"] = search_rect
    else:
        draw_text(screen, "Full-time jobs start at 16. Try a paper round or babysitting!", small_font, DARK_GREY, rect.x, rect.y + 44)
    draw_side_job_row(screen, rect, mouse_pos, career, state, 96, buttons)
    return buttons

def _new_job(job):
    j = dict(job)
    j.update({"base": job["title"], "years": 0, "perf": 55, "level": 0, "since": 0})
    return j

def handle_career_click(mx, my, buttons, career, state):
    mode = career.get("browsing_jobs")
    if mode:
        if buttons["back"].collidepoint(mx, my):
            career["browsing_jobs"] = False
            return
        if state["actions_remaining"] <= 0:
            return
        for job, take_rect in buttons["jobs"]:
            if take_rect.collidepoint(mx, my):
                if mode == "side":
                    career["side_job"] = dict(job)
                    _log(state, f"Started a part-time job: {job['title']}.")
                else:
                    career["job"] = _new_job(job)
                career["browsing_jobs"] = False
                state["actions_remaining"] -= 1
                return
        return

    for key in ("work", "fame"):
        if "view_" + key in buttons and buttons["view_" + key].collidepoint(mx, my):
            career["view"] = key
            return
    if career.get("view") == "fame":
        if state["actions_remaining"] <= 0:
            return
        for h, r2 in buttons.get("hustles", []):
            if r2.collidepoint(mx, my):
                career["hustle"] = dict(h)
                state["actions_remaining"] -= 1
                _log(state, f"Started a side career as a {h['title']}.")
                return
        if "hustle_quit" in buttons and buttons["hustle_quit"].collidepoint(mx, my):
            _log(state, f"Gave up the side career as a {career['hustle']['title']}.")
            career["hustle"] = None
            return
        fj = active_fame_job(career)
        if fj:
            for k, b in buttons.items():
                if k.startswith("f_") and b.collidepoint(mx, my):
                    _log(state, do_fame_action(k[2:], career, state, fj))
                    return
        return

    if "side_find" in buttons and buttons["side_find"].collidepoint(mx, my):
        career["browsing_jobs"] = "side"
        career["scroll"] = 0
        return
    if state["actions_remaining"] <= 0:
        return
    if "side_quit" in buttons and buttons["side_quit"].collidepoint(mx, my):
        _log(state, f"Left the part-time job as {career['side_job']['title']}.")
        career["side_job"] = None
        state["actions_remaining"] -= 1
        return

    stats = state["stats"]
    if career["job"]:
        job = career["job"]
        used = state["actions_used"]
        if buttons["better"].collidepoint(mx, my):
            career["browsing_jobs"] = "main"
            career["scroll"] = 0
        elif buttons["quit"].collidepoint(mx, my):
            career["job"] = None
            state["actions_remaining"] -= 1
        elif buttons["ot"].collidepoint(mx, my):
            n = used.get("__ot__", 0)
            bonus = max(1, int(job["pay"] * 0.15 / (1 + n)))
            state["money"] += bonus
            stats["mental"] = max(0, stats["mental"] - 2)
            if n >= 2:
                stats["physical"] = max(0, stats["physical"] - 1)
            job["perf"] = min(100, job.get("perf", 55) + 6)
            used["__ot__"] = n + 1
            state["actions_remaining"] -= 1
            _log(state, f"Worked overtime and earned ${bonus}.")
        elif buttons["net"].collidepoint(mx, my):
            n = used.get("__net__", 0)
            stats["social"] = min(100, stats["social"] + max(1, 2 - n // 2))
            job["perf"] = min(100, job.get("perf", 55) + 3)
            used["__net__"] = n + 1
            state["actions_remaining"] -= 1
        elif buttons["promo"].collidepoint(mx, my) and can_promote(job):
            chance = 0.15 + job.get("perf", 55) / 150 + (stats["academic"] - 50) / 400
            state["actions_remaining"] -= 1
            if random.random() < max(0.05, min(0.85, chance)):
                job["level"] = job.get("level", 0) + 1
                job["since"] = 0
                job["pay"] = int(job["pay"] * 1.25) + 2
                job["title"] = TITLE_PREFIX[job["level"]] + job["base"]
                stats["wealth"] = min(100, stats["wealth"] + 3)
                _log(state, f"Promoted to {job['title']}!")
            else:
                job["perf"] = max(0, job.get("perf", 55) - 5)
                _log(state, "Asked for a promotion but was turned down.")
        return

    if "search" in buttons and buttons["search"].collidepoint(mx, my):
        career["browsing_jobs"] = "main"
        career["scroll"] = 0

DEBT_INTEREST = 0.05
SAVINGS_INTEREST = 0.03

def advance_career_year(career, state, age):
    """Called once per year at year-end: wages, performance, promotions
    and dismissal, part-time pay, tuition, student debt, savings interest
    and progress through university."""
    stats = state["stats"]
    log = lambda t: _log(state, t)
    both = bool(career["job"]) + bool(career.get("side_job")) + bool(career["enrolled"]) >= 2

    job = career["job"]
    if job:
        job["years"] = job.get("years", 0) + 1
        job["since"] = job.get("since", 0) + 1
        perf = job.get("perf", 55) + random.randint(-4, 3) - (5 if stats["mental"] < 30 else 0) + (2 if stats["mental"] >= 70 else 0)
        job["perf"] = max(0, min(100, perf))
        job["pay"] = max(job["pay"], round(job["pay"] * 1.03))
        if "car" in state["owned"]:
            state["money"] += max(1, job["pay"] // 20)   # the commute is easier
        stats["wealth"] = max(0, min(100, stats["wealth"] + job["wealth"]))
        state["money"] += job["pay"]
        if job.get("fame"):
            bonus = int(job["pay"] * career.get("fame", 0) / 100)
            if bonus:
                state["money"] += bonus
                log(f"Fame earned you an extra ${bonus} this year.")
        elif stats["looks"] >= 70:
            state["money"] += max(1, job["pay"] // 20)   # looks open doors
        career["experience"] = career.get("experience", 0) + 1
        if job["perf"] < 15 and random.random() < 0.4:
            log(f"You were let go from your job as {job['title']}.")
            career["job"] = None
    elif age < 18:
        wealth = state.get("family_wealth", "Comfortable")
        state["money"] += {"Struggling": 8, "Comfortable": 15, "Wealthy": 30}[wealth]  # pocket money

    hustle = career.get("hustle")
    if hustle:
        state["money"] += hustle["pay"] // 2 + int(hustle["pay"] * career.get("fame", 0) / 200)
        if career["job"] or career["enrolled"] or age < 18:
            stats["mental"] = max(0, stats["mental"] - 1)    # it takes up your spare time
    old_tier = fame_tier(career.get("fame", 0))
    if career.get("fame", 0) > 0:
        in_fame_job = bool((career["job"] and career["job"].get("fame")) or hustle)
        career["fame"] = max(0, career["fame"] - (3 if in_fame_job else 8))
        new_tier = fame_tier(career["fame"])
        if new_tier != old_tier:
            log(f"Your fame status is now: {new_tier}.")

    side = career.get("side_job")
    if side:
        if side["enrolled"] and not career["enrolled"]:
            log(f"Lost the {side['title']} job when you stopped studying.")
            career["side_job"] = None
        else:
            state["money"] += side["pay"]
            stats["wealth"] = min(100, stats["wealth"] + 1)
            stats["mental"] = max(0, stats["mental"] - (2 if both else 1))
            if side["title"] in ("Cafe Assistant", "Retail Assistant", "Weekend Bar Work", "Babysitter"):
                stats["social"] = min(100, stats["social"] + 1)
            if side.get("intern"):
                career["experience"] = career.get("experience", 0) + 1
                stats["academic"] = min(100, stats["academic"] + 1)

    if career["enrolled"]:
        fund = career.get("funding") or {}
        owe = fund.get("owe", 0)
        if owe:
            if fund.get("mode") == "loan":
                state["debt"] = state.get("debt", 0) + owe
                log(f"Took a ${owe} student loan for fees.")
            else:
                paid = min(owe, state["money"])
                state["money"] -= paid
                if paid < owe:
                    state["debt"] = state.get("debt", 0) + (owe - paid)
                    log(f"Couldn't cover all the fees: ${owe - paid} was added to your debt.")
                else:
                    log(f"Paid ${paid} in tuition.")
        career["uni_years_done"] += 1
        target = career["uni_target"]
        if career["uni_years_done"] >= UNI_DURATION[target]:
            career["education"] = target
            career["prestige"] = max(career.get("prestige", 0), career.get("college_prestige", 0))
            if target == "Diploma":
                career["trade"] = career.get("course")
            elif stats["academic"] >= 75:
                career["prestige"] = min(3, career["prestige"] + 1)
                log("You graduated with honours (+1 prestige).")
            career["enrolled"] = False
            career["uni_target"] = None
            career["uni_years_done"] = 0
            career["college_name"] = None
            career["funding"] = None

    debt = state.get("debt", 0)
    if debt > 0:
        debt = int(round(debt * (1 + DEBT_INTEREST)))
        income = (career["job"]["pay"] if career["job"] else 0) + (career["side_job"]["pay"] if career.get("side_job") else 0)
        if income and not career["enrolled"]:
            pay = min(debt, state["money"], max(5, int(income * 0.2)))
            state["money"] -= pay
            debt -= pay
            if pay:
                log(f"Repaid ${pay} of your debt.")
        state["debt"] = debt
    sv = state.get("savings", 0)
    if sv > 0:
        state["savings"] = int(round(sv * (1 + SAVINGS_INTEREST)))
