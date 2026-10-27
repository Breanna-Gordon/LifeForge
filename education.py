import pygame
from constants import (
    WHITE, BLACK, LIGHT_GREY, DARK_GREY, ACCENT,
    font, small_font, draw_text, draw_rounded_rect
)

NEXT_LEVEL = {"None": "Bachelor's", "Bachelor's": "Master's", "Master's": "PhD", "PhD": None}
UNI_DURATION = {"Bachelor's": 3, "Master's": 2, "PhD": 3}

# Different colleges for the same degree need different Academic levels to
# get into, and hand the graduate a different prestige tier — used later
# by career.py to gate the best jobs. No age ceiling anywhere here: once
# you're 18+ you can apply at any age, not just right at 18.
COLLEGES = {
    "Bachelor's": [
        {"name": "Community College", "required_academic": 25, "prestige": 1},
        {"name": "State University", "required_academic": 50, "prestige": 2},
        {"name": "Ivy League University", "required_academic": 75, "prestige": 3},
    ],
    "Master's": [
        {"name": "State University", "required_academic": 40, "prestige": 2},
        {"name": "Ivy League University", "required_academic": 70, "prestige": 3},
    ],
    "PhD": [
        {"name": "State University", "required_academic": 55, "prestige": 2},
        {"name": "Ivy League University", "required_academic": 80, "prestige": 3},
    ],
}

# Courses: the offset is added to every college's entry requirement.
COURSES = {
    "Education":        {"offset": -5},
    "Arts":             {"offset": -5},
    "Sport Science":    {"offset": -5, "athletic": 50},
    "Business":         {"offset": 0},
    "Computer Science": {"offset": 5},
    "Engineering":      {"offset": 8},
    "Law":              {"offset": 10},
    "Medicine":         {"offset": 15},
}
SCHOLARSHIP_BONUS = 25

def entry_requirement(level, college, course, scholarship):
    offset = COURSES.get(course, {"offset": 0})["offset"] if level == "Bachelor's" else 0
    bonus = SCHOLARSHIP_BONUS if (scholarship and level == "Bachelor's") else 0
    return college["required_academic"] + offset - bonus

def eligible_colleges(level, academic, course=None, scholarship=False):
    return [c for c in COLLEGES.get(level, [])
            if academic >= entry_requirement(level, c, course, scholarship)]

def course_open(name, stats, scholarship):
    c = COURSES[name]
    if stats["athletic"] < c.get("athletic", 0):
        return False
    return bool(eligible_colleges("Bachelor's", stats["academic"], name, scholarship))

def draw_button(screen, rect, label, mouse_pos, disabled=False, done=False):
    hovered = rect.collidepoint(mouse_pos)
    fill = LIGHT_GREY if (disabled or done) else (ACCENT if hovered else WHITE)
    draw_rounded_rect(screen, fill, rect, radius=8)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=8)
    text_colour = DARK_GREY if (disabled or done) else BLACK
    draw_text(screen, label, small_font, text_colour, rect.centerx, rect.centery, centre=True)

