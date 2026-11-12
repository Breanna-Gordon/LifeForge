"""Events that actually DO something, age-milestone events, and the autopilot
used when you skip years.

Old events only nudged stats, so "Change career" or "Accept the leadership
role" changed nothing real. An option can now carry an "act": a named effect
that really changes your job, pay, side job, education or money. The result
text is added to the option's "note" so the screen can say what happened."""
import random
from constants import fmt
import career as C

def _a(word):
    return ("an " if word[:1].lower() in "aeiou" else "a ") + word

def _job_line(j):
    return f"{j['title']} (${fmt(j['pay'])} a year)"

# ---------------------------------------------------------------- the effects
def _job(state):  return state["_career"]["job"]
def _career(state): return state["_career"]

def a_promote(state, arg=None):
    c, j = _career(state), _job(state)
    if not j:
        return "You have no job to be promoted in."
    if j.get("level", 0) >= C.MAX_LEVEL:
        j["pay"] = int(j["pay"] * 1.08)
        return f"You're already at the top, so they gave you a bonus raise. Pay is now ${fmt(j['pay'])}."
    old = j["title"]
    C._promote(j, state, "Promoted")
    return f"Promoted from {old} to {j['title']}. Pay is now ${fmt(j['pay'])} a year."

def a_promo_try(state, chance):
    j = _job(state)
    if not j:
        return "You have no job."
    if j.get("level", 0) >= C.MAX_LEVEL:
        return "There is nowhere higher to go in this company."
    chance = float(chance) + (j.get("perf", 55) - 55) / 200
    if random.random() < max(0.08, min(0.9, chance)):
        return a_promote(state)
    j["perf"] = max(0, j.get("perf", 55) - 3)
    return "You went for it but didn't get the role this time."

def a_raise(state, pct):
    j = _job(state)
    if not j:
        return "You have no job."
    j["pay"] = int(j["pay"] * (1 + float(pct)))
    return f"Your pay rose to ${fmt(j['pay'])} a year."

def a_raise_ask(state, arg=None):
    j = _job(state)
    if not j:
        return "You have no job."
    chance = 0.3 + j.get("perf", 55) / 200
    if random.random() < chance:
        j["pay"] = int(j["pay"] * 1.10)
        return f"They agreed. Pay is now ${fmt(j['pay'])} a year."
    j["perf"] = max(0, j.get("perf", 55) - 2)
    return "They said no this year. Nothing changed."

def a_perf(state, n):
    j = _job(state)
    if j:
        j["perf"] = max(0, min(100, j.get("perf", 55) + int(n)))
        return "Your boss noticed." if int(n) > 0 else "It didn't go down well at work."
    return ""

def a_overtime(state, arg=None):
    j = _job(state)
    if not j:
        return ""
    bonus = max(200, int(j["pay"] * 0.04))
    state["money"] += bonus
    j["perf"] = min(100, j.get("perf", 55) + 5)
    return f"The extra hours earned ${fmt(bonus)}."

def _offers(state, better):
    c = _career(state)
    ok, _ = C.eligible_jobs(c, state)
    if c["job"] and better:
        ok = [j for j in ok if j["pay"] > c["job"]["pay"] * 1.12]
    return ok

def a_job_offer(state, mode="better"):
    c = _career(state)
    if state.get("jail"):
        return "Not while you're in prison."
    ok = _offers(state, mode == "better")
    if not ok:
        if c["job"]:
            c["job"]["perf"] = min(100, c["job"].get("perf", 55) + 2)
            return "No better offer came of it, but your boss heard you were in demand."
        return "Nothing suitable came up. More qualifications would open doors."
    j = random.choice(ok[:4])
    if c["job"]:
        C.cv_save(state, c["job"])
    c["job"] = C._new_job(j, state)
    return f"You took the new job: {_job_line(c['job'])}."

