"""Station: lives that don't follow the ordinary job ladder.

Royals don't apply for jobs: they carry out duties, live on a stipend that
depends on public approval, and get pulled through palace storylines (first
engagement, the palace vetting a partner, scandals, coronation, abdication).
They can step back from royal life, which ends the stipend and opens the job
board. Nobles run an estate alongside ordinary careers. Other starting
scenarios (tycoon, celebrity parents, sports family...) get a family
expectations storyline so where you started keeps mattering.
"""
import random
import pygame
from constants import (WHITE, INK, MUTED, OUTLINE, ACCENT, LIGHT_GREY, DARK_GREY, font, small_font,
                       draw_text, draw_rounded_rect, fmt)

EXPECTED = {"royal": 3, "noble": 2}      # duties a year that keep approval steady (adults)

# id: (label, min_age, stations, approval, stats, money, note)
DUTIES = [
    ("parade", "Wave from the balcony at a parade", 6, ("royal",), 2, {"social": 1}, 0, "The crowd cheered when you waved."),
    ("school_visit", "Visit a school with the family", 10, ("royal", "noble"), 2, {"social": 1}, 0, "The pupils had a lot of questions for you."),
    ("engagement", "Carry out an official engagement", 18, ("royal",), 4, {"social": 2, "mental": -1}, 0, "You opened a new hospital wing and shook a hundred hands."),
    ("patronage", "Champion a charity as patron", 18, ("royal", "noble"), 4, {"mental": 2}, -2000, "Your patronage brought the charity record donations."),
    ("tour", "Go on a royal tour abroad", 21, ("royal",), 6, {"social": 3, "physical": -2}, 0, "The tour was a diplomatic success, if exhausting."),
    ("military", "Serve a term with the armed forces", 18, ("royal",), 5, {"physical": 4, "athletic": 2, "mental": -1}, 0, "You completed your service with honours."),
    ("audiences", "Hold audiences with the Prime Minister", 18, ("monarch",), 4, {"academic": 2}, 0, "The weekly audience went well. You were well briefed."),
    ("state_open", "Open Parliament", 18, ("monarch",), 6, {"social": 2}, 0, "You read the speech from the throne without a stumble."),
    ("estate", "Manage the family estate", 18, ("noble",), 2, {"academic": 1}, 6000, "The harvest and the rents came in well."),
    ("ball", "Host a society ball", 18, ("noble",), 3, {"social": 3, "looks": 1}, -5000, "Your ball was the talk of the season."),
    ("lords", "Take your seat in the House of Lords", 25, ("peer",), 3, {"academic": 2}, 0, "You spoke in a debate and were quoted in the papers."),
    ("open_house", "Open the estate to visitors", 18, ("noble",), 2, {"social": 1}, 3000, "Coach parties toured the house all summer."),
]
_DUTY = {d[0]: d for d in DUTIES}


def station(state):
    """'royal', 'noble', 'former_royal' or None."""
    s = state.get("station")
    if s:
        return s
    t = state.get("title")
    if t and t["kind"] in ("king", "prince"):
        return "royal"
    if (t and t["kind"] == "peer") or (state.get("heir_to") or {}).get("kind") == "peer":
        return "noble"
    return None

def is_monarch(state):
    return (state.get("title") or {}).get("kind") == "king"

def approval(state):
    return state.setdefault("approval", 60)

def change_approval(state, d):
    state["approval"] = max(0, min(100, approval(state) + d))

def blocks_jobs(state):
    return station(state) == "royal"

def setup(state, scenario_id):
    """Called when a life starts from a scenario."""
    if scenario_id in ("royal1", "royal2"):
        state["station"] = "royal"
        state["approval"] = 62 if scenario_id == "royal2" else 55
    elif scenario_id == "noble":
        state["station"] = "noble"
        state["approval"] = 60

