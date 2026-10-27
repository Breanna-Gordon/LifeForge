"""Romance drama: break-ups, situationships, cheating (by you and by them),
getting back together, and the cards that ask you what to do."""
import random
from constants import fmt

def is_casual(p):
    return bool(p) and p.get("status") == "situationship"

# ---- endings ----------------------------------------------------------------
def _become_ex(p, friends, bad, log_text=None):
    p["married"] = False
    p["engaged"] = False
    p["merged"] = False
    p["status"] = None
    p["romance"] = 0
    if bad:
        p["category"], p["relation"] = "enemy", "Ex (bad terms)"
        p["conflict"] = max(p["conflict"], 55)
        p["closeness"] = min(p["closeness"], 15)
    else:
        p["category"], p["relation"] = "friend", "Ex"
        p["closeness"] = max(15, p["closeness"] // 2)
    if p not in friends:
        friends.append(p)

def divorce_share(p):
    """Share of your cash a divorce costs. A prenup caps it."""
    if p.get("prenup"):
        return 0.08
    return 0.5 if p.get("merged") else 0.25

def break_up(p, friends, state, log, divorce_ok=True):
    """The player ends it. Returns money lost (divorces are costly)."""
    married = bool(p.get("married"))
    casual = is_casual(p)
    stats = state["stats"]
    bad = (p["conflict"] >= 50 or p.get("cheated")
           or (("hot-tempered" in p["traits"] or "jealous" in p["traits"]) and random.random() < 0.5))
    lost = int(state["money"] * divorce_share(p)) if married else 0
    state["money"] -= lost
    _become_ex(p, friends, bad)
    stats["mental"] = max(0, stats["mental"] - (1 if casual else 5 if p["closeness"] >= 55 else 2))
    word = "marriage" if married else "situationship" if casual else "relationship"
    log(f"You ended the {word} with {p['name']}." + (" It got ugly." if bad else " It was fairly amicable.")
        + (f" The divorce cost you ${fmt(lost)}." if lost else ""))
    return lost

def they_end_it(p, friends, state, log, reason, bad=True):
    married = bool(p.get("married"))
    lost = int(state["money"] * divorce_share(p)) if married else 0
    state["money"] -= lost
    _become_ex(p, friends, bad)
    state["stats"]["mental"] = max(0, state["stats"]["mental"] - 5)
    log(f"{p['name']} ended things: {reason}." + (f" The divorce cost you ${fmt(lost)}." if lost else ""))

def make_official(p, state, log):
    """Ask a situationship to become a proper relationship."""
    score = (p["closeness"] + p["trust"] + p["romance"]) / 3
    chance = max(0.1, min(0.9, (score - 35) / 50 + (p.get("compat", 50) - 50) / 200))
    if random.random() < chance:
        p["status"] = None
        p["romance"] = max(p["romance"], 50)
        p["closeness"] = min(100, p["closeness"] + 6)
        log(f"{p['name']} said yes. You're official now!")
        return True
    p["closeness"] = max(0, p["closeness"] - 6)
    p["conflict"] = min(100, p["conflict"] + 8)
    log(f"{p['name']} isn't ready for anything serious.")
    return False

def get_back_together(p, state, log):
    """Try again with an ex. Returns True if they take you back."""
    chance = (p["closeness"] - 10) / 120 + 0.2 - (0.2 if p.get("cheated") else 0) + (0.1 if "loyal" in p["traits"] else 0)
    chance = max(0.08, min(0.8, chance))
    if p["category"] == "friend" and random.random() < chance:
        p["category"], p["relation"] = "partner", "Partner"
        p["status"] = None
        p["romance"], p["trust"] = 40, max(10, p["trust"] - 10)
        p["conflict"] = max(0, p["conflict"] - 10)
        p["cheated"] = False
        log(f"You and {p['name']} got back together.")
        return True
    p["closeness"] = max(0, p["closeness"] - 6)
    log(f"{p['name']} doesn't want to go back there.")
    return False

# ---- yearly drama -----------------------------------------------------------------
def romance_year(state, age, partner, friends, log, make_admirer, fame):
    """Runs at year end. Returns (partner, cards for next year)."""
    cards = []
    stats = state["stats"]
    if partner is None:
        state["fling"] = None
        return partner, cards
    t = partner["traits"]

    # situationships go somewhere, or nowhere
    if is_casual(partner):
        if partner["closeness"] < 35 and random.random() < 0.3:
            _become_ex(partner, friends, False)
            stats["mental"] = max(0, stats["mental"] - 2)
            log(f"{partner['name']} stopped replying. You've been ghosted.")
            return None, cards
        if partner["closeness"] >= 55 and partner["romance"] >= 45 and random.random() < 0.3:
            cards.append({"kind": "official", "person": partner, "text": f"{partner['name']} asks: \"What are we?\"",
                          "why": "They want to make it official."})
        elif random.random() < 0.12:
            partner["trust"] = max(0, partner["trust"] - 20)
            partner["conflict"] = min(100, partner["conflict"] + 15)
            partner["romance"] = max(0, partner["romance"] - 8)
            log(f"You found out {partner['name']} has been seeing other people too.")
    elif age >= 16:
        # a partner might stray
        base = 0.015 + (0.03 if partner["romance"] < 35 else 0) + (0.03 if partner["trust"] < 35 else 0)
        base += (0.02 if "outgoing" in t else 0) - (0.02 if "loyal" in t else 0)
        base += 0.01 if partner["stats"]["looks"] >= 70 else 0
        if partner.get("married"):
            base *= 0.7
        if random.random() < max(0.0, base):
            partner["cheated"] = True
            if random.random() < 0.6:
                cards.append({"kind": "cheated", "person": partner,
                              "text": f"You find out {partner['name']} has been cheating on you.",
                              "why": "Messages, a friend's tip... it's clear. What will you do?"})
            else:
                partner["trust"] = max(0, partner["trust"] - 6)

    if not is_casual(partner) and age >= 18:
        _partner_work(partner, log)

    # engaged couples talk about a prenup
    if partner.get("engaged") and not partner.get("prenup_done") and age >= 18:
        from people import finances
        mine = state["money"] + state.get("savings", 0) + state.get("invest", 0)
        f = finances(partner)
        if mine >= 250000 and mine > f["savings"] * 2:
            cards.append({"kind": "prenup", "person": partner,
                          "text": f"You're engaged to {partner['name']}. Do you want a prenup?",
                          "why": "It protects your money in a divorce, but asking can hurt feelings."})
        elif f["savings"] >= 250000 and f["savings"] > mine * 2:
            cards.append({"kind": "prenupask", "person": partner,
                          "text": f"{partner['name']} asks you to sign a prenup.",
                          "why": "It would limit what you'd get in a divorce."})
        elif random.random() < 0.5:
            partner["prenup_done"] = True

    # a long, happy relationship may bring a proposal
    if (not is_casual(partner) and not partner.get("married") and not partner.get("engaged") and age >= 18
            and partner.get("years", 0) >= 2 and partner["closeness"] >= 65 and partner["trust"] >= 55
            and partner["romance"] >= 60 and random.random() < 0.22):
        tier = _ring_tier(partner)
        cards.append({"kind": "proposed", "person": partner, "ring": tier,
                      "text": f"{partner['name']} gets down on one knee and proposes!",
                      "why": f"They chose a {tier} ring."})

    # the player's own affair
    fling = state.get("fling")
    if fling and not is_casual(partner):
        state["cheat_years"] = state.get("cheat_years", 0) + 1
        found = 0.25 + 0.08 * state["cheat_years"] + (0.15 if "jealous" in t else 0)
        if random.random() < found:
            partner["trust"] = max(0, partner["trust"] - 45)
            partner["romance"] = max(0, partner["romance"] - 35)
            partner["conflict"] = min(100, partner["conflict"] + 40)
            stats["social"] = max(0, stats["social"] - 3)
            state["fling"] = None
            state["cheat_years"] = 0
            if random.random() < 0.7:
                they_end_it(partner, friends, state, log, "they found out you were cheating")
                return None, cards
            log(f"{partner['name']} found out about your fling but gave you one last chance.")
        elif random.random() < 0.35:
            state["fling"] = None
            state["cheat_years"] = 0
            log("Your secret fling fizzled out.")
        else:
            stats["mental"] = max(0, stats["mental"] - 2)      # guilt
    elif fling:
        state["fling"] = None

    # temptation
    if age >= 18 and not is_casual(partner) and not state.get("fling"):
        looks = max(0, stats["looks"] - 50) / 100 * 0.6
        soc = max(0, stats["social"] - 50) / 100 * 0.6
        ft = fame / 100 * 0.5
        chance = 0.03 + 0.25 * (1 - (1 - looks) * (1 - soc) * (1 - ft))
        if random.random() < chance:
            cand = make_admirer()
            cards.append({"kind": "temptation", "person": cand,
                          "text": f"{cand['name']} is flirting with you, even though you're with {partner['name']}.",
                          "why": "It could be harmless... or not."})
    return partner, cards

# ---- card choices ------------------------------------------------------------------
RINGS = {"Simple $500": ("simple", 500, 0.0), "Classic $3,000": ("classic", 3000, 0.08), "Lavish $15,000": ("lavish", 15000, 0.16)}
WEDDINGS = {"Small $1,000": ("small", 1000, (3, 2, 5), 0.0), "Classic $15,000": ("classic", 15000, (5, 4, 10), 0.2),
            "Grand $50,000": ("grand", 50000, (7, 6, 15), 0.3)}
FAMILY_HELP = {"Struggling": 0.0, "Comfortable": 0.2, "Wealthy": 0.5}

LABELS = {
    "ringchoice": tuple(RINGS) + ("Cancel",),
    "weddingchoice": tuple(WEDDINGS) + ("Not yet",),
    "proposed": ("Say yes", "Not yet"),
    "date": ("Date them", "Keep it casual", "Decline"),
    "dance": ("Accept", "Decline"),
    "friend": ("Accept", "Decline"),
    "hangout": ("Accept", "Decline"),
    "cheated": ("Forgive", "Confront", "Break up"),
    "official": ("Make it official", "Keep it casual"),
    "temptation": ("Flirt back", "Turn them down"),
    "prenup": ("Ask for a prenup", "Skip it"),
    "prenupask": ("Sign it", "Refuse"),
}
HEADS = {"ringchoice": "Choose a ring", "weddingchoice": "Plan the wedding", "proposed": "A proposal!","dance": "School dance", "date": "Date invite", "friend": "Friend request", "hangout": "Invitation",
         "cheated": "Betrayal", "official": "What are we?", "temptation": "Temptation", "prenup": "Prenup?", "prenupask": "A prenup"}

def household_income(partner):
    """Money a spouse brings in each year."""
    from people import finances
    f = finances(partner)
    pay = 0 if f.get("jobless") else f["pay"]
    if partner.get("merged"):
        return pay
    return int(pay * 0.25)

def try_merge(p, state, log):
    """Ask your spouse to pool your money. Needs trust and a good match."""
    if p.get("prenup"):
        log(f"Your prenup with {p['name']} keeps your money separate.")
        return False
    chance = p["trust"] / 100 + (p.get("compat", 50) - 50) / 200 - (0.25 if "jealous" in p["traits"] else 0) + (0.1 if "loyal" in p["traits"] else 0)
    if random.random() < max(0.1, min(0.95, chance)):
        from people import finances
        f = finances(p)
        state["money"] += f["savings"]
        state["debt"] = state.get("debt", 0) + f["debt"]
        f["savings"], f["debt"] = 0, 0
        p["merged"] = True
        p["trust"] = min(100, p["trust"] + 5)
        log(f"You and {p['name']} combined your finances. Their income now joins yours.")
        return True
    p["trust"] = max(0, p["trust"] - 4)
    log(f"{p['name']} would rather keep money separate for now.")
    return False

def _ring_tier(partner):
    from people import finances
    pay = finances(partner)["pay"]
    return "lavish" if pay >= 80000 else "classic" if pay >= 30000 else "simple"

def resolve_card(inv, pick, partner, friends, state, log):
    """Handles the romance cards. Returns the partner."""
    kind, p = inv["kind"], inv["person"]
    stats = state["stats"]
    if kind == "ringchoice":
        if pick == "Cancel":
            state["actions_remaining"] += 1
            state["actions_used"]["__propose__"] = 0
            return partner
        tier, cost, bonus = RINGS[pick]
        if state["money"] < cost:
            log(f"You can't afford the {tier} ring.")
            inv["_retry"] = True
            return partner
        score = (p["closeness"] + p["trust"] + p["romance"]) / 3
        chance = max(0.05, min(0.95, (score - 40) / 50 + 0.15 + (p.get("compat", 50) - 50) / 200 + bonus))
        if random.random() < chance:
            state["money"] -= cost
            p["engaged"] = True
            p["ring"] = tier
            p["romance"] = min(100, p["romance"] + 8)
            stats["mental"] = min(100, stats["mental"] + 3)
            log(f"{p['name']} said yes to your {tier} ring! You're engaged.")
        else:
            p["closeness"] = max(0, p["closeness"] - 10)
            log(f"You proposed to {p['name']}, who wasn't ready.")
        return partner
    if kind == "weddingchoice":
        if pick == "Not yet":
            return partner
        tier, cost, (ment, soc, rom), help_pct = WEDDINGS[pick]
        help_amt = int(cost * _wj.tier_value(state, FAMILY_HELP)) if state.get("parents_ok") else 0
        net = cost - help_amt
        if state["money"] < net:
            log(f"You can't afford a {tier} wedding yet (you'd pay ${fmt(net)}).")
            inv["_retry"] = True
            return partner
        state["money"] -= net
        gifts = 0 if tier == "small" else int(cost * random.uniform(0.1, 0.3))
        state["money"] += gifts
        p["married"], p["engaged"], p["relation"] = True, False, "Spouse"
        p["wedding"] = tier
        p["romance"] = min(100, p["romance"] + rom)
        p["closeness"] = min(100, p["closeness"] + rom)
        stats["mental"] = min(100, stats["mental"] + ment)
        stats["social"] = min(100, stats["social"] + soc)
        msg = f"You married {p['name']} in a {tier} wedding (cost ${fmt(net)}"
        if help_amt:
            msg += f", your family chipped in ${fmt(help_amt)}"
        if gifts:
            msg += f", guests gave ${fmt(gifts)}"
        log(msg + ").")
        return partner
    if kind == "proposed":
        ring = inv.get("ring", "classic")
        if pick == "Say yes":
            p["engaged"], p["ring"] = True, ring
            p["romance"] = min(100, p["romance"] + 10)
            stats["mental"] = min(100, stats["mental"] + 3)
            log(f"You said yes to {p['name']}'s {ring} ring. You're engaged!")
        else:
            p["closeness"] = max(0, p["closeness"] - 5)
            p["trust"] = max(0, p["trust"] - 3)
            log(f"You told {p['name']} you're not ready to get engaged.")
        return partner
    if kind == "cheated":
        if pick == "Forgive":
            p["trust"] = max(0, p["trust"] - 25)
            p["romance"] = max(0, p["romance"] - 10)
            stats["mental"] = max(0, stats["mental"] - 3)
            log(f"You forgave {p['name']}, but trust will take time to rebuild.")
        elif pick == "Confront":
            p["conflict"] = min(100, p["conflict"] + 30)
            p["trust"] = max(0, p["trust"] - 15)
            if random.random() < 0.5:
                p["romance"] = min(100, p["romance"] + 5)
                log(f"{p['name']} admitted it and swore it was over. You're still together.")
            else:
                they_end_it(p, friends, state, log, "the confrontation blew up")
                return None
        else:
            break_up(p, friends, state, log)
            return None
        return partner
    if kind == "official":
        if pick == "Make it official":
            p["status"] = None
            p["romance"] = max(p["romance"], 50)
            log(f"You and {p['name']} made it official.")
        else:
            p["closeness"] = max(0, p["closeness"] - 4)
            log(f"You told {p['name']} you'd rather keep it casual.")
        return partner
    if kind in ("prenup", "prenupask"):
        asked = kind == "prenup"
        if pick in ("Skip it",):
            p["prenup_done"] = True
            log(f"You decided against a prenup with {p['name']}.")
            return partner
        if asked:
            chance = 0.35 + p["trust"] / 150 + (0.15 if p["romance"] >= 70 else -0.1) - (0.2 if "jealous" in p["traits"] else 0)
            if random.random() < max(0.1, min(0.9, chance)):
                p["prenup"] = p["prenup_done"] = True
                log(f"{p['name']} agreed to a prenup. If it ends, a divorce will cost you far less.")
            else:
                p["prenup_done"] = True
                p["trust"] = max(0, p["trust"] - 12)
                p["romance"] = max(0, p["romance"] - 6)
                log(f"{p['name']} was hurt that you asked for a prenup.")
                if random.random() < 0.15:
                    p["engaged"] = False
                    p["ring"] = None
                    log(f"{p['name']} called off the engagement.")
        elif pick == "Sign it":
            p["prenup"] = p["prenup_done"] = True
            log(f"You signed the prenup {p['name']} asked for. Your money stays yours.")
        else:
            p["prenup_done"] = True
            p["trust"] = max(0, p["trust"] - 10)
            p["romance"] = max(0, p["romance"] - 5)
            log(f"You refused {p['name']}'s prenup.")
            if random.random() < 0.3:
                p["engaged"] = False
                p["ring"] = None
                log(f"{p['name']} called off the engagement.")
        return partner
    if kind == "temptation":
        if pick == "Flirt back":
            state["fling"] = p
            state["cheat_count"] = state.get("cheat_count", 0) + 1
            state["cheat_years"] = 0
            stats["mental"] = min(100, stats["mental"] + 2)
            log(f"You flirted back with {p['name']}. Your partner doesn't know.")
        else:
            partner["trust"] = min(100, partner["trust"] + 2)
            stats["mental"] = min(100, stats["mental"] + 1)
            log(f"You turned {p['name']} down and stayed faithful.")
    return partner


import worldjobs as _wj
NEW_JOBS = ["nurse", "teacher", "electrician", "accountant", "chef", "designer", "mechanic", "shop manager",
            "engineer", "journalist", "paramedic", "builder", "dentist", "driver", "developer", "lawyer"]

def _partner_work(p, log):
    """Partners have careers too: promotions, layoffs, new jobs, retirement."""
    from people import finances
    f = finances(p)
    name, age = p["name"], p.get("age", 30)
    if age >= 66:
        if not f.get("retired"):
            f["retired"], f["jobless"] = True, 0
            f["pay"] = f["pay"] // 2
            log(f"{name} retired and now lives on a pension.")
        return
    if f.get("jobless"):
        f["jobless"] -= 1
        f["savings"] = max(0, f["savings"] - int(f["pay"] * 0.3))
        if f["jobless"] <= 0 or random.random() < 0.5:
            f["jobless"] = 0
            f["pay"] = max(8000, int(f["pay"] * random.uniform(0.75, 1.1) / 100) * 100)
            p["job_title"] = _wj.pick_job()[0]
            log(f"{name} found a new job as {'an' if p['job_title'][0].lower() in 'aeiou' else 'a'} {p['job_title']}.")
        return
    if f["pay"] <= 0:
        return
    x = random.random()
    if x < 0.05 and age < 62:
        f["jobless"] = random.randint(1, 3)
        p["conflict"] = min(100, p["conflict"] + 6)
        log(f"{name} was laid off. Money may be tight until they find work.")
    elif x < 0.14:
        f["pay"] = int(f["pay"] * random.uniform(1.12, 1.3) / 100) * 100
        log(f"{name} got a promotion and now earns ${fmt(f['pay'])} a year.")
    elif x < 0.22:
        f["pay"] = int(f["pay"] * 1.05 / 100) * 100
    elif x < 0.26:
        f["pay"] = max(8000, int(f["pay"] * random.uniform(0.7, 1.5) / 100) * 100)
        p["job_title"] = _wj.pick_job()[0]
        log(f"{name} changed careers and is now {'an' if p['job_title'][0].lower() in 'aeiou' else 'a'} {p['job_title']}.")
