import pygame
from constants import (
    WHITE, BLACK, LIGHT_GREY, DARK_GREY, ACCENT,
    font, small_font, draw_text, draw_rounded_rect
)
from education import UNI_DURATION

EDUCATION_RANK = {"None": 0, "Bachelor's": 1, "Master's": 2, "PhD": 3}

# Jobs now care about how old you are, your qualifications AND course, your
# stats, and sometimes the clubs or teams you belong to.
#   courses: degree subjects that qualify (None = any)
#   stats:   minimum stat levels
#   any_of:  you must be in at least one of these clubs/teams
def J(title, age, edu, pay, wealth, prestige=0, courses=None, stats=None, any_of=None):
    return {"title": title, "min_age": age, "min_education": edu, "min_prestige": prestige,
            "courses": courses, "stats": stats or {}, "any_of": any_of, "wealth": wealth, "pay": pay}

JOB_TIERS = [
    J("Paper Round", 13, "None", 6, 1),
    J("Babysitter", 14, "None", 8, 1, stats={"social": 40}),
    J("Cashier", 16, "None", 15, 3),
    J("Waiter", 16, "None", 14, 3, stats={"social": 40}),
    J("Warehouse Worker", 18, "None", 18, 4, stats={"physical": 45}),
    J("Office Assistant", 18, "None", 22, 5),
    J("Fitness Instructor", 18, "None", 24, 5, stats={"athletic": 60}),
    J("Musician", 16, "None", 20, 4, stats={"social": 45}, any_of=["band"]),
    J("Model", 18, "None", 40, 8, stats={"looks": 75}),
    J("Actor", 18, "None", 38, 7, stats={"looks": 60, "social": 60}, any_of=["drama"]),
    J("Professional Athlete", 18, "None", 70, 12, stats={"athletic": 85},
      any_of=["football", "basket", "swim", "track", "rugby"]),
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

def stats_ok(job, stats):
    return all(stats[k] >= v for k, v in job["stats"].items())

def eligible_jobs(career, state):
    """Returns (jobs you can take now, count of age-appropriate jobs you
    can't yet qualify for)."""
    age = state["age"]
    rank = EDUCATION_RANK[career["education"]]
    prestige = career.get("prestige", 0)
    course = career.get("course")
    current = career["job"]["title"] if career["job"] else None
    ok, locked = [], 0
    for j in JOB_TIERS:
        if j["min_age"] > age or j["title"] == current:
            continue
        qualified = (EDUCATION_RANK[j["min_education"]] <= rank
                     and j["min_prestige"] <= prestige
                     and (j["courses"] is None or course in j["courses"])
                     and stats_ok(j, state["stats"])
                     and (j["any_of"] is None or any(a in state["activities"] for a in j["any_of"])))
        if qualified:
            ok.append(j)
        else:
            locked += 1
    ok.sort(key=lambda j: -j["pay"])
    return ok, locked

def get_button_layout(rect, count):
    button_w = 220
    button_h = 36
    gap = 14
    total_w = count * button_w + (count - 1) * gap
    start_x = rect.centerx - total_w // 2
    return [pygame.Rect(start_x + i * (button_w + gap), rect.y + 60, button_w, button_h)
            for i in range(count)]

def draw_button(screen, rect, label, mouse_pos, disabled=False):
    hovered = rect.collidepoint(mouse_pos)
    fill = LIGHT_GREY if disabled else (ACCENT if hovered else WHITE)
    draw_rounded_rect(screen, fill, rect, radius=8)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=8)
    text_colour = DARK_GREY if disabled else BLACK
    draw_text(screen, label, small_font, text_colour, rect.centerx, rect.centery, centre=True)

