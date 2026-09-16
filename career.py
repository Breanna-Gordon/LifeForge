import pygame
from constants import (
    WHITE, BLACK, LIGHT_GREY, DARK_GREY, ACCENT,
    font, small_font, draw_text, draw_rounded_rect
)

EDUCATION_RANK = {"None": 0, "Bachelor's": 1, "Master's": 2, "PhD": 3}
NEXT_LEVEL = {"None": "Bachelor's", "Bachelor's": "Master's", "Master's": "PhD", "PhD": None}
REQUIRED_ACADEMIC = {"Bachelor's": 50, "Master's": 65, "PhD": 80}
UNI_DURATION = {"Bachelor's": 3, "Master's": 2, "PhD": 3}

JOB_TIERS = [
    {"title": "Cashier", "min_education": "None", "wealth": 3},
    {"title": "Warehouse Worker", "min_education": "None", "wealth": 4},
    {"title": "Office Assistant", "min_education": "None", "wealth": 5},
    {"title": "Teacher", "min_education": "Bachelor's", "wealth": 8},
    {"title": "Accountant", "min_education": "Bachelor's", "wealth": 9},
    {"title": "Software Engineer", "min_education": "Bachelor's", "wealth": 11},
    {"title": "Manager", "min_education": "Master's", "wealth": 14},
    {"title": "Lawyer", "min_education": "Master's", "wealth": 16},
    {"title": "Doctor", "min_education": "PhD", "wealth": 20},
    {"title": "University Professor", "min_education": "PhD", "wealth": 15},
]

def eligible_jobs(career):
    rank = EDUCATION_RANK[career["education"]]
    current_title = career["job"]["title"] if career["job"] else None
    return [j for j in JOB_TIERS
            if EDUCATION_RANK[j["min_education"]] <= rank and j["title"] != current_title]

def get_button_layout(rect, count):
    button_w = 220
    button_h = 36
    gap = 14
    total_w = count * button_w + (count - 1) * gap
    start_x = rect.centerx - total_w // 2
    return [pygame.Rect(start_x + i * (button_w + gap), rect.y + 60, button_w, button_h)
            for i in range(count)]

def draw_button(screen, rect, label, mouse_pos, disabled=False, done=False):
    hovered = rect.collidepoint(mouse_pos)
    fill = LIGHT_GREY if (disabled or done) else (ACCENT if hovered else WHITE)
    draw_rounded_rect(screen, fill, rect, radius=8)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=8)
    text_colour = DARK_GREY if (disabled or done) else BLACK
    draw_text(screen, label, small_font, text_colour, rect.centerx, rect.centery, centre=True)

def draw_career_tab(screen, rect, mouse_pos, age, stats, career, interacted_this_year):
    academic = stats["academic"]

    if career.get("browsing_jobs"):
        draw_text(screen, "Choose a job:", font, BLACK, rect.x, rect.y)
        back_rect = pygame.Rect(rect.x, rect.y + 30, 120, 30)
        draw_button(screen, back_rect, "Back", mouse_pos)

        jobs = eligible_jobs(career)
        y = rect.y + 74
        job_rects = []
        for job in jobs:
            row_rect = pygame.Rect(rect.x, y, rect.width, 34)
            draw_rounded_rect(screen, WHITE, row_rect, radius=6)
            pygame.draw.rect(screen, BLACK, row_rect, 1, border_radius=6)
            draw_text(screen, f"{job['title']}  (+{job['wealth']} wealth/yr)", small_font, BLACK,
                      row_rect.x + 10, row_rect.y + 8)
            take_rect = pygame.Rect(row_rect.right - 90, row_rect.y + 4, 80, 26)
            hovered = take_rect.collidepoint(mouse_pos)
            draw_rounded_rect(screen, ACCENT if hovered else LIGHT_GREY, take_rect, radius=6)
            pygame.draw.rect(screen, BLACK, take_rect, 1, border_radius=6)
            draw_text(screen, "Take", small_font, BLACK, take_rect.centerx, take_rect.centery, centre=True)
            job_rects.append((job, take_rect))
            y += 40
        return {"back": back_rect, "jobs": job_rects}

    lines = [f"Academic: {academic}", f"Education: {career['education']}"]

    if career["enrolled"]:
        target = career["uni_target"]
        duration = UNI_DURATION[target]
        lines.append(f"Studying for {target} — Year {career['uni_years_done']}/{duration}")
        for i, line in enumerate(lines):
            draw_text(screen, line, small_font, BLACK if i == 2 else DARK_GREY, rect.x, rect.y + i * 20)

        study_rect, dropout_rect = get_button_layout(rect, 2)
        study_done = "__study__" in interacted_this_year
        draw_button(screen, study_rect, "Study Harder", mouse_pos, done=study_done)
        draw_button(screen, dropout_rect, "Drop Out", mouse_pos)
        return {"study": study_rect, "dropout": dropout_rect}

    if career["job"]:
        job = career["job"]
        lines.append(f"Working as {job['title']} (+{job['wealth']} wealth/yr)")
        for i, line in enumerate(lines):
            draw_text(screen, line, small_font, BLACK if i == 2 else DARK_GREY, rect.x, rect.y + i * 20)

        buttons = {}
        better_rect, quit_rect = get_button_layout(rect, 2)
        draw_button(screen, better_rect, "Look for a Better Job", mouse_pos)
        draw_button(screen, quit_rect, "Quit Job", mouse_pos)
        buttons["better"] = better_rect
        buttons["quit"] = quit_rect

        next_level = NEXT_LEVEL[career["education"]]
        if next_level:
            enroll_rect = pygame.Rect(rect.centerx - 110, rect.y + 110, 220, 34)
            can_enroll = academic >= REQUIRED_ACADEMIC[next_level]
            draw_button(screen, enroll_rect, f"Study for {next_level}", mouse_pos, disabled=not can_enroll)
            buttons["enroll"] = enroll_rect
        return buttons

    for i, line in enumerate(lines):
        draw_text(screen, line, small_font, DARK_GREY, rect.x, rect.y + i * 20)

    buttons = {}
    if age < 18:
        study_rect = pygame.Rect(rect.centerx - 110, rect.y + 60, 220, 36)
        study_done = "__study__" in interacted_this_year
        draw_button(screen, study_rect, "Study", mouse_pos, done=study_done)
        buttons["study"] = study_rect
    else:
        next_level = NEXT_LEVEL[career["education"]]
        rects = get_button_layout(rect, 2 if next_level else 1)
        if next_level:
            can_enroll = academic >= REQUIRED_ACADEMIC[next_level]
            draw_button(screen, rects[0], f"Study for {next_level}", mouse_pos, disabled=not can_enroll)
            buttons["enroll"] = rects[0]
            draw_button(screen, rects[1], "Search for a Job", mouse_pos)
            buttons["search"] = rects[1]
        else:
            draw_button(screen, rects[0], "Search for a Job", mouse_pos)
            buttons["search"] = rects[0]

    return buttons

