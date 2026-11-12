"""The story director: every system that tells multi-year stories (royal
life, fame, relationships, money) offers "beats" here, and one is picked each
year to sit alongside the normal event.

A beat is (id, text, options). Options use the usual consequence keys (stat
deltas, "person": (p, fx), "gamble") plus a "story" act for anything else:
    S(cash=-500, fn=lambda state: "what happened")
Beat ids are remembered so a story only happens once; ids starting with "~"
can repeat.
"""
import random

COOLDOWN = 4      # years before a repeatable beat can come back

def S(**kw):
    """An option that runs a story act: cash change and/or a function."""
    return {"act": ("story", kw)}

def with_(base, **stats):
    out = dict(base)
    out.update(stats)
    return out

def a_story(state, arg):
    arg = arg or {}
    notes = []
    if arg.get("cash"):
        state["money"] = max(0, state["money"] + arg["cash"])
    fn = arg.get("fn")
    if fn:
        note = fn(state)
        if note:
            notes.append(note)
    return " ".join(notes)

def _sources():
    import station, publiclife, bonds, budget, idol, pathways
    return (station._story, publiclife.beats, bonds.beats, budget.beats, idol.beats, pathways.beats)

def story_event(state, ctx, age, chance=0.8):
    flags = state.setdefault("flags", {})
    beats = []
    for src in _sources():
        try:
            beats += src(state, ctx, age)
        except Exception:        # a broken story never stops the year
            pass
    def ready(bid):
        if bid.startswith("~"):      # repeatable beats rest for a few years
            return age - flags.get("last_" + bid, -99) >= COOLDOWN
        return not flags.get("seen_" + bid)
    beats = [b for b in beats if ready(b[0])]
    if not beats or random.random() > chance:
        return None
    once = [b for b in beats if not b[0].startswith("~")]
    pool = once if once and random.random() < 0.75 else beats
    bid, text, opts = random.choice(pool[:4]) if pool is once else random.choice(pool)
    if bid.startswith("~"):
        flags["last_" + bid] = age
    else:
        flags["seen_" + bid] = True
    return text, opts

def install():
    import lifeevents
    lifeevents.ACTS["story"] = a_story
