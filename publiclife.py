"""Public life: a social following that grows with fame, brand endorsements,
and the stories that come with being known (going viral, paparazzi, fans,
talk shows, awards, being 'cancelled')."""
import random
from constants import fmt
from stories import S, with_

def followers(state):
    return state.setdefault("followers", 0)

def short(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1000:
        return f"{n // 1000}k"
    return str(n)

def _fame(state):
    return (state.get("_career") or {}).get("fame", 0)

def _royal(state):
    import station
    return station.station(state) == "royal"

def year(state, career, age, log):
    if age < 12:
        return
    fame, social = career.get("fame", 0), state["stats"]["social"]
    target = int((fame / 100) ** 2.2 * 8_000_000 + social * 60 + (400 if fame else 0))
    f = followers(state)
    f += (target - f) * 0.3 + random.gauss(0, max(50, f * 0.04))
    state["followers"] = max(0, int(f))
    state["_endorse"] = 0
    if fame >= 40 and age >= 16 and not _royal(state):
        pay = min(5_000_000, int(state["followers"] * 0.04 * random.uniform(0.6, 1.2)))
        state["money"] += pay
        state["_endorse"] = pay
        state["endorse_last"] = pay
        if random.random() < 0.3:
            log(f"Brand deals and sponsored posts earned you ${fmt(pay)} this year.")
    else:
        state["endorse_last"] = 0

def snapshot_rows(state):
    f = followers(state)
    return [("Followers", short(f))] if f >= 1000 else []

def _fame_up(n):
    def fn(state):
        c = state.get("_career") or {}
        c["fame"] = max(0, min(100, c.get("fame", 0) + n))
        return ""
    return fn

def _approval(n):
    def fn(state):
        import station
        if station.station(state) in ("royal", "noble"):
            station.change_approval(state, n)
        return ""
    return fn

def beats(state, ctx, age):
    fame = _fame(state)
    royal = _royal(state)
    out = []
    if 13 <= age <= 35 and fame < 25:
        out.append(("viral", "A video you posted is blowing up overnight. Strangers are sharing it everywhere.",
                    {"Lean into it": with_(S(fn=_fame_up(12)), social=2), "Delete it before it gets weird": {"mental": 1}}))
    if fame >= 40 and random.random() < 0.3:
        out.append(("~paparazzi", "Photographers have been camped outside your home all week.",
                    {"Smile and give them a shot": with_(S(fn=_fame_up(2)), social=1),
                     "Confront them": {"gamble": [with_(S(fn=_fame_up(4)), social=-2), {"mental": -3, "social": -1}]},
                     "Stay indoors": {"mental": -2}}))
    if fame >= 50:
        out.append(("fans", "A fan waits outside with a hand-made gift and a letter about how you changed their life.",
                    {"Thank them warmly": {"social": 2, "mental": 2}, "Have security move them on": {"mental": -1}}))
    if fame >= 45 and age >= 16:
        out.append(("talkshow", "A primetime talk show wants you as a guest.",
                    {"Go on the show": {"gamble": [with_(S(fn=_fame_up(8)), social=2), with_(S(fn=_fame_up(-3)), mental=-3)]},
                     "Turn it down": {"mental": 1}}))
    job = (state.get("_career") or {}).get("job") or {}
    if fame >= 65 and job.get("fame"):
        out.append(("award", "You've been nominated for a major award in your field.",
                    {"Attend the ceremony": {"gamble": [with_(S(fn=_fame_up(10)), mental=5), {"mental": -2}]},
                     "Skip it and stay humble": {"mental": 1}}))
    if fame >= 55 and age >= 18 and not royal:
        out.append(("cancelled", "An old joke of yours resurfaces and people online want you 'cancelled'.",
                    {"Apologise sincerely": with_(S(fn=_fame_up(-3)), mental=-1),
                     "Double down": {"gamble": [S(fn=_fame_up(6)), with_(S(fn=_fame_up(-15)), mental=-4)]},
                     "Go quiet for a while": with_(S(fn=_fame_up(-6)), mental=-2)}))
    if fame >= 30 and age >= 16 and not royal:
        deal = max(5000, min(2_000_000, followers(state) // 10))
        out.append(("sponsor", f"A brand offers you a sponsorship deal worth ${fmt(deal)}.",
                    {"Sign it": S(cash=deal), "Only work with brands you believe in": {"mental": 2}}))
    if royal and fame >= 40 and age >= 18:
        out.append(("royal_brand", "A luxury brand quietly offers you millions to wear their clothes. Royals aren't meant to take money like this.",
                    {"Decline": S(fn=_approval(2)),
                     "Take it secretly": {"gamble": [S(cash=2_000_000), with_(S(cash=2_000_000, fn=_approval(-18)), mental=-3)]}}))
    return out
