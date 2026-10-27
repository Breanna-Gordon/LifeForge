import random

# Situational events. Each one only shows up when its condition fits your
# life right now (a job, a partner, studying, money, age), so no two
# playthroughs feel the same. Effects may include "money" (dollars) as well
# as the usual stats.
def _job(c): return c["career"]["job"] is not None
def _uni(c): return c["career"]["enrolled"]
def _partner(c): return c["partner"] is not None
def _friends(c): return len(c["friends"]) > 0
def _broke(c): return c["money"] < 40
def _comfortable(c): return c["money"] >= 150

SITUATIONAL = [
    {"text": "Your boss offers you a project nobody else wants.", "min": 18, "max": 70, "cond": _job,
     "options": {"Take it on": {"wealth": 3, "mental": -3, "money": 20}, "Politely refuse": {"mental": 1, "social": -1}}},
    {"text": "A coworker takes credit for your work.", "min": 18, "max": 70, "cond": _job,
     "options": {"Speak up": {"social": -1, "mental": 2, "wealth": 1}, "Let it go": {"mental": -3}}},
    {"text": "Your team invites you to after-work drinks.", "min": 18, "max": 70, "cond": _job,
     "options": {"Join them": {"social": 3, "money": -15}, "Head home": {"mental": 1}}},
    {"text": "You're up for a pay rise.", "min": 20, "max": 65, "cond": _job,
     "options": {"Ask for more": {"wealth": 3, "money": 30, "social": -1}, "Accept the offer": {"wealth": 1, "money": 10}}},
    {"text": "The company announces layoffs.", "min": 20, "max": 65, "cond": _job,
     "options": {"Work extra hard": {"mental": -3, "wealth": 2}, "Update your CV quietly": {"mental": 1, "academic": 1}}},
    {"text": "A group project is going badly at university.", "min": 18, "max": 99, "cond": _uni,
     "options": {"Take charge": {"academic": 3, "mental": -2}, "Let others lead": {"academic": -1, "social": 1}}},
    {"text": "You have a finals week crunch.", "min": 18, "max": 99, "cond": _uni,
     "options": {"Pull all-nighters": {"academic": 4, "physical": -3, "mental": -2}, "Study steadily": {"academic": 3, "mental": 1}}},
    {"text": "A lecturer invites you to help with their research.", "min": 18, "max": 99, "cond": _uni,
     "options": {"Say yes": {"academic": 4, "social": 1, "mental": -1}, "Focus on your own work": {"academic": 1}}},
    {"text": "Your partner suggests a weekend away.", "min": 16, "max": 99, "cond": _partner,
     "options": {"Book it": {"social": 3, "mental": 3, "money": -40}, "Suggest staying in": {"social": 1, "money": 0}}},
    {"text": "You and your partner have a big disagreement.", "min": 16, "max": 99, "cond": _partner,
     "options": {"Talk it through": {"social": 2, "mental": 1}, "Give them the silent treatment": {"social": -3, "mental": -2}}},
    {"text": "It's your anniversary.", "min": 17, "max": 99, "cond": _partner,
     "options": {"Plan something special": {"social": 4, "mental": 2, "money": -30}, "Forget about it": {"social": -4, "mental": -2}}},
    {"text": "A friend is going through a hard time.", "min": 10, "max": 99, "cond": _friends,
     "options": {"Be there for them": {"social": 3, "mental": 1, "physical": -1}, "Give them space": {"social": -1}}},
    {"text": "A friend asks to borrow some money.", "min": 16, "max": 99, "cond": _friends,
     "options": {"Lend it": {"social": 2, "money": -25}, "Say no": {"social": -2, "mental": 1}}},
    {"text": "You're invited to a friend's wedding.", "min": 20, "max": 99, "cond": _friends,
     "options": {"Go and celebrate": {"social": 4, "mental": 2, "money": -35}, "Send a card": {"social": 1, "money": -5}}},
    {"text": "An unexpected bill arrives.", "min": 18, "max": 99, "cond": _broke,
     "options": {"Pay it now": {"money": -30, "mental": -2}, "Ask family for help": {"social": -1, "money": -5, "mental": 1}}},
    {"text": "You find a second-hand bargain you didn't need.", "min": 14, "max": 99, "cond": _comfortable,
     "options": {"Buy it": {"mental": 2, "money": -25}, "Walk away": {"wealth": 1, "money": 0}}},
    {"text": "Someone pitches you a 'sure thing' investment.", "min": 20, "max": 99, "cond": _comfortable,
     "options": {"Invest": {"gamble": [{"money": 90, "mental": 1}, {"money": -60, "mental": -2}]}, "Pass": {"mental": 1}}},
    {"text": "You get a seasonal flu.", "min": 3, "max": 99, "cond": lambda c: True,
     "options": {"Rest up": {"physical": 1, "mental": 1, "money": -5}, "Push through": {"physical": -4, "mental": -1}}},
    {"text": "A neighbour invites you to a street party.", "min": 8, "max": 99, "cond": lambda c: True,
     "options": {"Go along": {"social": 3, "mental": 1}, "Stay in": {"mental": 1}}},
    {"text": "You discover a new hobby online.", "min": 10, "max": 99, "cond": lambda c: True,
     "options": {"Dive in": {"mental": 3, "money": -10}, "Bookmark it for later": {"mental": 0}}},
    {"text": "You find some money on the pavement.", "min": 6, "max": 99, "cond": lambda c: True,
     "options": {"Keep it": {"money": 10, "mental": 1}, "Hand it in": {"social": 1, "mental": 2}}},
    {"text": "A school trip is announced.", "min": 8, "max": 17, "cond": lambda c: True,
     "options": {"Sign up": {"social": 3, "mental": 2, "money": -10}, "Skip it": {"mental": 0, "money": 0}}},
    {"text": "A teacher says you could be a top student.", "min": 11, "max": 17, "cond": lambda c: c["stats"]["academic"] >= 60,
     "options": {"Aim higher": {"academic": 4, "mental": -1}, "Stay relaxed": {"mental": 2}}},
    {"text": "You're falling behind at school.", "min": 8, "max": 17, "cond": lambda c: c["stats"]["academic"] < 40,
     "options": {"Ask for help": {"academic": 3, "social": 1}, "Hope it sorts itself out": {"academic": -3, "mental": -1}}},
    {"text": "You've been feeling out of shape.", "min": 14, "max": 99, "cond": lambda c: c["stats"]["physical"] < 40,
     "options": {"Start moving more": {"physical": 4, "mental": 1}, "Do nothing": {"physical": -2}}},
    {"text": "You feel lonely lately.", "min": 12, "max": 99, "cond": lambda c: c["stats"]["social"] < 35,
     "options": {"Reach out to someone": {"social": 4, "mental": 2}, "Keep to yourself": {"social": -2, "mental": -2}}},
    {"text": "Someone compliments how you look.", "min": 13, "max": 70, "cond": lambda c: c["stats"]["looks"] >= 65,
     "options": {"Smile and say thanks": {"social": 2, "mental": 1}, "Brush it off": {"mental": 0}}},
    {"text": "You get teased about your appearance.", "min": 10, "max": 30, "cond": lambda c: c["stats"]["looks"] < 40,
     "options": {"Shrug it off": {"mental": 0, "social": -1}, "Let it get to you": {"mental": -3}, "Treat yourself to a makeover": {"looks": 3, "money": -20}}},
    {"text": "A coach spots you at a local sports day.", "min": 9, "max": 25, "cond": lambda c: c["stats"]["athletic"] >= 65,
     "options": {"Start training with them": {"athletic": 4, "physical": 1, "social": 1}, "Stay casual": {"mental": 1}}},
    {"text": "You pull a muscle while exercising.", "min": 14, "max": 99, "cond": lambda c: c["stats"]["athletic"] >= 50,
     "options": {"Rest it": {"physical": 1, "athletic": -1}, "Train through the pain": {"physical": -4, "athletic": 1}}},
    {"text": "You're asked to model for a friend's project.", "min": 16, "max": 45, "cond": lambda c: c["stats"]["looks"] >= 60,
     "options": {"Say yes": {"looks": 1, "social": 2, "money": 15}, "Decline": {"mental": 0}}},
    {"text": "School reports are coming home.", "min": 8, "max": 17, "cond": lambda c: True,
     "options": {"Hand it over proudly": {"mental": 1, "social": 1}, "Hope nobody asks": {"mental": -1}}},
    {"text": "Your phone breaks.", "min": 12, "max": 99, "cond": lambda c: True,
     "options": {"Replace it": {"money": -30}, "Live without for a while": {"mental": 1, "social": -1}}},
    {"text": "You're offered a lift to a festival.", "min": 16, "max": 45, "cond": lambda c: True,
     "options": {"Go": {"social": 3, "mental": 2, "money": -20}, "Stay at home": {"money": 0}}},
    {"text": "You get lost on a hike.", "min": 10, "max": 70, "cond": lambda c: True,
     "options": {"Stay calm and retrace your steps": {"mental": 1, "physical": 1}, "Panic": {"mental": -3}}},
    {"text": "A relative asks you to visit.", "min": 12, "max": 99, "cond": lambda c: True,
     "options": {"Visit them": {"social": 3, "mental": 1, "money": -10}, "Call instead": {"social": 1}}},
    {"text": "You're offered a chance to volunteer.", "min": 14, "max": 99, "cond": lambda c: True,
     "options": {"Sign up": {"social": 3, "mental": 3, "physical": 1}, "Not now": {}}},
    {"text": "You take up a creative project.", "min": 12, "max": 99, "cond": lambda c: True,
     "options": {"Commit to it": {"mental": 4, "social": 1}, "Let it fizzle": {"mental": -1}}},
]

