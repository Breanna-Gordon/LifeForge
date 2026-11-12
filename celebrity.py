"""Fame that runs in families: a famous parent, sibling or grandparent puts
your name in the papers before you've done anything. Their fame sets a floor
under yours, which fades slowly once they're gone.

state["kin_fame"] is that floor; state["famous_kin"] remembers who it's from.
"""
import random

# how famous each public job makes someone, before their personal star power
FAMOUS_JOBS = {"Royal Family Member": 75, "Actor": 62, "Singer": 62, "Footballer": 56, "Basketball Player": 56,
               "Film Director": 46, "Model": 46, "Politician": 42, "Boxer": 40, "Comedian": 40, "Influencer": 36,
               "Duke / Duchess": 30, "DJ": 26, "Musician": 16, "Writer": 12, "Journalist": 10}
SHOWBIZ = {"Actor", "Singer", "Film Director", "Model", "Comedian", "Influencer", "DJ", "Musician"}
_WEIGHT = {"Mother": 1.0, "Father": 1.0, "Sibling": 0.7}
FLOOR_CAP = 38          # family fame alone never makes you more than a rising star


def fame_of(p):
    base = FAMOUS_JOBS.get(p.get("job_title"), 0)
    if not base or p.get("age", 30) < 18:
        return 0
    if "star" not in p:
        p["star"] = _star_power(p["job_title"] == "Royal Family Member")
    return min(100, int(base * p["star"]))

def _star_power(big=False):
    """Most actors and singers are jobbing professionals; only a few are stars."""
    r = random.random()
    if big or r < 0.08:
        return round(random.uniform(0.9, 1.25), 2)
    return round(random.uniform(0.55, 0.85) if r < 0.3 else random.uniform(0.15, 0.45), 2)

def _weight(p):
    rel = p.get("relation", "")
    if rel.endswith(("Grandfather", "Grandmother")):
        return 0.5
    for k, w in _WEIGHT.items():
        if k in rel:
            return w
    return 0.3

def famous_relatives(people):
    """[(person, their fame)] for relatives in the public eye, most famous first."""
    out = [(p, fame_of(p)) for p in people if p.get("category") == "family" and not p.get("is_child")]
    return sorted([x for x in out if x[1] >= 30], key=lambda x: -x[1] * _weight(x[0]))

def _live_floor(people):
    kin = famous_relatives(people)
    if not kin:
        return 0, None
    p, f = kin[0]
    return min(FLOOR_CAP, int(f * _weight(p) * 0.5)), p

def seed(people):
    """Now and then an ordinary family has a retired star among the grandparents."""
    if famous_relatives(people) or random.random() > 0.06:
        return
    import worldjobs
    gps = [p for p in people if p.get("relation", "").endswith(("Grandfather", "Grandmother"))]
    if gps:
        gp = random.choice(gps)
        worldjobs.assign_job(gp, worldjobs.BY_TITLE[random.choice(["Actor", "Singer", "Footballer", "Model"])])
        gp["star"] = _star_power(True)

def setup(state, career, people, log):
    if state.get("scenario") in ("stars", "sport"):      # the scenario promises famous parents
        for p in people:
            if p.get("relation") in ("Mother", "Father"):
                p["star"] = _star_power(True)
    floor, who = _live_floor(people)
    state["kin_fame"] = floor
    if not who:
        return
    state["famous_kin"] = {"name": who["name"], "relation": who["relation"], "job": who["job_title"]}
    if who["job_title"] == "Royal Family Member":
        return          # royals get their own introduction
    career["fame"] = max(career.get("fame", 0), floor)
    log(f"Your {who['relation'].lower()}, {who['name']}, is a famous {who['job_title'].lower()}. "
        "Photographers were outside the hospital when you were born.")

def year(state, career, people):
    """Keep your fame from falling below the family name."""
    floor, who = _live_floor(people)
    state["kin_fame"] = max(floor, int(state.get("kin_fame", 0) * 0.92))
    if who:
        state["famous_kin"] = {"name": who["name"], "relation": who["relation"], "job": who["job_title"]}
    if state["kin_fame"] > career.get("fame", 0):
        career["fame"] = state["kin_fame"]

def floor(state):
    return state.get("kin_fame", 0)

def showbiz_family(state):
    k = state.get("famous_kin")
    return bool(k) and k["job"] in SHOWBIZ

def note(state):
    """One line for the Fame view, or None."""
    k, f = state.get("famous_kin"), floor(state)
    if not k or f < 3:
        return None
    return (f"Famous family: your {k['relation'].lower()} {k['name'].split()[0]} ({k['job'].lower()}) "
            f"keeps your name in the papers. Your fame won't drop below {f}.")
