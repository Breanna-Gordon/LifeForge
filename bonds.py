"""Relationship storylines: falling out and making up, rivals offering peace,
best friends, sibling rivalry, parents growing old, in-laws and reunions."""
import random
from stories import S, with_

def _first(p):
    return p["name"].split()[0]

def _drop_friend(friends, p):
    def fn(state):
        if p in friends:
            friends.remove(p)
        return f"You and {_first(p)} went your separate ways."
    return fn

def _make_peace(p):
    def fn(state):
        p["category"], p["relation"] = "friend", "Friend"
        p["closeness"], p["conflict"] = 45, 0
        return f"You and {_first(p)} are on good terms now."
    return fn

def _bestie(p):
    def fn(state):
        p["best"] = True
        p["relation"] = "Best Friend"
        p["closeness"] = min(100, p["closeness"] + 5)
        return f"{_first(p)} is officially your best friend."
    return fn

def _care(p, how):
    def fn(state):
        p["care"] = how
        if how == "home":
            return f"{_first(p)} moved in with you."
        return f"{_first(p)} moved into a care home."
    return fn

def _reunion(friends, age):
    def fn(state):
        if random.random() < 0.5 and len(friends) < 12:
            from people import make_person
            old = make_person("Friend", "friend", None, 50, age=age)
            friends.append(old)
            return f"You reconnected with {old['name']}, an old classmate."
        return "It was strange and lovely to see everyone again."
    return fn

def beats(state, ctx, age):
    people, friends, partner = ctx.get("people", []), ctx.get("friends", []), ctx.get("partner")
    out = []
    pals = [f for f in friends if f.get("category") == "friend"]
    for f in pals:
        n = _first(f)
        if age >= 10 and (f.get("conflict", 0) >= 40 or (f.get("closeness", 50) < 22 and not f.get("best"))):
            out.append((f"fallout:{f['name']}", f"{n} has gone cold on you since your last argument.",
                        {"Apologise first": with_({"person": (f, {"closeness": 15, "conflict": -30})}, mental=1),
                         "Give it time": {"gamble": [{"person": (f, {"closeness": 8, "conflict": -20})}, {"person": (f, {"closeness": -10})}]},
                         "Let the friendship go": S(fn=_drop_friend(friends, f))}))
            break
    for f in pals:
        if f.get("closeness", 0) >= 85 and not f.get("best") and age >= 8 and not any(x.get("best") for x in pals):
            out.append((f"bestie:{f['name']}", f"{_first(f)} says you're their best friend.",
                        {"Say it back": S(fn=_bestie(f)), "Laugh it off": {"person": (f, {"closeness": -5})}}))
            break
    best = next((f for f in pals if f.get("best")), None)
    if best and 18 <= age <= 32:
        out.append((f"roadtrip:{best['name']}", f"{_first(best)} wants to take a road trip together this summer.",
                    {"Pack the car": with_(S(cash=-1500), mental=4, social=2, person=(best, {"closeness": 8})),
                     "You can't get away": {"person": (best, {"closeness": -4})}}))
    if best and 25 <= age <= 42:
        role = "best man" if best.get("gender") == "Male" else "maid of honour"
        out.append((f"bestwed:{best['name']}", f"{_first(best)} is getting married and asks you to be {role}.",
                    {"Say yes and write a speech": {"gamble": [with_({"person": (best, {"closeness": 10})}, social=3, mental=2),
                                                               with_({"person": (best, {"closeness": 4})}, mental=-2)]},
                     "Say you're too busy": {"person": (best, {"closeness": -15})}}))
    for f in friends:
        if f.get("category") == "enemy" and f.get("conflict", 50) < 30 and age >= 16:
            out.append((f"peace:{f['name']}", f"Your old rival {_first(f)} reaches out to bury the hatchet.",
                        {"Accept": with_(S(fn=_make_peace(f)), mental=2), "Refuse": {"social": -1}}))
            break
    for s in people:
        if "Sibling" in s.get("relation", "") and abs(s.get("age", 0) - age) <= 4 and 10 <= age <= 18:
            out.append((f"sibrival:{s['name']}", f"Your parents keep comparing you to {_first(s)}.",
                        {"Try harder at school": {"academic": 2, "mental": -2},
                         f"Talk it out with {_first(s)}": {"person": (s, {"closeness": 10})},
                         "Lash out": with_({"person": (s, {"closeness": -10, "conflict": 20})}, mental=1)}))
            break
    for p in people:
        if p.get("relation") in ("Mother", "Father") and p.get("age", 0) >= 78 and age >= 30 and not p.get("care"):
            who = f"Your {p['relation'].lower()}, {_first(p)},"
            out.append((f"care:{p['name']}", f"{who} can't safely live alone any more.",
                        {"Move them in with you": with_(S(fn=_care(p, "home")), mental=-2, person=(p, {"closeness": 15})),
                         "Pay for a good care home": S(cash=-40000, fn=_care(p, "care home")),
                         "Leave it to the rest of the family": with_({"person": (p, {"closeness": -20})}, mental=-2)}))
            break
    if partner and partner.get("married") and age >= 22:
        out.append(("inlaws", "Your in-laws are coming to stay for a whole month.",
                    {"Roll out the red carpet": with_(S(cash=-1000), mental=-2, person=(partner, {"closeness": 8})),
                     "Keep the peace": {"mental": -1},
                     "Suddenly get very busy": {"person": (partner, {"closeness": -6})}}))
    for n in (10, 20, 30):
        if age in (17 + n, 18 + n):
            out.append((f"reunion{n}", f"An invitation arrives: your {n}-year school reunion.",
                        {"Go": with_(S(fn=_reunion(friends, age)), social=2), "Skip it": {"mental": 1}}))
    return out