def a_change_career(state, arg=None):
    c = _career(state)
    cur = c["job"].get("base") or c["job"]["title"] if c["job"] else None
    ok, _ = C.eligible_jobs(c, state)
    ok = [j for j in ok if j["title"] != cur and not j.get("fame")]
    if not ok:
        return "You looked around but found nothing you qualify for yet. Study something new first."
    j = random.choice(ok[:6])
    if c["job"]:
        C.cv_save(state, c["job"])
    c["job"] = C._new_job(j, state)
    state["stats"]["mental"] = min(100, state["stats"]["mental"] + 3)
    return f"You changed careers and became {_a(c['job']['title'])} on ${fmt(c['job']['pay'])} a year."

def a_side_job(state, arg=None):
    c = _career(state)
    ok = C.eligible_side_jobs(c, state)
    if not ok:
        return "Nothing suitable was going."
    j = random.choice(ok)
    c["side_job"] = dict(j)
    return f"You started a part-time job as a {j['title']} (${fmt(j['pay'])} a year)."

def a_edu_offer(state, arg=None):
    state["scholarship"] = True
    state["stats"]["academic"] = min(100, state["stats"]["academic"] + 2)
    return "They offered you a scholarship place. Apply in the Education tab to use it."

def a_layoff_check(state, arg=None):
    c, j = _career(state), _job(state)
    if not j:
        return ""
    if random.random() < max(0.1, 0.5 - j.get("perf", 55) / 200):
        sev = int(j["pay"] * 0.25)
        state["money"] += sev
        C.cv_save(state, j)
        c["job"] = None
        return f"You were laid off with ${fmt(sev)} severance. It's on your CV."
    return "Your job was safe in the end."

def a_redundancy(state, arg=None):
    c, j = _career(state), _job(state)
    if not j:
        return ""
    pay = int(j["pay"] * 0.9)
    state["money"] += pay
    C.cv_save(state, j)
    c["job"] = None
    return f"You took the payout of ${fmt(pay)} and left the job."

