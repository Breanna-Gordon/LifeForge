import worldjobs
from constants import fmt
from constants import OUTLINE, INK, MUTED, draw_card, draw_pill, draw_shadow
import pygame
from constants import (
    WHITE, BLACK, LIGHT_GREY, DARK_GREY, ACCENT,
    font, small_font, draw_text, draw_rounded_rect
)

NEXT_LEVEL = {"None": "Bachelor's", "Diploma": "Bachelor's", "Bachelor's": "Master's", "Master's": "PhD", "PhD": None}
UNI_DURATION = {"Diploma": 2, "Bachelor's": 3, "Master's": 2, "PhD": 3}

# Different colleges for the same degree need different Academic levels to
# get into, and hand the graduate a different prestige tier — used later
# by career.py to gate the best jobs. No age ceiling anywhere here: once
# you're 18+ you can apply at any age, not just right at 18.
# "tuition" is the cost per year.
COLLEGES = {
    "Diploma": [
        {"name": "Technical College", "required_academic": 20, "prestige": 1, "tuition": 6000},
    ],
    "Bachelor's": [
        {"name": "Community College", "required_academic": 25, "prestige": 1, "tuition": 8000},
        {"name": "State University", "required_academic": 50, "prestige": 2, "tuition": 16000},
        {"name": "Ivy League University", "required_academic": 75, "prestige": 3, "tuition": 32000},
    ],
    "Master's": [
        {"name": "State University", "required_academic": 40, "prestige": 2, "tuition": 20000},
        {"name": "Ivy League University", "required_academic": 70, "prestige": 3, "tuition": 36000},
    ],
    "PhD": [
        {"name": "State University", "required_academic": 55, "prestige": 2, "tuition": 12000},
        {"name": "Ivy League University", "required_academic": 80, "prestige": 3, "tuition": 24000},
    ],
}
TRADES = ["Electrician", "Plumber", "Chef", "Mechanic", "Hairdresser", "Nursing Assistant",
          "Carpenter", "Beautician", "Paramedic", "Police Training", "Firefighter", "Pilot Licence"]

# How much of the fees your family covers (if your parents are around and
# you get on with them).
FAMILY_SHARE = {"Struggling": 0.0, "Comfortable": 0.4, "Wealthy": 1.0}

def funding_plan(level, college, course, state):
    """Works out who pays what per year: scholarship first, then family,
    then you (savings or a student loan)."""
    tuition = college["tuition"]
    surplus = state["stats"]["academic"] - entry_requirement(level, college, course, False)
    pct = 1.0 if surplus >= 25 else 0.5 if surplus >= 15 else 0.25 if surplus >= 8 else 0.0
    label = "Merit scholarship" if pct else ""
    if state.get("scholarship") and level == "Bachelor's" and pct < 0.5:
        pct, label = 0.5, "Sports scholarship"
    sch = int(tuition * pct)
    wealth = state.get("family_wealth", "Comfortable")
    share = worldjobs.tier_value(wealth, FAMILY_SHARE) if state.get("parents_ok") else 0.0
    family = int((tuition - sch) * share)
    return {"tuition": tuition, "sch": sch, "sch_label": label, "family": family,
            "owe": tuition - sch - family, "wealth": wealth}

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
    "Psychology":       {"offset": 3},
    "Science":          {"offset": 8},
    "Architecture":     {"offset": 8},
    "Media & Film":     {"offset": -3},
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
    pygame.draw.rect(screen, OUTLINE, rect, 2, border_radius=8)
    text_colour = DARK_GREY if (disabled or done) else BLACK
    draw_text(screen, label, small_font, text_colour, rect.centerx, rect.centery, centre=True)