def available_duties(state):
    st, age = station(state), state.get("age", 0)
    done = state.setdefault("duties_done", [])
    out = []
    for d in DUTIES:
        did, label, min_age, who = d[0], d[1], d[2], d[3]
        ok = (st in who or ("monarch" in who and is_monarch(state) and st == "royal")
              or ("peer" in who and (state.get("title") or {}).get("kind") == "peer"))
        if ok and age >= min_age and did not in done:
            out.append(d)
    return out

def do_duty(state, did, log):
    d = _DUTY[did]
    _, label, _, _, appr, fx, money, note = d
    stats = state["stats"]
    for k, v in fx.items():
        stats[k] = max(0, min(100, stats[k] + v))
    if money:
        state["money"] = max(0, state["money"] + money)
    if approval(state) > 75:
        appr = max(1, appr // 2)      # goodwill is harder to win once you're already popular
    change_approval(state, appr)
    state.setdefault("duties_done", []).append(did)
    log(f"{note} (+{appr} approval)")


# ---------------------------------------------------------------- yearly upkeep
def year(state, career, people, log):
    st = station(state)
    age = state.get("age", 0)
    done = len(state.get("duties_done", []))
    if st in EXPECTED and age >= 18:
        need = EXPECTED[st] + (1 if is_monarch(state) else 0)
        if done < need:
            drop = (need - done) * (4 if st == "royal" else 1)
            change_approval(state, -drop)
            if done == 0:
                log("The papers asked where you'd been all year. Your approval slipped." if st == "royal"
                    else "The estate was neglected this year, and the tenants noticed.")
        elif done > need:
            change_approval(state, 1)
        # opinion drifts back toward the middle over time
        a = approval(state)
        change_approval(state, -3 if a > 80 else (-1 if a > 65 else (2 if a < 40 else 0)))
    if st == "royal":
        career["fame"] = max(career.get("fame", 0), 45 if age >= 18 else 25)
        career["job"] = None
    if st == "noble" and (state.get("flags") or {}).get("estate_open"):
        state["money"] += 12000
    if st == "noble" and age >= 18 and not state.get("title"):
        state["money"] += int(20000 * income_factor(state))     # an heir's allowance from the estate
    state["duties_done"] = []

def income_factor(state):
    """Stipends and estate income follow public approval."""
    st = station(state)
    if st == "former_royal":
        return 0.0
    if st in ("royal", "noble"):
        return 0.5 + approval(state) / 100
    return 1.0

def snapshot_rows(state):
    st = station(state)
    if st == "royal":
        return [("Approval", f"{approval(state)}%")]
    if st == "noble":
        return [("Standing", f"{approval(state)}%")]
    return []

def home_label(state):
    return {"royal": "Royal residence", "noble": "Family estate"}.get(station(state))

def job_label(state, age):
    st = station(state)
    if st == "royal":
        return "Monarch" if is_monarch(state) else ("Royal duties" if age >= 18 else "Royal (in school)")
    return None


# ---------------------------------------------------------------- the Duties panel
def draw_duties(screen, rect, mouse, state, career):
    st = station(state)
    age = state.get("age", 0)
    no_budget = state["actions_remaining"] <= 0
    buttons = {"_station": True, "duties": []}
    head = "Royal duties" if st == "royal" else "Estate & society"
    draw_text(screen, head, font, INK, rect.x, rect.y)
    a = approval(state)
    bar = pygame.Rect(rect.x + 230, rect.y + 6, 200, 14)
    draw_rounded_rect(screen, LIGHT_GREY, bar, radius=7)
    colr = (90, 180, 120) if a >= 60 else ((230, 180, 70) if a >= 40 else (220, 90, 90))
    draw_rounded_rect(screen, colr, (bar.x, bar.y, max(6, int(bar.w * a / 100)), bar.h), radius=7)
    draw_text(screen, f"{'Approval' if st == 'royal' else 'Standing'} {a}%", small_font, INK, bar.right + 10, rect.y + 3)
    need = EXPECTED.get(st, 0) + (1 if is_monarch(state) else 0)
    done = len(state.get("duties_done", []))
    if age >= 18:
        sub = (f"Duties this year: {done} of the {need} the public expects. "
               + ("Your stipend follows your approval." if st == "royal" else "Estate income follows your standing."))
    else:
        sub = "You're too young for full duties, but the family brings you along to some."
    draw_text(screen, sub, small_font, MUTED, rect.x, rect.y + 30)
    y = rect.y + 60
    duties = available_duties(state)
    if not duties:
        draw_text(screen, "Nothing else on the calendar this year.", small_font, DARK_GREY, rect.x, y)
    for n, d in enumerate(duties[:8]):
        r = pygame.Rect(rect.x + (n % 2) * 340, y + (n // 2) * 50, 330, 44)
        hov = r.collidepoint(mouse) and not no_budget
        draw_rounded_rect(screen, (255, 236, 218) if hov else WHITE, r, radius=8)
        pygame.draw.rect(screen, OUTLINE, r, 1, border_radius=8)
        draw_text(screen, d[1], small_font, INK if not no_budget else DARK_GREY, r.x + 10, r.y + 5)
        extra = f"+{d[4]} {'approval' if st == 'royal' else 'standing'}" + (f", ${fmt(abs(d[6]))} {'in' if d[6] > 0 else 'cost'}" if d[6] else "")
        draw_text(screen, extra, small_font, MUTED, r.x + 10, r.y + 24)
        buttons["duties"].append((d[0], r))
    by = y + 4 * 50 + 6
    if st == "royal":
        if age >= 18:
            sb = pygame.Rect(rect.x, by, 260, 32)
            draw_rounded_rect(screen, (250, 228, 228) if sb.collidepoint(mouse) else WHITE, sb, radius=8)
            pygame.draw.rect(screen, (200, 110, 110), sb, 1, border_radius=8)
            draw_text(screen, "Step back from royal life", small_font, (170, 60, 60), sb.centerx, sb.centery, centre=True)
            buttons["step_back"] = sb
            draw_text(screen, "Royals can't take ordinary jobs. Stepping back ends your stipend,", small_font, DARK_GREY, rect.x, by + 42)
            draw_text(screen, "but you'll be free to work like anyone else.", small_font, DARK_GREY, rect.x, by + 60)
    else:
        wb = pygame.Rect(rect.x, by, 200, 32)
        draw_rounded_rect(screen, ACCENT if wb.collidepoint(mouse) else WHITE, wb, radius=8)
        pygame.draw.rect(screen, OUTLINE, wb, 1, border_radius=8)
        draw_text(screen, "Ordinary work & fame", small_font, INK, wb.centerx, wb.centery, centre=True)
        buttons["to_work"] = wb
    return buttons

def handle_duties_click(mx, my, buttons, state, career, log):
    if buttons.get("step_back") and buttons["step_back"].collidepoint(mx, my):
        log(step_back(state))
        career["view"] = "work"
        return
    if buttons.get("to_work") and buttons["to_work"].collidepoint(mx, my):
        career["view"] = "work"
        return
    if state["actions_remaining"] <= 0:
        return
    for did, r in buttons["duties"]:
        if r.collidepoint(mx, my):
            do_duty(state, did, log)
            state["actions_remaining"] -= 1
            return

def step_back(state):
    state["station"] = "former_royal"
    state.pop("heir_to", None)
    change_approval(state, -10)
    state.setdefault("flags", {})["stepped_back"] = True
    return "You stepped back from royal life. No more stipend and no more duties, but you're free to work."


# ---------------------------------------------------------------- storylines
def _flags(state):
    return state.setdefault("flags", {})

def a_royal(state, arg):
    """The one act behind every station storyline: arg is a dict of effects."""
    arg = arg or {}
    notes = []
    if "approval" in arg:
        change_approval(state, arg["approval"])
    if "cash" in arg:
        state["money"] = max(0, state["money"] + arg["cash"])
    for k in arg.get("flags", ()):
        _flags(state)[k] = True
    do = arg.get("do")
    people = state.get("_people", [])
    partner = state.get("_partner")
    career = state.get("_career", {})
    if do == "step_back":
        notes.append(step_back(state))
    elif do == "abdicate":
        state["title"] = {"kind": "prince"}
        state["station"] = "former_royal"
        heir = next((p for p in people if p.get("is_child")), None)
        notes.append(f"You abdicated. {heir['name'] + ' is' if heir else 'Your heir is'} now on the throne.")
    elif do == "vet_partner":
        if partner and approval(state) >= 45 and partner.get("stats", {}).get("social", 50) >= 35:
            partner["closeness"] = min(100, partner["closeness"] + 8)
            _flags(state)["partner_approved"] = True
            notes.append(f"The palace gave its blessing to you and {partner['name']}.")
        elif partner:
            partner["closeness"] = max(0, partner["closeness"] - 10)
            change_approval(state, -3)
            notes.append(f"The palace advised against {partner['name']}. Things are tense between you.")
    elif do == "family_job":
        import career as C
        title, pay = arg.get("job", ("Executive Trainee", 60000))
        tpl = C.J(title, 18, "None", pay, 10)
        career["job"] = C._new_job(tpl, state)
        notes.append(f"You joined the family business as {title} on ${fmt(pay)} a year.")
    elif do == "boarding":
        if not state.get("private_school"):
            state["private_school"] = "boarding"
            notes.append("You started at the boarding school.")
    elif do == "fame":
        career["fame"] = min(100, career.get("fame", 0) + arg.get("amount", 10))
    elif do == "estate_open":
        _flags(state)["estate_open"] = True
        notes.append("The estate now opens to paying visitors every summer.")
    elif do == "sell_land":
        state["money"] += 400000
        notes.append("You sold the home farm. The estate is smaller, but the debts are gone.")
    elif do == "death_duties":
        bill = arg.get("bill", 300000)
        if state["money"] >= bill:
            state["money"] -= bill
            notes.append(f"You paid ${fmt(bill)} in inheritance tax.")
        else:
            state["money"] = 0
            change_approval(state, -6)
            notes.append("You couldn't cover the tax bill. The family paintings went to auction.")
    for k, v in arg.get("stats", {}).items():
        state["stats"][k] = max(0, min(100, state["stats"][k] + v))
    if "approval" in arg and station(state) in ("royal", "noble"):
        notes.append(f"{'Approval' if station(state) == 'royal' else 'Standing'} is now {approval(state)}%.")
    return " ".join(notes)

def R(**kw):
    return {"act": ("royal", kw)}

def _story(state, ctx, age):
    """All storyline beats that could fire this year, as (id, text, options)."""
    st, f = station(state), _flags(state)
    sc = state.get("scenario")
    partner = ctx.get("partner")
    pn = partner["name"] if partner else ""
    beats = []
    def add(bid, text, opts, cond=True):
        if cond and not f.get("seen_" + bid):
            beats.append((bid, text, opts))

    if st == "royal":
        add("kid_parade", "The palace wants you on the balcony for the anniversary parade. You'd rather stay inside and play.",
            {"Smile and wave": dict(R(approval=3), social=1), "Sulk in the back row": dict(R(approval=-2), mental=1)}, 6 <= age <= 11)
        add("school", "Time to choose a school: the traditional boarding school, or the local school like everyone else?",
            {"Boarding school": dict(R(approval=3, flags=["boarding"], do="boarding"), academic=3, social=-1),
             "The local school": dict(R(approval=-1, flags=["local_school"]), social=3)}, 11 <= age <= 13)
        add("first_engagement", "Your first official engagement: opening a children's hospital, cameras everywhere.",
            {"Embrace it": dict(R(approval=6, flags=["dutiful"]), social=2, mental=-1),
             "Get through it nervously": dict(R(approval=2), mental=-2),
             "Refuse to go": dict(R(approval=-8, flags=["rebel"]), mental=2)}, 18 <= age <= 20)
        add("military", "Royal tradition says you serve with the armed forces for a few years.",
            {"Serve": dict(R(approval=8, flags=["served"]), physical=5, athletic=3, mental=-2),
             "Decline and go to university": dict(R(approval=-4), academic=3)}, 19 <= age <= 24)
        add("spare", "The press call your sibling 'the future' and you 'the spare'. It stings.",
            {"Support your sibling publicly": dict(R(approval=5), mental=-1),
             "Carve out your own cause": dict(R(approval=3, flags=["own_cause"]), mental=2),
             "Give a candid interview": dict(R(approval=-6, flags=["candid"]), mental=4)}, sc == "royal2" and 20 <= age <= 35)
        add("vet_partner", f"The palace wants to vet your relationship with {pn} before it goes any further.",
            {"Ask for the palace's blessing": R(do="vet_partner"),
             "Keep it private and hope": dict(R(approval=-2), mental=-1),
             f"Choose {pn} over the palace": dict(R(approval=-10, flags=["defiant"]), mental=3)}, bool(partner) and age >= 20)
        add("wedding", f"Your wedding to {pn} will be a national event. How big should it be?",
            {"A full state wedding": dict(R(approval=10, flags=["state_wedding"]), social=3),
             "Small and private": dict(R(approval=-4), mental=4)}, bool(partner and partner.get("married")))
        add("stand_in", "The monarch is unwell and asks you to stand in at the state opening of Parliament.",
            {"Step up": dict(R(approval=8), social=2, mental=-2), "Ask someone else to go": R(approval=-6)},
            (state.get("heir_to") or {}).get("kind") == "king" and age >= 25)
        add("coronation", "The coronation. Robes, oaths, and the weight of a crown on your head.",
            {"Promise to serve your whole life": dict(R(approval=10, flags=["crowned"]), mental=-2),
             "Promise a modern, smaller monarchy": dict(R(approval=6, flags=["crowned", "modern"]), mental=1)}, is_monarch(state))
        add("crisis", "The government asks you to sign a law that divides the country. By tradition you can't refuse.",
            {"Sign it, as tradition demands": R(approval=-3), "Delay and ask for advice": dict(R(approval=2), academic=1)},
            is_monarch(state) and age >= 30 and f.get("crowned"))
        add("abdicate", "Your heir is grown and ready. Is it time to hand over the crown?",
            {"Abdicate in their favour": R(do="abdicate", approval=5), "Reign on": dict(R(approval=1), mental=-1)},
            is_monarch(state) and age >= 70 and any(p.get("is_child") and p.get("age", 0) >= 30 for p in ctx.get("people", [])))
        if age >= 18 and random.random() < 0.35:
            scandal = random.choice(["A tabloid prints photos of you at a party you'd rather forget.",
                                     "A former friend sells a story about you to the papers.",
                                     "An old social media post of yours resurfaces and goes viral."])
            beats.append(("~scandal", scandal,
                          {"Issue a calm statement": R(approval=-2), "Say nothing": R(approval=-5),
                           "Give a heartfelt interview": {"gamble": [dict(R(approval=6), mental=1), dict(R(approval=-9), mental=-3)]}}))
    elif st == "former_royal":
        add("memoir", "Publishers are bidding for your memoir about life inside the palace.",
            {"Tell everything": dict(R(cash=900000, approval=-12, flags=["memoir"]), mental=2),
             "A gentle, careful book": R(cash=250000, approval=2), "No book": dict(R(approval=3), mental=-1)}, age >= 25)
        add("invite_back", "The palace invites you back for a family occasion, the first since you left.",
            {"Go and make peace": dict(R(approval=6), mental=3), "Stay away": dict(R(approval=-2), mental=-1)},
            f.get("stepped_back") and age >= 22)
    elif st == "noble":
        add("debut", "Your debut at the first ball of the season. Every family in the county is watching.",
            {"Dance all night": dict(R(approval=3), social=3, looks=1), "Hide by the buffet": dict(R(approval=-1), mental=1)}, 16 <= age <= 19)
        add("intro", "Your family arranges an 'introduction' to the heir of another old family.",
            {"Go along with it": dict(R(approval=3, cash=20000), social=1), "Refuse politely": dict(R(approval=-1), mental=2)},
            not partner and 20 <= age <= 32)
        add("roof", "The roof of the old house is failing. Repairs will cost a fortune.",
            {"Pay for it": dict(R(cash=-150000, approval=2), mental=-1),
             "Open the estate to paying visitors": R(do="estate_open", approval=1),
             "Sell the home farm": R(do="sell_land", approval=-4)}, age >= 24)
        add("death_duties", "The inheritance tax bill on the family estate has arrived. It's enormous.",
            {"Pay it": R(do="death_duties", bill=300000), "Sell a painting to cover it": R(cash=-50000, approval=-2),
             "Contest it in court": {"gamble": [R(cash=100000, approval=-3), R(do="death_duties", bill=420000)]}},
            (state.get("title") or {}).get("kind") == "peer" and not (state.get("heir_to")))
        add("tenants", "Your tenant farmers ask for a rent cut after a bad harvest.",
            {"Cut the rents": R(cash=-30000, approval=6), "Refuse": R(approval=-6)}, age >= 25)
    else:
        if sc == "tycoon":
            add("family_firm", "Your parent offers you a place in the family company.",
                {"Take it": R(do="family_job", job=("Executive Trainee", 65000)), "Make your own way": dict(R(), mental=3, social=1)}, 18 <= age <= 24)
            add("succession", "The board wants to know: will you take over the family company one day?",
                {"Yes, groom me for it": dict(R(do="family_job", job=("Managing Director", 220000)), mental=-3),
                 "Sell my share": dict(R(cash=1500000), mental=2)}, 35 <= age <= 50 and bool((ctx.get("career") or {}).get("job")))
        elif sc == "stars":
            add("casting", "A casting director wants you for a film, mostly because of your famous parents.",
                {"Take the role": dict(R(do="fame", amount=15), looks=1), "Turn it down": dict(R(), mental=2)}, 10 <= age <= 17)
            add("nepo", "Online, people call you a 'nepo baby'. It's everywhere this week.",
                {"Laugh along": dict(R(do="fame", amount=5), social=2), "Prove them wrong with hard work": academic_or(3)}, 16 <= age <= 30)
        elif sc == "sport":
            add("academy", "Your parents want you at an elite sports academy, training six days a week.",
                {"Go to the academy": dict(athletic=6, physical=3, academic=-2), "Stay at a normal school": dict(social=2, academic=2)}, 11 <= age <= 14)
        elif sc == "doctor":
            add("medicine", "Your parents expect you to apply for medicine. They've already told everyone.",
                {"Apply for medicine": dict(academic=3, mental=-3), "Choose your own subject": dict(mental=3, social=1)}, 16 <= age <= 18)
        elif sc == "blessed_poor":
            add("scout", "A scholarship scout from a top school has noticed you.",
                {"Apply for the scholarship": {"gamble": [dict(R(cash=0), academic=5), dict(mental=-2)]}, "Stay with your friends": dict(social=3)}, 12 <= age <= 16)
    return beats

def academic_or(n):
    return {"academic": n, "mental": -1}

def story_event(state, ctx, age, chance=0.75):
    """One storyline beat for this year, or None. Marks it as seen."""
    beats = _story(state, ctx, age)
    if not beats or random.random() > chance:
        return None
    bid, text, opts = beats[0] if beats[0][0] != "scandal" or len(beats) == 1 else random.choice(beats)
    if bid != "scandal":
        _flags(state)["seen_" + bid] = True
    return text, opts

def install():
    import lifeevents
    lifeevents.ACTS["royal"] = a_royal