def a_retire(state, arg=None):
    c, j = _career(state), _job(state)
    if not j:
        state["pension"] = max(state.get("pension", 0), 9000)
        return "You settled into retirement."
    state["pension"] = max(state.get("pension", 0), j["pay"] // 2)
    C.cv_save(state, j)
    c["job"] = None
    c["side_job"] = None
    return f"You retired. Your pension is ${fmt(state['pension'])} a year."

def a_licence(state, arg=None):
    if random.random() < 0.65 + state["stats"]["mental"] / 400:
        state["license"] = True
        return "You passed your driving test first time."
    return "You failed the driving test. You can try again."

def a_skill(state, arg):
    k, n = arg
    sk = state.setdefault("skills", {})
    sk[k] = sk.get(k, 0) + n
    return f"Your {k} skill is now level {sk[k]}."

def a_exam(state, arg=None):
    a = state["stats"]["academic"]
    g = "top grades" if a >= 80 else "good grades" if a >= 65 else "average grades" if a >= 50 else "weak grades"
    state["_exam_grade"] = g
    return f"You got {g}."

def a_windfall(state, arg):
    lo, hi = arg
    amt = random.randint(lo, hi)
    state["money"] += amt
    return f"You received ${fmt(amt)}."

def a_title(state, kind):
    import titles
    ok = titles.grant(state, "knight" if kind == "knight" else "peer", 0, log=None)
    if not ok:
        return "You already hold a higher title."
    return f"You are now {titles.label(state)}."


def _kids(state, lo=0, hi=17):
    return [p for p in state.get("_people", []) if p.get("is_child") and lo <= p.get("age", 0) <= hi]

def a_kids_bond(state, n):
    ks = _kids(state)
    for k in ks:
        k["closeness"] = max(0, min(100, k["closeness"] + n))
        k["trust"] = max(0, min(100, k.get("trust", 50) + (1 if n > 0 else -1)))
        k["contacted"] = True
    if not ks:
        return ""
    k = ks[0]
    return (f"{k['name']} and you grew closer." if n > 0 else f"{k['name']} was hurt and went quiet.")

def a_rival_family(state, kind):
    fl = state.get("_friends")
    if fl is None:
        return ""
    import people as PP
    r = PP.make_person("Rival", "enemy", None, 8, age=random.randint(35, 70))
    r["conflict"] = 60
    pre = "Lord" if r["gender"] == "Male" else "Lady"
    first = r["name"].split()
    r["name"] = f"{pre} {first[-1]}"
    r["noble_rival"] = True
    fl.append(r)
    return f"{r['name']} and the whole family now see you as a rival."

def a_adopt_story(state, arg=None):
    import kids
    people = state.get("_people")
    if people is None:
        return ""
    if len(PPchildren(people)) >= __import__('people').MAX_CHILDREN:
        return "There was no room in the house for another child."
    age0 = random.choice([0, 0, 3, 3, 8, 14]) if arg is None else arg
    kids.add_child(state, people, state["stats"], state.get("_partner"), state.get("_skin", (234, 192, 134)), "adopted", age0,
                   log=lambda t: state["journal"].append((state["age"], t)))
    state["money"] = max(0, state["money"] - 500)
    return "The adoption was approved. A child has joined your family."

def PPchildren(people):
    return [p for p in people if p.get("is_child")]

ACTS = {"kids_bond": a_kids_bond, "rival_family": a_rival_family, "adopt_story": a_adopt_story, "title": a_title, "promote": a_promote, "promo_try": a_promo_try, "raise": a_raise, "raise_ask": a_raise_ask,
        "perf": a_perf, "overtime": a_overtime, "job_offer": a_job_offer, "change_career": a_change_career,
        "side_job": a_side_job, "edu_offer": a_edu_offer, "layoff_check": a_layoff_check,
        "redundancy": a_redundancy, "retire": a_retire, "licence": a_licence, "skill": a_skill,
        "exam": a_exam, "windfall": a_windfall}
DRASTIC = {"change_career", "redundancy", "retire", "layoff_check"}   # autopilot never picks these

def run_act(state, act):
    """act is "name" or ("name", arg). Returns text describing what happened."""
    name, arg = (act, None) if isinstance(act, str) else act
    fn = ACTS.get(name)
    if not fn or "_career" not in state:
        return ""
    try:
        return fn(state, arg)
    except Exception as e:      # never crash a life over an event
        return ""

# ----------------------------------------------------- patch the old events
def _set(pool, text, option, **fx):
    opt = pool.get(text, {}).get(option)
    if opt is not None:
        opt.update(fx)

def install(choice_events, situational):
    adult = choice_events["Adult"]["choices"]
    young = choice_events["Young Adult"]["choices"]
    teen = choice_events["Teenage"]["choices"]
    for pool in choice_events.values():
        ch = pool["choices"]
        _set(ch, "You are considering changing careers.", "Change career", act="change_career")
        _set(ch, "You are considering changing careers.", "Stay where you are", act=("perf", 3))
        _set(ch, "You're offered a leadership role at work.", "Accept", act=("promo_try", 0.8))
        _set(ch, "You're offered a leadership role at work.", "Decline", act=("perf", -2))
        _set(ch, "Your workplace offers overtime.", "Accept", act="overtime")
        _set(ch, "You are offered a weekend job.", "Take the job", act="side_job")
        _set(ch, "You receive an offer for further education.", "Accept", act="edu_offer")
    S = {e["text"]: e for e in situational}
    def so(text, option, **fx):
        if text in S and option in S[text]["options"]:
            S[text]["options"][option].update(fx)
    so("You're up for a pay rise.", "Ask for more", act="raise_ask")
    so("You're up for a pay rise.", "Accept the offer", act=("raise", 0.03))
    so("Your boss offers you a project nobody else wants.", "Take it on", act=("promo_try", 0.25))
    so("The company announces layoffs.", "Work extra hard", act=("perf", 6))
    so("The company announces layoffs.", "Update your CV quietly", act="layoff_check")
    so("A relative offers to help you find work.", "Accept the help", act=("job_offer", "any"))
    so("You spend weeks scrolling job listings.", "Apply everywhere", act=("job_offer", "any"))
    so("A coworker takes credit for your work.", "Speak up", act=("perf", 3))
    situational.extend(NEW_EVENTS)

def _has_job(c): return c["career"]["job"] is not None
def _since(n): return lambda c: c["career"]["job"] is not None and c["career"]["job"].get("since", 0) >= n
def _below_top(c): return c["career"]["job"] is not None and c["career"]["job"].get("level", 0) < C.MAX_LEVEL
def _good(c): return c["career"]["job"] is not None and c["career"]["job"].get("perf", 55) >= 60
def _no_job(c): return c["career"]["job"] is None and not c["career"]["enrolled"]
def _kid_age(lo, hi):
    return lambda c: any(p.get("is_child") and lo <= p.get("age", 0) <= hi for p in c["people"])
def _wealthy_or_known(c): return c["money"] >= 100000 or c["career"].get("fame", 0) >= 50 or bool(c.get("title"))
def _can_adopt(c):
    import people as PP
    return len(PP.children_of(c["people"])) < PP.MAX_CHILDREN
def _rich(c): return c["money"] >= 20000

def E(text, lo, hi, cond, options, exact=None):
    d = {"text": text, "min": lo, "max": hi, "cond": cond, "options": options}
    if exact is not None:
        d["exact"] = exact
    return d

NEW_EVENTS = [
    # ---- work that really changes things
    E("A recruiter has noticed your work.", 22, 62, _has_job,
      {"Take the interview": {"mental": 1, "act": ("job_offer", "better")},
       "Stay put": {"act": ("raise", 0.03), "mental": 1}}),
    E("You've been in the same role for a while.", 22, 62, _since(3),
      {"Ask about a promotion": {"act": ("promo_try", 0.5), "social": -1},
       "Quietly update your CV": {"act": ("job_offer", "better")},
       "Enjoy the stability": {"mental": 2}}),
    E("Your manager is leaving and the role is open.", 24, 62, lambda c: _below_top(c) and _since(1)(c),
      {"Apply for it": {"mental": -1, "act": ("promo_try", 0.55)},
       "Stay in your role": {"mental": 1}}),
    E("Your company offers voluntary redundancy.", 45, 64, _has_job,
      {"Take the payout": {"act": "redundancy", "mental": 1},
       "Decline": {"act": ("perf", 3)}}),
    E("You're headhunted for a bigger job in another city.", 26, 55, lambda c: _good(c),
      {"Accept the move": {"act": ("job_offer", "better"), "social": -2, "mental": -1},
       "Stay where you are": {"social": 1}}),
    E("A friend says their company is hiring.", 18, 62, _no_job,
      {"Apply": {"act": ("job_offer", "any"), "mental": 1}, "Not interested": {"mental": 0}}),
    E("You're burnt out and thinking of retiring early.", 55, 66, _has_job,
      {"Retire now": {"act": "retire", "mental": 4}, "Keep going": {"mental": -1, "money": 20}}),
    E("The honours list arrives, and your name is on it.", 40, 95,
      lambda c: (c["career"].get("fame", 0) >= 35 or c["money"] >= 400000) and (not c.get("title")),
      {"Accept the knighthood": {"act": ("title", "knight"), "mental": 3, "social": 2}, "Decline humbly": {"mental": 1}}),
    E("You are offered a peerage for your services.", 50, 95,
      lambda c: (c["career"].get("fame", 0) >= 60 or c["money"] >= 3000000) and (not c.get("title") or c["title"]["kind"] == "knight"),
      {"Accept the title": {"act": ("title", "peer"), "mental": 3, "social": 3}, "Decline": {"mental": 1}}),
    E("You see a job advert for something completely different.", 24, 58, _has_job,
      {"Apply": {"act": "change_career", "mental": 1}, "Close the tab": {"mental": 0}}),
    # ---- children
    E("Your child's teacher asks to see you after school.", 22, 70, _kid_age(5, 17),
      {"Talk it through calmly": {"act": ("kids_bond", 4), "mental": -1},
       "Ground them": {"act": ("kids_bond", -3), "mental": -1},
       "Say it's the teacher's fault": {"act": ("kids_bond", 2), "social": -1}}),
    E("Your toddler says their first proper sentence.", 20, 60, _kid_age(1, 3),
      {"Write it in the journal": {"act": ("kids_bond", 3), "mental": 2}, "Film it for the family": {"act": ("kids_bond", 2), "social": 1}}),
    E("Your child wants to join a club but it costs money.", 22, 70, _kid_age(6, 16),
      {"Pay for it": {"act": ("kids_bond", 4), "money": -40}, "Say not this year": {"act": ("kids_bond", -2)}}),
    E("Your child wins a prize at school.", 24, 70, _kid_age(6, 17),
      {"Throw a small party": {"act": ("kids_bond", 5), "money": -20, "mental": 2}, "Tell them well done": {"act": ("kids_bond", 2)}}),
    E("Your teenager wants to stay out late with friends.", 30, 70, _kid_age(14, 17),
      {"Let them go": {"act": ("kids_bond", 3), "mental": -1}, "Set a strict curfew": {"act": ("kids_bond", -2), "mental": 1}}),
    E("Your child is being bullied and hasn't told anyone.", 24, 70, _kid_age(7, 16),
      {"Notice the signs and talk": {"act": ("kids_bond", 6), "mental": -1}, "Miss it entirely": {"act": ("kids_bond", -5)}}),
    # ---- rival titled family
    E("A titled family sneers at your new money at a charity dinner.", 25, 85, _wealthy_or_known,
      {"Befriend them anyway": {"social": 3, "mental": -1}, "Snub them back": {"act": ("rival_family", 0), "social": 1},
       "Outbid them at the auction": {"act": ("rival_family", 0), "money": -150, "social": 3}}),
    E("A noble family disputes your place at a society event.", 30, 90, lambda c: bool(c.get("title")),
      {"Hold your ground": {"act": ("rival_family", 0), "social": 2}, "Yield with grace": {"social": 1, "mental": -1}}),
    # ---- dating and adoption story
    E("After a long dinner, your partner admits they have always wanted to adopt.", 24, 68, lambda c: c["partner"] is not None and _can_adopt(c),
      {"Start the adoption process": {"act": "adopt_story", "mental": 3}, "Try for a baby instead": {"mental": 1},
       "Not right now": {"mental": 0}}),
    E("A charity worker tells you about a child who needs a loving home.", 24, 85, lambda c: _can_adopt(c) and c["money"] >= 3000,
      {"Offer to adopt": {"act": "adopt_story", "mental": 3, "money": -40}, "Donate instead": {"money": -30, "social": 2}}),
    E("Your date asks if you want children one day.", 20, 50, lambda c: c["partner"] is not None and not c["partner"].get("married"),
      {"Say yes, maybe adopt too": {"mental": 2, "social": 1}, "Say you're not sure": {"mental": 0}}),
]

# -------------------------------------------------------- age milestones
# "exact" events show up in that very year (they get priority over normal ones).
AGE_EVENTS = [
    E("It's your first day at school.", 5, 5, lambda c: True,
      {"Walk in bravely": {"social": 3, "mental": 1}, "Cling to your parent": {"mental": 1, "social": -1}}, exact=5),
    E("You'd love to learn an instrument.", 8, 8, lambda c: True,
      {"Ask for lessons": {"mental": 2, "act": ("skill", ("music", 1)), "money": -10}, "Just listen to music": {"mental": 1}}, exact=8),
    E("You start secondary school.", 11, 11, lambda c: True,
      {"Make new friends": {"social": 3, "mental": -1}, "Keep your head down": {"academic": 2, "social": -1}}, exact=11),
    E("You get your first phone.", 12, 12, lambda c: True,
      {"Use it sensibly": {"mental": 1, "social": 1}, "Live on it": {"social": 2, "mental": -2, "academic": -2}}, exact=12),
    E("You start feeling your first real crush.", 13, 13, lambda c: True,
      {"Tell them": {"social": 2, "mental": -1}, "Keep it secret": {"mental": 1}}, exact=13),
    E("Time to choose your exam subjects.", 14, 14, lambda c: True,
      {"Sciences and maths": {"academic": 4}, "Arts and languages": {"academic": 2, "mental": 2, "act": ("skill", ("languages", 1))},
       "Practical subjects": {"academic": 1, "athletic": 2}}, exact=14),
    E("Your exam results come in.", 16, 16, lambda c: True,
      {"Open the envelope": {"act": "exam", "mental": 1}, "Let a friend open it": {"act": "exam", "social": 1}}, exact=16),
    E("You're old enough to learn to drive.", 17, 17, lambda c: True,
      {"Book lessons": {"money": -25, "act": "licence"}, "Not yet": {"mental": 0}}, exact=17),
    E("It's your 18th birthday.", 18, 18, lambda c: True,
      {"Throw a big party": {"social": 4, "mental": 2, "money": -30}, "Quiet dinner with family": {"mental": 3, "social": 1}}, exact=18),
    E("It's your 21st birthday.", 21, 21, lambda c: True,
      {"Celebrate with everyone": {"social": 4, "mental": 2, "money": -35}, "Keep it small": {"mental": 2}}, exact=21),
    E("You turn 25 and wonder where your life is going.", 25, 25, lambda c: True,
      {"Set new goals": {"mental": 3, "academic": 1}, "Ignore the feeling": {"mental": -1}}, exact=25),
    E("You turn 30.", 30, 30, lambda c: True,
      {"Throw a party": {"social": 3, "mental": 2, "money": -30}, "Reflect quietly": {"mental": 2, "wealth": 1}}, exact=30),
    E("You hit 40 and take stock of your life.", 40, 40, _has_job,
      {"Chase a big change": {"act": "change_career", "mental": 1}, "Book a health check": {"physical": 4, "money": -15},
       "Carry on as you are": {"mental": 1}}, exact=40),
    E("You hit 40 and take stock of your life.", 40, 40, lambda c: not _has_job(c),
      {"Make a fresh start": {"act": ("job_offer", "any"), "mental": 2}, "Book a health check": {"physical": 4, "money": -15}}, exact=40),
    E("Your body is starting to complain.", 50, 50, lambda c: True,
      {"Take up gentle exercise": {"physical": 5, "athletic": 1}, "Put up with it": {"physical": -2}}, exact=50),
    E("You think about retirement.", 60, 60, _has_job,
      {"Retire now": {"act": "retire", "mental": 3}, "Work a few more years": {"money": 25, "mental": -1}}, exact=60),
    E("It's time to write your will.", 70, 70, lambda c: True,
      {"Do it properly": {"mental": 2, "wealth": 1, "money": -10}, "Leave it for later": {"mental": 0}}, exact=70),
]

def age_event(age, ctx):
    """The milestone event for exactly this age, if one fits."""
    fits = [e for e in AGE_EVENTS if e["exact"] == age and e["cond"](ctx)]
    return random.choice(fits) if fits else None

# ---------------------------------------------------------------- autopilot
def option_score(opt):
    s = 0.0
    for k, v in opt.items():
        if k in ("act", "note", "person", "gamble", "new_enemy", "new_friend", "covered"):
            continue
        s += v / 50 if k == "money" else v
    return s

def autopilot_pick(data):
    """Pick the option a sensible player would: avoids drastic life changes."""
    def drastic(o):
        a = o.get("act")
        if not a:
            return False
        if not isinstance(a, str) and a[0] == "royal":
            return (a[1] or {}).get("do") in ("step_back", "abdicate", "sell_land")
        return (a if isinstance(a, str) else a[0]) in DRASTIC
    names = [n for n, o in data.items() if not drastic(o)]
    names = names or list(data.keys())
    scored = sorted(names, key=lambda n: -option_score(data[n]) + random.random() * 2.5)
    return scored[0]


def _auto_enrol(state, career, log):
    """Skipping with strong grades: apply for university (or the next degree) like a sensible player would."""
    import education as ED
    stats = state["stats"]
    age = state["age"]
    level = ED.NEXT_LEVEL.get(career["education"])
    if not level or career["enrolled"] or state.get("jail") or age < 18 or age > 40:
        return
    need = {"Bachelor's": 66, "Master's": 74, "PhD": 82}[level]
    if stats["academic"] < need:
        return
    if level != "Bachelor's" and (age > 32 or random.random() > 0.45):
        return
    course = None
    if level == "Bachelor's":
        if career.get("pending_course") and ED.course_open(career["pending_course"], stats, state.get("scholarship")):
            course = career["pending_course"]
        else:
            open_c = [c for c in ED.COURSES if ED.course_open(c, stats, state.get("scholarship"))]
            if not open_c:
                return
            course = random.choice(sorted(open_c, key=lambda c: -ED.COURSES[c]["offset"])[:5])
    opts = ED.eligible_colleges(level, stats["academic"], course, state.get("scholarship"))
    if not opts:
        return
    college = max(opts, key=lambda c: c["prestige"])
    plan = ED.funding_plan(level, college, course, state)
    mode = "loan" if plan["owe"] > state["money"] * 0.5 else "pay"
    career.update({"enrolled": True, "uni_target": level, "college_name": college["name"],
                   "college_prestige": college["prestige"], "uni_years_done": 0, "job": None, "pending_course": None,
                   "funding": {"mode": mode, "tuition": plan["tuition"], "sch": plan["sch"],
                               "family": plan["family"], "owe": plan["owe"]}})
    if level == "Bachelor's":
        career["course"] = course
    log(f"You got into {college['name']} to study a {level}" + (f" in {course}." if course else "."))

def autopilot_year(state, career, people, friends, partner, log):
    """What a sensible player would do with a normal year of actions. Runs
    for each skipped year so skipping never means standing still."""
    stats = state["stats"]
    age = state["age"]
    job = career["job"]
    if job:
        job["perf"] = min(100, job.get("perf", 55) + 4)
        stats["social"] = min(100, stats["social"] + 1)
        if C.can_promote(job) and job.get("perf", 0) >= 62 and random.random() < 0.35:
            C._promote(job, state, "Promoted")
    if career["enrolled"]:
        stats["academic"] = min(100, stats["academic"] + 3)
    elif age < 18:
        stats["academic"] = min(100, stats["academic"] + 2)
    if age < 55:
        stats["physical"] = min(100, stats["physical"] + 1)
    kin = sorted([p for p in people + friends + ([partner] if partner else []) if p.get("category") != "enemy"],
                 key=lambda p: -p["closeness"])[:5]
    for p in kin:
        p["closeness"] = min(100, p["closeness"] + 3)
        p["trust"] = min(100, p["trust"] + 1)
        p["contacted"] = True
    if not career["enrolled"] and not job:
        _auto_enrol(state, career, log)
    if (age >= 18 and not job and not career["enrolled"] and not state.get("jail")
            and age < 66 and random.random() < 0.7):
        ok, _ = C.eligible_jobs(career, state)
        if ok:
            j = ok[0] if random.random() < 0.4 else random.choice(ok[:5])
            career["job"] = C._new_job(j, state)
            log(f"You found work as a {career['job']['title']} (${fmt(career['job']['pay'])} a year).")