def relationship_events(ctx):
    """Events generated from your actual relationships: neglected friends and
    partners speak up, close friends reach out, and conflicts flare up."""
    out = []
    people = ctx.get("friends", []) + ([ctx["partner"]] if ctx.get("partner") else [])
    for p in people:
        n = p["name"]
        if p["closeness"] < 45:
            out.append((f"{n} says you never make time for them any more.", {
                "Apologise and arrange a meetup": {"person": (p, {"closeness": 8, "trust": 4}), "social": 1},
                "Make an excuse": {"person": (p, {"closeness": -2, "trust": -3}), "social": -1},
                "Brush it off": {"person": (p, {"closeness": -6, "conflict": 10}), "mental": 1}}))
        elif p["closeness"] >= 60:
            out.append((f"{n} invites you out for the day.", {
                "Go together": {"person": (p, {"closeness": 6, "trust": 2}), "social": 2, "mental": 1, "money": -10},
                "Maybe next time": {"person": (p, {"closeness": -2}), "mental": 0}}))
        if p["conflict"] >= 40:
            out.append((f"You and {n} are still on bad terms.", {
                "Clear the air": {"person": (p, {"conflict": -30, "trust": 3}), "mental": 1},
                "Avoid them": {"person": (p, {"closeness": -4}), "mental": -1}}))
        if "jealous" in p["traits"] and p["category"] == "partner":
            out.append((f"{n} gets jealous about the time you spend with friends.", {
                "Reassure them": {"person": (p, {"trust": 5, "romance": 3}), "social": -1},
                "Tell them it's fine": {"person": (p, {"trust": -4, "conflict": 10}), "mental": 0}}))
    for c in [x for x in ctx.get("people", []) if x.get("is_child")]:
        n, a = c["name"], c.get("age", 0)
        if a <= 4:
            out.append((f"{n} wakes up crying in the night.", {
                "Get up and comfort them": {"person": (c, {"closeness": 4, "trust": 3}), "mental": -1},
                "Let them settle on their own": {"person": (c, {"trust": -4}), "mental": 0}}))
        elif a <= 12:
            out.append((f"{n} has a school play.", {
                "Be in the audience": {"person": (c, {"closeness": 6, "trust": 3}), "social": 1, "mental": 1},
                "Miss it for work": {"person": (c, {"closeness": -5, "trust": -3}), "money": 10}}))
            out.append((f"{n} wants a pet.", {
                "Get a pet": {"person": (c, {"closeness": 7}), "money": -30, "social": 1},
                "Say not yet": {"person": (c, {"closeness": -2}), "mental": 0}}))
        elif a <= 17:
            out.append((f"{n} wants a later curfew.", {
                "Compromise": {"person": (c, {"trust": 4, "closeness": 2}), "mental": 0},
                "Say no": {"person": (c, {"closeness": -5, "conflict": 12}), "mental": -1}}))
        else:
            out.append((f"{n} asks to borrow some money.", {
                "Help out": {"person": (c, {"closeness": 6, "trust": 2}), "money": -30},
                "Encourage them to manage alone": {"person": (c, {"closeness": -2}), "mental": 1}}))
    for p in ctx.get("people", []):
        if p["category"] == "family" and p["closeness"] < 35 and not p.get("is_child"):
            out.append((f"Your {p['relation'].lower()}, {p['name']}, feels distant from you.", {
                "Reach out": {"person": (p, {"closeness": 8, "trust": 3}), "social": 1},
                "Leave it": {"person": (p, {"closeness": -3}), "mental": 0}}))
    return out