def handle_career_click(mx, my, buttons, age, stats, career, interacted_this_year):
    if career.get("browsing_jobs"):
        if buttons["back"].collidepoint(mx, my):
            career["browsing_jobs"] = False
            return
        for job, take_rect in buttons["jobs"]:
            if take_rect.collidepoint(mx, my):
                career["job"] = dict(job)
                career["browsing_jobs"] = False
                return
        return

    if career["enrolled"]:
        if buttons["study"].collidepoint(mx, my) and "__study__" not in interacted_this_year:
            stats["academic"] = max(0, min(100, stats["academic"] + 3))
            stats["mental"] = max(0, min(100, stats["mental"] - 1))
            interacted_this_year.add("__study__")
        elif buttons["dropout"].collidepoint(mx, my):
            career["enrolled"] = False
            career["uni_target"] = None
            career["uni_years_done"] = 0
        return

    if career["job"]:
        if buttons["better"].collidepoint(mx, my):
            career["browsing_jobs"] = True
        elif buttons["quit"].collidepoint(mx, my):
            career["job"] = None
        elif "enroll" in buttons and buttons["enroll"].collidepoint(mx, my):
            next_level = NEXT_LEVEL[career["education"]]
            if next_level and stats["academic"] >= REQUIRED_ACADEMIC[next_level]:
                career["enrolled"] = True
                career["uni_target"] = next_level
                career["uni_years_done"] = 0
                career["job"] = None
        return

    if age < 18:
        if "study" in buttons and buttons["study"].collidepoint(mx, my) and "__study__" not in interacted_this_year:
            stats["academic"] = max(0, min(100, stats["academic"] + 4))
            stats["mental"] = max(0, min(100, stats["mental"] + 1))
            interacted_this_year.add("__study__")
        return

    if "enroll" in buttons and buttons["enroll"].collidepoint(mx, my):
        next_level = NEXT_LEVEL[career["education"]]
        if next_level and stats["academic"] >= REQUIRED_ACADEMIC[next_level]:
            career["enrolled"] = True
            career["uni_target"] = next_level
            career["uni_years_done"] = 0
    elif "search" in buttons and buttons["search"].collidepoint(mx, my):
        career["browsing_jobs"] = True

def advance_career_year(career, stats):
    """Called once per year at year-end — applies job income and
    progresses university enrolment."""
    if career["job"]:
        stats["wealth"] = max(0, min(100, stats["wealth"] + career["job"]["wealth"]))

    if career["enrolled"]:
        career["uni_years_done"] += 1
        target = career["uni_target"]
        if career["uni_years_done"] >= UNI_DURATION[target]:
            career["education"] = target
            career["enrolled"] = False
            career["uni_target"] = None
            career["uni_years_done"] = 0