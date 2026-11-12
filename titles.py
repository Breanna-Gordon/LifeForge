import random

PLACES = ["Ashford", "Bramwell", "Carrow", "Dunmere", "Elmsworth", "Fairhaven", "Greystone", "Harrowgate",
          "Kingsbury", "Larkfield", "Marlow", "Northcliff", "Oakridge", "Ravensmoor", "Stanbrook", "Westmere"]

# higher number outranks lower
ORDER = {"knight": 1, "peer": 2, "prince": 3, "king": 4}

PEER_RANKS = [("Baron", "Baroness"), ("Viscount", "Viscountess"), ("Earl", "Countess"), ("Duke", "Duchess")]

# yearly income from estates / the crown
INCOME = {"knight": 0, "peer": 40000, "prince": 150000, "king": 500000}


def _female(state, gender=None):
    return (gender or state.get("gender")) == "Female"


def _score(t):
    if not t:
        return 0
    return ORDER.get(t["kind"], 0) * 10 + t.get("rank", 0)


def grant(state, kind, rank=0, log=None, place=None):
    new = {"kind": kind}
    if kind == "peer":
        new["rank"] = max(0, min(rank, len(PEER_RANKS) - 1))
        new["place"] = place or random.choice(PLACES)
    if _score(state.get("title")) >= _score(new):
        return False
    state["title"] = new
    if log:
        log(f"You are now {label(state)}.")
    return True


def label(state, gender=None):
    t = state.get("title")
    if not t:
        return ""
    f = _female(state, gender)
    kind = t["kind"]
    if kind == "knight":
        return "a Dame" if f else "a Knight"
    if kind == "peer":
        return f"{PEER_RANKS[t.get('rank', 0)][1 if f else 0]} of {t.get('place', 'Ashford')}"
    if kind == "prince":
        return "Princess" if f else "Prince"
    if kind == "king":
        return "Queen" if f else "King"
    return kind.title()


def styled_name(state, name, gender=None):
    t = state.get("title")
    if not t:
        return name
    f = _female(state, gender)
    prefix = {"knight": "Dame" if f else "Sir", "peer": "Lady" if f else "Lord",
              "prince": "Princess" if f else "Prince", "king": "Queen" if f else "King"}.get(t["kind"])
    return f"{prefix} {name}" if prefix else name


def pass_on(title, heir_kind):
    # knighthoods die with you; hereditary titles go to blood relatives only
    if not title or title["kind"] == "knight":
        return None
    if heir_kind not in ("Child", "Grandchild"):
        return None
    return dict(title)


def check_succession(state, people, log):
    heir = state.get("heir_to")
    if not heir:
        return
    if any(p["name"] == heir["holder_name"] for p in people):
        return
    state.pop("heir_to")
    if heir["kind"] == "king":
        if grant(state, "king"):
            log("The crown has passed to you.")
            log(f"You are now {label(state)}.")
    elif grant(state, "peer", heir.get("rank", 0), place=heir.get("place")):
        log(f"You inherited the family title. You are now {label(state)}.")


def year(state, career, log):
    t = state.get("title")
    if not t or state.get("age", 0) < 18:
        return
    income = INCOME.get(t["kind"], 0)
    if t["kind"] == "peer":
        income = int(income * (1 + t.get("rank", 0) * 0.5))
    import station
    income = int(income * station.income_factor(state))
    if income:
        state["money"] += income
        if random.random() < 0.15:
            log(f"Your {'royal stipend' if t['kind'] in ('king', 'prince') else 'estates'} brought in ${income:,} this year.")