def eligible(age, ctx):
    return [e for e in SITUATIONAL if e["min"] <= age <= e["max"] and e["cond"](ctx)]

def pick_year_events(age, ctx, normal_pool, wildcard_pool, last_text, extra_chance=0.55, recent=()):
    """Returns 1-2 events for the year: [(text, options_dict), ...].
    `recent` holds events seen lately so the same ones don't keep coming back."""
    use_wild = bool(wildcard_pool) and random.random() < 0.15
    pool = wildcard_pool if use_wild else normal_pool
    cands = list(pool.items())
    if len(cands) > 1 and last_text:
        f = [c for c in cands if c[0] != last_text]
        cands = f or cands
    fresh = [c for c in cands if c[0] not in recent]
    events = [random.choice(fresh or cands)]
    rel = [r for r in relationship_events(ctx) if r[0] not in recent]
    if rel and random.random() < 0.5:
        events.append(random.choice(rel))
    elif random.random() < extra_chance:
        sit = [e for e in eligible(age, ctx) if e["text"] != events[0][0] and e["text"] not in recent]
        if not sit:
            sit = [e for e in eligible(age, ctx) if e["text"] != events[0][0]]
        if sit:
            e = random.choice(sit)
            events.append((e["text"], e["options"]))
    return events

def describe(consequence):
    names = {"physical": "Health", "wealth": "Wealth", "mental": "Mental", "social": "Social", "academic": "Academic", "looks": "Looks", "athletic": "Athletic"}
    parts = []
    if "gamble" in consequence:
        return "Risky: it could go either way"
    for k, v in consequence.items():
        if k == "person":
            who, fx = v
            parts.append(", ".join(f"{who['name']}: {kk.title()} {vv:+d}" for kk, vv in fx.items()))
            continue
        if v == 0: continue
        if k == "money":
            parts.append(f"{'+' if v>0 else '-'}${abs(v)}")
        else:
            parts.append(f"{names[k]} {v:+d}")
    return ", ".join(parts) if parts else "No change"
