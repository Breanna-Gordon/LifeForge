"""Sports careers: school and college teams, the draft, pro teams.

School and college play comes from the clubs and teams you join. From 20
you can enter the draft (if you're good enough) and sign with a pro team.
A pro contract is your job: it pays each year, performance matters, you
can be traded, get injured and eventually retire."""
import random
import pygame
from constants import fmt, OUTLINE, INK, MUTED
from constants import (WHITE, LIGHT_GREY, DARK_GREY, ACCENT, GREEN, RED,
                       font, small_font, draw_text, draw_rounded_rect)

SPORT_IDS = {"football": "Football", "basket": "Basketball", "rugby": "Rugby", "track": "Athletics", "swim": "Swimming"}
PRO_TITLE = {"football": "Footballer", "basket": "Basketball Player", "rugby": "Rugby Player", "track": "Track Athlete", "swim": "Swimmer"}
# (team name, tier) tier 1 = the best team in the league
TEAMS = {
    "football": [("Capital City FC", 1), ("Northern Rovers", 1), ("Harbour United", 2), ("Valley Wanderers", 2), ("Redstone Athletic", 3), ("Lakeside Town", 3), ("Moorland FC", 4), ("Fenwick Albion", 4)],
    "basket":   [("Metro Kings", 1), ("Bay Sharks", 1), ("Summit Peaks", 2), ("River City Flyers", 2), ("Desert Suns", 3), ("Prairie Wolves", 3), ("Harbor Gulls", 4), ("Iron Hawks", 4)],
    "rugby":    [("Crown Lions", 1), ("Border Reivers", 1), ("Castle Bears", 2), ("Hill Stags", 2), ("Marsh Otters", 3), ("Quarry Giants", 3), ("Dockside RFC", 4), ("Vale Warriors", 4)],
    "track":    [("National Squad", 1), ("Metro Club", 2), ("City Harriers", 3), ("County Runners", 4)],
    "swim":     [("National Squad", 1), ("Aqua Elite", 2), ("City Dolphins", 3), ("County Swim Club", 4)],
}
TIER_PAY = {1: 900000, 2: 380000, 3: 140000, 4: 55000}

def my_sport(state):
    from activities import BY_ID
    for aid in state.get("activities", {}):
        a = BY_ID.get(aid)
        if a and a["kind"] == "sport" and aid in SPORT_IDS:
            return aid
    return None

def level_of(state, career):
    pro = state.get("pro")
    if pro:
        return "pro"
    if my_sport(state):
        return "college" if career.get("enrolled") else "school"
    return None

def draft_score(state, career):
    s = state["stats"]
    return s["athletic"] * 0.65 + s["physical"] * 0.15 + career.get("fame", 0) * 0.2 + state.get("sport_perf", 50) * 0.2 + random.randint(-10, 10)

def _contract(tier, state):
    base = TIER_PAY[tier]
    return int(base * (0.8 + state["stats"]["athletic"] / 250) / 1000) * 1000

def sign_pro(state, career, sid, team, tier, log):
    import career as C
    pay = _contract(tier, state)
    job = {"title": PRO_TITLE[sid], "base": "Professional Athlete", "min_age": 18, "pay": pay, "wealth": 12,
           "fame": True, "stats": {}, "skills": {}, "courses": None, "any_of": None, "min_education": "None", "min_prestige": 0}
    if career.get("job"):
        C.cv_save(state, career["job"])
    career["job"] = C._new_job(job, None)
    career["job"]["base"] = "Professional Athlete"
    career["job"]["title"] = PRO_TITLE[sid]
    state["pro"] = {"sport": sid, "team": team, "tier": tier, "years": 0}
    career["fame"] = min(100, career.get("fame", 0) + (12 if tier == 1 else 6))
    log(f"Signed with {team} for ${fmt(pay)} a year.")