def draw_career_tab(screen, rect, mouse_pos, career, state):
    no_budget = state["actions_remaining"] <= 0

    if career.get("browsing_jobs"):
        draw_text(screen, "Choose a job:", font, BLACK, rect.x, rect.y)
        back_rect = pygame.Rect(rect.x, rect.y + 30, 120, 30)
        draw_button(screen, back_rect, "Back", mouse_pos)

        jobs, locked = eligible_jobs(career, state)
        rows = 6
        scroll = max(0, min(career.get("scroll", 0), max(0, len(jobs) - rows)))
        career["scroll"] = scroll
        if locked:
            draw_text(screen, f"{locked} more jobs need better stats, a course, or a club or team.",
                      small_font, DARK_GREY, rect.x + 130, rect.y + 37)
        y = rect.y + 70
        job_rects = []
        if not jobs:
            draw_text(screen, "No new jobs available yet. Improve your stats, join clubs, or study.",
                      small_font, DARK_GREY, rect.x, y)
        for job in jobs[scroll:scroll + rows]:
            row_rect = pygame.Rect(rect.x, y, rect.width, 34)
            draw_rounded_rect(screen, WHITE, row_rect, radius=6)
            pygame.draw.rect(screen, BLACK, row_rect, 1, border_radius=6)
            draw_text(screen, f"{job['title']}  (${job['pay']}/yr)", small_font, BLACK,
                      row_rect.x + 10, row_rect.y + 8)
            take_rect = pygame.Rect(row_rect.right - 90, row_rect.y + 4, 80, 26)
            hovered = take_rect.collidepoint(mouse_pos)
            fill = LIGHT_GREY if no_budget else (ACCENT if hovered else LIGHT_GREY)
            draw_rounded_rect(screen, fill, take_rect, radius=6)
            pygame.draw.rect(screen, BLACK, take_rect, 1, border_radius=6)
            draw_text(screen, "Take", small_font, BLACK, take_rect.centerx, take_rect.centery, centre=True)
            job_rects.append((job, take_rect))
            y += 40
        if len(jobs) > rows:
            draw_text(screen, "Scroll for more", small_font, DARK_GREY, rect.right - 120, rect.y + 2)
        return {"back": back_rect, "jobs": job_rects}

    if career["job"]:
        job = career["job"]
        draw_text(screen, f"Working as {job['title']}", font, BLACK, rect.x, rect.y)
        draw_text(screen, f"Pay: ${job['pay']}/yr", small_font, DARK_GREY, rect.x, rect.y + 26)

        better_rect, quit_rect = get_button_layout(rect, 2)
        draw_button(screen, better_rect, "Look for a Better Job", mouse_pos, disabled=no_budget)
        draw_button(screen, quit_rect, "Quit Job", mouse_pos, disabled=no_budget)
        return {"better": better_rect, "quit": quit_rect}

    if state["age"] < 13:
        draw_text(screen, "You're too young to work. Jobs start at 13.", small_font, DARK_GREY, rect.x, rect.y)
        return {}
    draw_text(screen, "You're not currently employed.", small_font, DARK_GREY, rect.x, rect.y)
    search_rect = pygame.Rect(rect.centerx - 110, rect.y + 40, 220, 36)
    draw_button(screen, search_rect, "Search for a Job", mouse_pos, disabled=no_budget)
    return {"search": search_rect}

def handle_career_click(mx, my, buttons, career, state):
    if state["actions_remaining"] <= 0:
        return

    if career.get("browsing_jobs"):
        if buttons["back"].collidepoint(mx, my):
            career["browsing_jobs"] = False
            return
        for job, take_rect in buttons["jobs"]:
            if take_rect.collidepoint(mx, my):
                career["job"] = dict(job)
                career["browsing_jobs"] = False
                state["actions_remaining"] -= 1
                return
        return

    if career["job"]:
        if buttons["better"].collidepoint(mx, my):
            career["browsing_jobs"] = True
        elif buttons["quit"].collidepoint(mx, my):
            career["job"] = None
            state["actions_remaining"] -= 1
        return

    if "search" in buttons and buttons["search"].collidepoint(mx, my):
        career["browsing_jobs"] = True

def advance_career_year(career, state, age):
    """Called once per year at year-end — applies job income, pocket
    money for minors, and progresses university enrolment."""
    stats = state["stats"]

    if career["job"]:
        stats["wealth"] = max(0, min(100, stats["wealth"] + career["job"]["wealth"]))
        state["money"] += career["job"]["pay"]
    elif age < 18:
        state["money"] += 15  # pocket money

    if career["enrolled"]:
        career["uni_years_done"] += 1
        target = career["uni_target"]
        if career["uni_years_done"] >= UNI_DURATION[target]:
            career["education"] = target
            career["prestige"] = max(career.get("prestige", 0), career.get("college_prestige", 0))
            career["enrolled"] = False
            career["uni_target"] = None
            career["uni_years_done"] = 0
            career["college_name"] = None