def draw_education_tab(screen, rect, mouse_pos, age, state, career):
    stats = state["stats"]
    academic = stats["academic"]
    actions_used = state["actions_used"]
    no_budget = state["actions_remaining"] <= 0
    scholarship = state.get("scholarship", False)

    course = career.get("course")
    lines = [f"Academic: {academic}", f"Education: {career['education']}" + (f" ({course})" if course else "")]

    if career["enrolled"]:
        target = career["uni_target"]
        duration = UNI_DURATION[target]
        lines.append(f"Studying for {target}" + (f" in {course}" if course else "") +
                     f" at {career['college_name']}. Year {career['uni_years_done']}/{duration}")
        for i, line in enumerate(lines):
            draw_text(screen, line, small_font, BLACK if i == 2 else DARK_GREY, rect.x, rect.y + i * 20)
        study_rect = pygame.Rect(rect.centerx - 230, rect.y + 70, 220, 36)
        dropout_rect = pygame.Rect(rect.centerx + 10, rect.y + 70, 220, 36)
        study_done = actions_used.get("__study__", 0) >= 1
        draw_button(screen, study_rect, "Study Harder", mouse_pos, disabled=no_budget, done=study_done)
        draw_button(screen, dropout_rect, "Drop Out", mouse_pos, disabled=no_budget)
        return {"study": study_rect, "dropout": dropout_rect}

    for i, line in enumerate(lines):
        draw_text(screen, line, small_font, DARK_GREY, rect.x, rect.y + i * 20)

    buttons = {}

    if age < 18:
        study_rect = pygame.Rect(rect.centerx - 110, rect.y + 60, 220, 36)
        study_done = actions_used.get("__study__", 0) >= 1
        draw_button(screen, study_rect, "Study", mouse_pos, disabled=no_budget, done=study_done)
        buttons["study"] = study_rect
        draw_text(screen, "Join clubs and sports from the Activities tab. From 18 you can apply to university.",
                  small_font, DARK_GREY, rect.x, rect.y + 112)
        return buttons

    next_level = NEXT_LEVEL[career["education"]]
    if next_level is None:
        draw_text(screen, "You've completed the highest level of education.",
                  small_font, DARK_GREY, rect.x, rect.y + 60)
        return buttons

    if next_level == "Bachelor's" and not career.get("pending_course"):
        draw_text(screen, "Choose a course for your Bachelor's:", font, BLACK, rect.x, rect.y + 46)
        cols = 2
        col_w = (rect.width - 10) // cols
        hits = []
        for n, name in enumerate(COURSES):
            r = pygame.Rect(rect.x + (n % cols) * (col_w + 10), rect.y + 74 + (n // cols) * 38, col_w, 32)
            ok = course_open(name, stats, scholarship)
            hovered = r.collidepoint(mouse_pos) and ok
            draw_rounded_rect(screen, ACCENT if hovered else (WHITE if ok else LIGHT_GREY), r, radius=8)
            pygame.draw.rect(screen, BLACK, r, 2, border_radius=8)
            need = COURSES[name].get("athletic")
            if ok:
                note = ""
            elif need and stats["athletic"] < need:
                note = f"  (Athletic {need}+)"
            else:
                lowest = min(entry_requirement("Bachelor's", c, name, scholarship) for c in COLLEGES["Bachelor's"])
                note = f"  (Academic {lowest}+)"
            draw_text(screen, name + note, small_font, BLACK if ok else DARK_GREY, r.x + 10, r.centery - 8)
            hits.append((name, r))
        buttons["courses"] = hits
        return buttons

    chosen_course = career.get("pending_course") if next_level == "Bachelor's" else course
    options = eligible_colleges(next_level, academic, chosen_course, scholarship)
    title = f"Apply for a {next_level}" + (f" in {chosen_course}" if chosen_course and next_level == "Bachelor's" else "") + ":"
    draw_text(screen, title, font, BLACK, rect.x, rect.y + 46)
    if next_level == "Bachelor's":
        change_rect = pygame.Rect(rect.right - 130, rect.y + 44, 130, 26)
        hovered = change_rect.collidepoint(mouse_pos)
        draw_rounded_rect(screen, ACCENT if hovered else WHITE, change_rect, radius=6)
        pygame.draw.rect(screen, BLACK, change_rect, 1, border_radius=6)
        draw_text(screen, "Change course", small_font, BLACK, change_rect.centerx, change_rect.centery, centre=True)
        buttons["change"] = change_rect

    if not options:
        lowest = min(entry_requirement(next_level, c, chosen_course, scholarship) for c in COLLEGES[next_level])
        draw_text(screen, f"Needs Academic {lowest}+ to qualify anywhere yet.",
                  small_font, DARK_GREY, rect.x, rect.y + 84)
        return buttons

    college_rects = []
    y = rect.y + 80
    for college in options:
        row_rect = pygame.Rect(rect.x, y, rect.width, 34)
        draw_rounded_rect(screen, WHITE, row_rect, radius=6)
        pygame.draw.rect(screen, BLACK, row_rect, 1, border_radius=6)
        stars = "*" * college["prestige"]
        extra = " (scholarship)" if scholarship and next_level == "Bachelor's" and academic < college["required_academic"] + (COURSES.get(chosen_course, {"offset": 0})["offset"]) else ""
        draw_text(screen, f"{college['name']}  ({stars} prestige){extra}", small_font, BLACK,
                  row_rect.x + 10, row_rect.y + 8)
        apply_rect = pygame.Rect(row_rect.right - 90, row_rect.y + 4, 80, 26)
        hovered = apply_rect.collidepoint(mouse_pos)
        fill = LIGHT_GREY if no_budget else (ACCENT if hovered else LIGHT_GREY)
        draw_rounded_rect(screen, fill, apply_rect, radius=6)
        pygame.draw.rect(screen, BLACK, apply_rect, 1, border_radius=6)
        draw_text(screen, "Apply", small_font, BLACK, apply_rect.centerx, apply_rect.centery, centre=True)
        college_rects.append((college, apply_rect))
        y += 40

    buttons["colleges"] = college_rects
    buttons["next_level"] = next_level
    return buttons

def handle_education_click(mx, my, buttons, age, state, career):
    actions_used = state["actions_used"]
    stats = state["stats"]

    # choosing a course is free; applying costs an action
    if "courses" in buttons:
        for name, r in buttons["courses"]:
            if r.collidepoint(mx, my) and course_open(name, stats, state.get("scholarship", False)):
                career["pending_course"] = name
        return
    if "change" in buttons and buttons["change"].collidepoint(mx, my):
        career["pending_course"] = None
        return

    if state["actions_remaining"] <= 0:
        return

    if career["enrolled"]:
        if buttons["study"].collidepoint(mx, my) and actions_used.get("__study__", 0) < 1:
            stats["academic"] = max(0, min(100, stats["academic"] + 3))
            stats["mental"] = max(0, min(100, stats["mental"] - 1))
            actions_used["__study__"] = 1
            state["actions_remaining"] -= 1
        elif buttons["dropout"].collidepoint(mx, my):
            career["enrolled"] = False
            career["uni_target"] = None
            career["uni_years_done"] = 0
            career["college_name"] = None
            state["actions_remaining"] -= 1
        return

    if age < 18:
        if "study" in buttons and buttons["study"].collidepoint(mx, my) and actions_used.get("__study__", 0) < 1:
            stats["academic"] = max(0, min(100, stats["academic"] + 4))
            stats["mental"] = max(0, min(100, stats["mental"] + 1))
            actions_used["__study__"] = 1
            state["actions_remaining"] -= 1
        return

    if "colleges" in buttons:
        for college, apply_rect in buttons["colleges"]:
            if apply_rect.collidepoint(mx, my):
                if buttons["next_level"] == "Bachelor's":
                    career["course"] = career.get("pending_course")
                career["enrolled"] = True
                career["uni_target"] = buttons["next_level"]
                career["college_name"] = college["name"]
                career["college_prestige"] = college["prestige"]
                career["uni_years_done"] = 0
                career["job"] = None  # studying full-time
                state["actions_remaining"] -= 1
                return