def view_buttons(rect, n):
    return [pygame.Rect(rect.x + (i % 2) * 337, rect.y + 120 + (i // 2) * 44, 330, 38) for i in range(n)]

def _options(state, age, career):
    """(key, label, subtitle, enabled)"""
    sid = my_sport(state)
    pro = state.get("pro")
    out = []
    left = state["actions_remaining"] > 0
    if pro:
        out.append(("train", "Train with the squad", "Athletic up, performance up", left))
        out.append(("showcase", "Play a showcase match", "Fame and form", left))
        out.append(("trade", "Ask for a trade", "Change team (may raise pay)", left))
        out.append(("retire", "Retire from sport", "Leave the sport for good", True))
        return out
    if not sid:
        out.append(("info", "Join a team in Clubs first", "Football, Basketball, Rugby, Athletics or Swimming", False))
        return out
    out.append(("train", "Extra training", "Athletic +, performance +", left))
    if age >= 20:
        ok = left and state["stats"]["athletic"] >= 60
        out.append(("draft", "Enter the draft", "Needs Athletic 60+. Teams pick the best", ok))
        out.append(("trial", "Pro trial", "Try out for a lower-league team", left and state["stats"]["athletic"] >= 50))
    else:
        out.append(("scout", "Attend a scouting camp", "Scouts notice you (fame)", left and age >= 15))
    return out

def draw_sports(screen, rect, mouse_pos, state, age, career):
    sid = my_sport(state)
    pro = state.get("pro")
    lvl = level_of(state, career)
    perf = state.get("sport_perf", 50)
    draw_text(screen, "Sports", font, INK, rect.x, rect.y)
    if pro:
        t = f"{PRO_TITLE[pro['sport']]} at {pro['team']}  ·  {pro['years']} seasons  ·  ${fmt(career['job']['pay']) if career.get('job') else 0}/yr"
    elif sid:
        t = f"{SPORT_IDS[sid]} {'college' if lvl == 'college' else 'school'} team  ·  form {perf}"
    else:
        t = "You're not on a team yet."
    draw_text(screen, t, small_font, DARK_GREY, rect.x, rect.y + 28)
    bar = pygame.Rect(rect.x, rect.y + 52, 260, 10)
    draw_rounded_rect(screen, LIGHT_GREY, bar, radius=5)
    draw_rounded_rect(screen, (80, 190, 210), (bar.x, bar.y, int(bar.w * perf / 100), bar.h), radius=5)
    draw_text(screen, "Form", small_font, MUTED, bar.right + 8, bar.y - 4)
    hint = {"pro": "Good form means pay rises and fame. Injuries and age end careers.",
            "college": "Strong college players get drafted at 20+. Form matters.",
            "school": "Join a team in Clubs, train, and the scouts will come.",
            None: "Teams are in the Clubs view."}[lvl]
    draw_text(screen, hint, small_font, MUTED, rect.x, rect.y + 70)
    if sid:
        draw_text(screen, "Teams in your league: " + ", ".join(n for n, tr in TEAMS[pro["sport"] if pro else sid][:4]) + "...",
                  small_font, MUTED, rect.x, rect.y + 90)
    hits = []
    for (key, label, sub, en), r in zip(_options(state, age, career), view_buttons(rect, 8)):
        hov = en and r.collidepoint(mouse_pos)
        draw_rounded_rect(screen, ACCENT if hov else (WHITE if en else LIGHT_GREY), r, radius=8)
        pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
        draw_text(screen, label, small_font, INK, r.x + 10, r.y + 3)
        draw_text(screen, sub, small_font, DARK_GREY, r.x + 10, r.y + 20)
        hits.append((key, r, en))
    return {"sports": hits}

def handle_sports_click(mx, my, buttons, state, age, career, log):
    stats = state["stats"]
    for key, r, en in buttons.get("sports", []):
        if not (r.collidepoint(mx, my) and en):
            continue
        sid = state["pro"]["sport"] if state.get("pro") else my_sport(state)
        if key == "retire":
            log(f"You retired from {SPORT_IDS[sid]}.")
            if career.get("job") and career["job"].get("base") == "Professional Athlete":
                career["job"] = None
            state["pro"] = None
            return
        state["actions_remaining"] -= 1
        perf = state.get("sport_perf", 50)
        if key == "train":
            stats["athletic"] = min(100, stats["athletic"] + random.randint(1, 3))
            stats["physical"] = max(0, stats["physical"] - 1)
            state["sport_perf"] = min(100, perf + random.randint(2, 6))
            log("A tough training block. You feel sharper.")
        elif key == "showcase":
            state["sport_perf"] = min(100, perf + random.randint(-3, 8))
            career["fame"] = min(100, career.get("fame", 0) + 1)
            log("A big match. The crowd noticed.")
        elif key == "scout":
            career["fame"] = min(100, career.get("fame", 0) + 1)
            state["sport_perf"] = min(100, perf + 3)
            log("Scouts watched you at camp.")
        elif key == "draft":
            sc = draft_score(state, career)
            teams = TEAMS[sid]
            if sc >= 84:
                tier, rnd = 1, "first-round pick"
            elif sc >= 72:
                tier, rnd = 2, "second-round pick"
            elif sc >= 60:
                tier, rnd = 3, "late pick"
            else:
                log("Nobody picked you in the draft this year.")
                return
            team = random.choice([n for n, t in teams if t == tier])
            log(f"Drafted as a {rnd} by {team}!")
            sign_pro(state, career, sid, team, tier, log)
        elif key == "trial":
            tier = 4 if state["stats"]["athletic"] < 70 else 3
            if random.random() < 0.35 + (stats["athletic"] - 50) / 100:
                team = random.choice([n for n, t in TEAMS[sid] if t == tier])
                sign_pro(state, career, sid, team, tier, log)
            else:
                log("The pro trial didn't lead to a contract.")
        elif key == "trade":
            pro = state["pro"]
            better = [(n, t) for n, t in TEAMS[pro["sport"]] if t < pro["tier"]]
            pool = better if (better and state.get("sport_perf", 50) >= 65 and random.random() < 0.6) else [(n, t) for n, t in TEAMS[pro["sport"]] if n != pro["team"]]
            n, t = random.choice(pool)
            pro["team"], pro["tier"] = n, t
            new_pay = _contract(t, state)
            if career.get("job"):
                career["job"]["pay"] = max(career["job"]["pay"] // 2, new_pay if t < pro["tier"] or new_pay > career["job"]["pay"] else career["job"]["pay"])
            log(f"You were traded to {n}.")
        return

def sports_year(state, career, log):
    """Season results, injuries, contracts and retirement for pro players."""
    pro = state.get("pro")
    if state.get("pro") and not (career.get("job") and career["job"].get("base") == "Professional Athlete"):
        state["pro"] = None    # lost the job some other way
        return
    stats = state["stats"]
    perf = state.get("sport_perf", 50)
    if pro:
        pro["years"] += 1
        perf = max(0, min(100, perf + random.randint(-12, 10) + (stats["athletic"] - 60) // 10))
        state["sport_perf"] = perf
        job = career["job"]
        if perf >= 75:
            job["pay"] = int(job["pay"] * 1.12)
            career["fame"] = min(100, career.get("fame", 0) + 2)
            log(f"A great season with {pro['team']}. Your contract improved to ${fmt(job['pay'])}.")
        elif perf < 30:
            log(f"A poor season with {pro['team']}. The fans are restless.")
        if random.random() < 0.08 + (0.04 if stats["physical"] < 40 else 0):
            stats["physical"] = max(0, stats["physical"] - random.randint(6, 14))
            stats["athletic"] = max(0, stats["athletic"] - random.randint(3, 8))
            log("A serious injury cost you months of the season.")
        if state["age"] >= 34 and random.random() < 0.25 + (state["age"] - 34) * 0.1:
            log(f"You retired from {SPORT_IDS[pro['sport']]} after {pro['years']} seasons.")
            career["job"] = None
            state["pro"] = None
    else:
        state["sport_perf"] = max(0, min(100, perf + random.randint(-4, 5)))