def draw_trades(screen, rect, mouse_pos, state, buttons):
    draw_text(screen, "Pick a trade (2 years, cheap fees, needs Academic 20+):", small_font, INK, rect.x, rect.y + 112)
    hits = []
    for n, name in enumerate(TRADES):
        r = pygame.Rect(rect.x + (n % 3) * 224, rect.y + 136 + (n // 3) * 40, 216, 34)
        ok = state["stats"]["academic"] >= 20
        draw_rounded_rect(screen, ACCENT if (ok and r.collidepoint(mouse_pos)) else (WHITE if ok else LIGHT_GREY), r, radius=8)
        pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
        draw_text(screen, name, small_font, INK, r.centerx, r.centery, centre=True)
        hits.append((name, r))
    buttons["trades"] = hits
    return buttons

def draw_funding(screen, rect, mouse_pos, state, career, buttons):
    pa = career["pending_apply"]
    plan = funding_plan(pa["level"], pa["college"], pa["course"], state)
    buttons.clear()
    what = pa["level"] + (f" in {pa['course']}" if pa["course"] else "")
    draw_text(screen, f"{what} at {pa['college']['name']}", font, INK, rect.x, rect.y)
    rows = [f"Tuition: ${fmt(plan['tuition'])} a year for {UNI_DURATION[pa['level']]} years",
            f"{plan['sch_label'] or 'Scholarship'}: ${fmt(plan['sch'])}" + ("" if plan["sch"] else "  (need a higher Academic score)"),
            f"Family contribution: ${fmt(plan['family'])}" + ("" if plan["family"] else
                "  (parents can't or don't cover fees)" if not state.get("parents_ok") or plan["wealth"] == "Struggling"
                else ""),
            f"Your family is {plan['wealth'].lower()}.",
            f"You pay: ${fmt(plan['owe'])} a year"]
    for i, t in enumerate(rows):
        draw_text(screen, t, small_font, BLACK if i == 4 else DARK_GREY, rect.x, rect.y + 32 + i * 22)
    y = rect.y + 160
    if plan["owe"] > 0:
        loan = pygame.Rect(rect.x, y, 210, 36)
        pay = pygame.Rect(rect.x + 220, y, 210, 36)
        draw_button(screen, loan, f"Student loan (+${fmt(plan['owe'])}/yr debt)", mouse_pos)
        draw_button(screen, pay, "Pay from savings", mouse_pos)
        buttons["fund_loan"], buttons["fund_pay"] = loan, pay
        draw_text(screen, f"You have ${fmt(state['money'])}. Loans grow by 5% a year and are repaid from your wages.",
                  small_font, DARK_GREY, rect.x, y + 46)
    else:
        ok = pygame.Rect(rect.x, y, 210, 36)
        draw_button(screen, ok, "Confirm (fully funded)", mouse_pos)
        buttons["fund_free"] = ok
    cancel = pygame.Rect(rect.right - 150, y, 150, 36)
    draw_button(screen, cancel, "Cancel", mouse_pos)
    buttons["fund_cancel"] = cancel
    return buttons

def draw_education_tab(screen, rect, mouse_pos, age, state, career):
    stats = state["stats"]
    academic = stats["academic"]
    actions_used = state["actions_used"]
    no_budget = state["actions_remaining"] <= 0
    scholarship = state.get("scholarship", False)

    if career.get("pending_apply") and age >= 18 and not career["enrolled"]:
        return draw_funding(screen, rect, mouse_pos, state, career, {})

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
        n = actions_used.get("__study__", 0)
        draw_button(screen, study_rect, "Study Harder" + (f" ({n})" if n else ""), mouse_pos, disabled=no_budget)
        draw_button(screen, dropout_rect, "Drop Out", mouse_pos, disabled=no_budget)
        fund = career.get("funding") or {}
        if fund:
            how = "student loan" if fund.get("mode") == "loan" else "savings"
            txt = (f"Tuition ${fmt(fund['tuition'])}/yr: family ${fmt(fund['family'])}, scholarship ${fmt(fund['sch'])}, "
                   f"you ${fmt(fund['owe'])} ({how}).")
            draw_text(screen, txt, small_font, DARK_GREY, rect.x, rect.y + 120)
        draw_text(screen, "Part-time and student jobs are in the Career tab.", small_font, DARK_GREY, rect.x, rect.y + 144)
        return {"study": study_rect, "dropout": dropout_rect}

    for i, line in enumerate(lines):
        draw_text(screen, line, small_font, DARK_GREY, rect.x, rect.y + i * 20)

    buttons = {}

    if age < 18:
        study_rect = pygame.Rect(rect.centerx - 230, rect.y + 60, 220, 36)
        n = actions_used.get("__study__", 0)
        draw_button(screen, study_rect, "Study" + (f" ({n})" if n else ""), mouse_pos, disabled=no_budget)
        buttons["study"] = study_rect
        if age >= 16 and career["education"] == "None":
            if career.get("pending_apply"):
                return draw_funding(screen, rect, mouse_pos, state, career, buttons)
            vr = pygame.Rect(rect.centerx + 10, rect.y + 60, 220, 36)
            draw_button(screen, vr, "Vocational training", mouse_pos, disabled=no_budget)
            buttons["voc_menu"] = vr
            if career.get("voc_open"):
                return draw_trades(screen, rect, mouse_pos, state, buttons)
        draw_text(screen, "Join clubs and sports from the Activities tab. From 18 you can apply to university.",
                  small_font, DARK_GREY, rect.x, rect.y + 112)
        return buttons

    next_level = NEXT_LEVEL[career["education"]]
    if next_level is None:
        draw_text(screen, "You've completed the highest level of education.",
                  small_font, DARK_GREY, rect.x, rect.y + 60)
        return buttons

    if career["education"] == "None" and not career.get("pending_course"):
        vr = pygame.Rect(rect.right - 190, rect.y + 20, 190, 26)
        draw_button(screen, vr, "Vocational instead" if not career.get("voc_open") else "University courses", mouse_pos)
        buttons["voc_menu"] = vr
        if career.get("voc_open"):
            return draw_trades(screen, rect, mouse_pos, state, buttons)
    if next_level == "Bachelor's" and not career.get("pending_course"):
        draw_text(screen, "Choose a course for your Bachelor's:", font, INK, rect.x, rect.y + 46)
        cols = 2
        col_w = (rect.width - 10) // cols
        hits = []
        for n, name in enumerate(COURSES):
            r = pygame.Rect(rect.x + (n % cols) * (col_w + 10), rect.y + 74 + (n // cols) * 38, col_w, 32)
            ok = course_open(name, stats, scholarship)
            hovered = r.collidepoint(mouse_pos) and ok
            draw_rounded_rect(screen, ACCENT if hovered else (WHITE if ok else LIGHT_GREY), r, radius=8)
            pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
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
    draw_text(screen, title, font, INK, rect.x, rect.y + 46)
    if next_level == "Bachelor's":
        change_rect = pygame.Rect(rect.right - 130, rect.y + 44, 130, 26)
        hovered = change_rect.collidepoint(mouse_pos)
        draw_rounded_rect(screen, ACCENT if hovered else WHITE, change_rect, radius=6)
        pygame.draw.rect(screen, OUTLINE, change_rect, 1, border_radius=6)
        draw_text(screen, "Change course", small_font, INK, change_rect.centerx, change_rect.centery, centre=True)
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
        pygame.draw.rect(screen, OUTLINE, row_rect, 1, border_radius=6)
        stars = "*" * college["prestige"]
        extra = " (scholarship)" if scholarship and next_level == "Bachelor's" and academic < college["required_academic"] + (COURSES.get(chosen_course, {"offset": 0})["offset"]) else ""
        draw_text(screen, f"{college['name']}  ({stars} prestige){extra}", small_font, INK,
                  row_rect.x + 10, row_rect.y + 8)
        apply_rect = pygame.Rect(row_rect.right - 90, row_rect.y + 4, 80, 26)
        hovered = apply_rect.collidepoint(mouse_pos)
        fill = LIGHT_GREY if no_budget else (ACCENT if hovered else LIGHT_GREY)
        draw_rounded_rect(screen, fill, apply_rect, radius=6)
        pygame.draw.rect(screen, OUTLINE, apply_rect, 1, border_radius=6)
        draw_text(screen, "Apply", small_font, INK, apply_rect.centerx, apply_rect.centery, centre=True)
        college_rects.append((college, apply_rect))
        y += 40

    buttons["colleges"] = college_rects
    buttons["next_level"] = next_level
    return buttons

def _start_course(state, career, mode):
    pa = career.pop("pending_apply")
    plan = funding_plan(pa["level"], pa["college"], pa["course"], state)
    if pa["level"] in ("Bachelor's", "Diploma"):
        career["course"] = pa["course"]
    career["pending_course"] = None
    career["voc_open"] = False
    career["enrolled"] = True
    career["uni_target"] = pa["level"]
    career["college_name"] = pa["college"]["name"]
    career["college_prestige"] = pa["college"]["prestige"]
    career["uni_years_done"] = 0
    career["job"] = None  # studying full-time
    career["funding"] = {"mode": mode, "tuition": plan["tuition"], "sch": plan["sch"],
                         "family": plan["family"], "owe": plan["owe"]}
    state["actions_remaining"] -= 1

def handle_education_click(mx, my, buttons, age, state, career):
    actions_used = state["actions_used"]
    stats = state["stats"]

    # funding screen
    if career.get("pending_apply"):
        if "fund_cancel" in buttons and buttons["fund_cancel"].collidepoint(mx, my):
            career.pop("pending_apply", None)
        elif state["actions_remaining"] > 0:
            for key, mode in (("fund_loan", "loan"), ("fund_pay", "savings"), ("fund_free", "savings")):
                if key in buttons and buttons[key].collidepoint(mx, my):
                    _start_course(state, career, mode)
                    return
        return

    if "voc_menu" in buttons and buttons["voc_menu"].collidepoint(mx, my):
        career["voc_open"] = not career.get("voc_open")
        return
    if "trades" in buttons:
        for name, r in buttons["trades"]:
            if r.collidepoint(mx, my) and stats["academic"] >= 20:
                career["pending_apply"] = {"level": "Diploma", "college": COLLEGES["Diploma"][0], "course": name}
        return

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

    def study(gain):
        n = actions_used.get("__study__", 0)
        stats["academic"] = max(0, min(100, stats["academic"] + max(1, gain - n)))
        stats["mental"] = max(0, min(100, stats["mental"] - (1 if career["enrolled"] else 0) + (0 if career["enrolled"] else 1 if n < 2 else 0)))
        actions_used["__study__"] = n + 1
        state["actions_remaining"] -= 1

    if career["enrolled"]:
        if buttons["study"].collidepoint(mx, my):
            study(3)
        elif buttons["dropout"].collidepoint(mx, my):
            career["enrolled"] = False
            career["uni_target"] = None
            career["uni_years_done"] = 0
            career["college_name"] = None
            career["funding"] = None
            state["actions_remaining"] -= 1
        return

    if age < 18:
        if "study" in buttons and buttons["study"].collidepoint(mx, my):
            study(4)
        return

    if "colleges" in buttons:
        for college, apply_rect in buttons["colleges"]:
            if apply_rect.collidepoint(mx, my):
                level = buttons["next_level"]
                career["pending_apply"] = {"level": level, "college": college,
                                           "course": career.get("pending_course") if level == "Bachelor's" else career.get("course")}
                return
