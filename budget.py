"""Money and housing: where you rent, yearly bills, debt that piles up when
you can't pay, and a Budget view of income against expenses."""
import random
import pygame
from constants import (WHITE, INK, MUTED, OUTLINE, ACCENT, GREEN, LIGHT_GREY, DARK_GREY, font, small_font,
                       draw_text, draw_rounded_rect, draw_pill, fmt)
from stories import S, with_

# id, name, rent a year, yearly stat effects
RENTALS = [("shared", "Shared house", 4800, {"social": 1, "mental": -1}),
           ("studio", "Studio flat", 7200, {}),
           ("city", "City apartment", 14400, {"mental": 1}),
           ("luxury", "Luxury apartment", 36000, {"mental": 2, "looks": 1})]
_RENTAL = {r[0]: r for r in RENTALS}
BILLS = 2400            # utilities, phone and internet
GROCERIES = 3000
MOVE_FEE = 800

def rental(state):
    return _RENTAL.get(state.get("rental", "studio"), _RENTAL["studio"])

def living(state, age):
    """'child', 'parents', 'free' (royal / estate), 'owner', 'jail' or 'renting'."""
    if age < 18:
        return "child"
    if state.get("jail"):
        return "jail"
    if state.get("station") in ("royal", "noble"):
        return "free"
    if state.get("home"):
        return "owner"
    from life import LIVE_WITH_PARENTS_UNTIL
    if age < LIVE_WITH_PARENTS_UNTIL and state.get("parents_ok"):
        return "parents"
    return "renting"

def housing_costs(state, age):
    """(rent, bills) this year."""
    how = living(state, age)
    if how in ("child", "jail", "parents", "free"):
        return 0, 0
    rent = rental(state)[2] if how == "renting" else 0
    return rent, BILLS + GROCERIES

def pay(state, amount, what, log):
    """Pay a bill; whatever you can't cover goes on a credit card (debt)."""
    if amount <= 0:
        return
    if state["money"] >= amount:
        state["money"] -= amount
        return
    short = amount - state["money"]
    state["money"] = 0
    state["debt"] = state.get("debt", 0) + short
    state["stats"]["mental"] = max(0, state["stats"]["mental"] - 2)
    log(f"You couldn't cover your {what}: ${fmt(short)} went on a credit card.")

def year(state, age, log):
    """Rent, bills and debt pressure. Replaces the old flat rent."""
    how = living(state, age)
    rent, bills = housing_costs(state, age)
    pay(state, rent, "rent", log)
    pay(state, bills, "bills", log)
    if how == "renting":
        for k, v in rental(state)[3].items():
            state["stats"][k] = max(0, min(100, state["stats"][k] + v))
    debt = state.get("debt", 0)
    income = state.get("_income", 0) + state.get("endorse_last", 0)
    state["_debt_pressure"] = age >= 18 and debt > max(20000, income * 2)
    if state["_debt_pressure"]:
        state["stats"]["mental"] = max(0, state["stats"]["mental"] - 2)

def move_to(state, rid, log):
    r = _RENTAL[rid]
    state["rental"] = rid
    state["money"] = max(0, state["money"] - MOVE_FEE)
    log(f"You moved into a {r[1].lower()} (${fmt(r[2])} a year).")


# ---------------------------------------------------------------- projections
def projection(state, career, age, people):
    """This year's expected money in and out, as two lists of (label, amount)."""
    import titles, station, assets
    inc, out = [], []
    job, side, hustle = career.get("job"), career.get("side_job"), career.get("hustle")
    if job: inc.append(("Salary", job["pay"]))
    if side: inc.append(("Part-time job", side["pay"]))
    if hustle: inc.append(("Side career", hustle["pay"] // 2))
    t = state.get("title")
    if t and age >= 18:
        base = titles.INCOME.get(t["kind"], 0) * (1 + t.get("rank", 0) * 0.5 if t["kind"] == "peer" else 1)
        amt = int(base * station.income_factor(state))
        if amt:
            inc.append(("Royal stipend" if t["kind"] in ("king", "prince") else "Estate income", amt))
    import idol
    if idol.last_pay(state):
        inc.append(("Idol earnings", idol.last_pay(state)))
    if state.get("endorse_last"):
        inc.append(("Endorsements", state["endorse_last"]))
    rents = sum(int(p["value"] * 0.055 * 0.88) for p in state.get("properties", []) if p.get("rented"))
    if rents: inc.append(("Rental income", rents))
    if state.get("savings"): inc.append(("Savings interest", int(state["savings"] * 0.03)))
    if state.get("pension") and age >= 66: inc.append(("Pension", state["pension"]))
    rent, bills = housing_costs(state, age)
    if rent: out.append((f"Rent ({rental(state)[1].lower()})", rent))
    if bills: out.append(("Bills & groceries", bills))
    up = sum(int(p["value"] * (0.004 if p.get("live") else 0.008)) for p in state.get("properties", []))
    if up: out.append(("Property upkeep", up))
    cars = sum(c["bought"] // 40 for c in state.get("cars", []))
    if cars: out.append(("Car costs", cars))
    from people import CHILD_COST
    kids = sum(1 for p in people if p.get("is_child") and p.get("age", 0) < 18)
    if kids: out.append((f"Children ({kids})", CHILD_COST * kids))
    if state.get("pets") and age >= 18: out.append(("Pets", 300 * len(state["pets"])))
    fund = career.get("funding") or {}
    if career.get("enrolled") and fund.get("owe"): out.append(("Tuition", fund["owe"]))
    if state.get("debt"): out.append(("Debt interest", int(state["debt"] * 0.05)))
    return inc, out

def draw_budget(screen, rect, mouse, state, career, age, people):
    hits = []
    inc, out = projection(state, career, age, people)
    ti, to = sum(v for _, v in inc), sum(v for _, v in out)
    draw_text(screen, "Budget", font, INK, rect.x, rect.y)
    net = ti - to
    draw_text(screen, f"{'+' if net >= 0 else '-'}${fmt(abs(net))} a year", font, GREEN if net >= 0 else (200, 70, 70), rect.x + 110, rect.y)
    draw_text(screen, f"Cash ${fmt(state['money'])}   Debt ${fmt(state.get('debt', 0))}", small_font, MUTED, rect.x + 300, rect.y + 6)
    colw = (rect.width - 20) // 2
    top = max(ti, to, 1)
    for ci, (title, rows, col) in enumerate((("Money in", inc, (90, 170, 120)), ("Money out", out, (220, 110, 100)))):
        x, y = rect.x + ci * (colw + 20), rect.y + 36
        card = pygame.Rect(x, y, colw, 230)
        draw_rounded_rect(screen, WHITE, card, radius=12)
        pygame.draw.rect(screen, OUTLINE, card, 1, border_radius=12)
        tot = sum(v for _, v in rows)
        draw_text(screen, f"{title}: ${fmt(tot)}", small_font, INK, x + 12, y + 10)
        if not rows:
            draw_text(screen, "Nothing yet.", small_font, DARK_GREY, x + 12, y + 40)
        for n, (lab, v) in enumerate(rows[:8]):
            ry = y + 36 + n * 24
            draw_text(screen, lab, small_font, INK, x + 12, ry)
            draw_text(screen, f"${fmt(v)}", small_font, MUTED, x + colw - 90, ry)
            bar = pygame.Rect(x + 170, ry + 6, colw - 270, 8)
            draw_rounded_rect(screen, LIGHT_GREY, bar, radius=4)
            draw_rounded_rect(screen, col, (bar.x, bar.y, max(4, int(bar.w * v / top)), bar.h), radius=4)
    y = rect.y + 280
    how = living(state, age)
    note = {"child": "You live at home with your family.", "parents": "You still live with your parents: no rent.",
            "free": "You live in the family residence: no rent.", "jail": "You're in prison."}.get(how)
    if how == "owner":
        note = f"You own your home: {state['home']['name']}."
    if note:
        draw_text(screen, note, small_font, MUTED, rect.x, y)
    else:
        draw_text(screen, "Where you rent (moving costs $" + fmt(MOVE_FEE) + " and one action):", small_font, INK, rect.x, y)
        cur = rental(state)[0]
        bw = (rect.width - 30) // 4
        for n, (rid, name, rent, fx) in enumerate(RENTALS):
            r = pygame.Rect(rect.x + n * (bw + 10), y + 24, bw, 70)
            on = rid == cur
            draw_rounded_rect(screen, ACCENT if on else ((255, 236, 218) if r.collidepoint(mouse) else WHITE), r, radius=10)
            pygame.draw.rect(screen, OUTLINE, r, 1, border_radius=10)
            draw_text(screen, name, small_font, WHITE if on else INK, r.x + 10, r.y + 7)
            draw_text(screen, f"${fmt(rent)} a year", small_font, WHITE if on else MUTED, r.x + 10, r.y + 27)
            eff = ", ".join(f"{'+' if v > 0 else ''}{v} {k}" for k, v in fx.items()) or "no effect"
            draw_text(screen, eff, small_font, WHITE if on else MUTED, r.x + 10, r.y + 46)
            if not on:
                hits.append((rid, r))
    if state.get("_debt_pressure"):
        draw_text(screen, "Your debt is more than twice your income. It's weighing on you (Mental -2 a year).",
                  small_font, (200, 70, 70), rect.x, y + 106)
    return {"move": hits}

def handle_budget_click(mx, my, hits, state, log):
    if state["actions_remaining"] <= 0:
        return
    for rid, r in hits.get("move", []):
        if r.collidepoint(mx, my):
            move_to(state, rid, log)
            state["actions_remaining"] -= 1
            return


# ---------------------------------------------------------------- stories
def _set_rental(rid):
    def fn(state):
        state["rental"] = rid
        return f"You moved into a {_RENTAL[rid][1].lower()}."
    return fn

def _debt_help(state):
    if state.get("parents_ok") and state.get("family_wealth") in ("Comfortable", "Wealthy", "Elite", "Royalty"):
        cut = state.get("debt", 0) // 2
        state["debt"] -= cut
        return f"Your family paid off ${fmt(cut)} of your debt."
    return "Your family couldn't help this time."

def _repay_plan(state):
    pay_now = min(state["money"], state.get("debt", 0) // 3)
    state["money"] -= pay_now
    state["debt"] -= pay_now
    return f"You paid ${fmt(pay_now)} off your debt and agreed a plan for the rest."

def beats(state, ctx, age):
    out = []
    how = living(state, age)
    if how == "renting" and 18 <= age <= 30 and not state.get("rental"):
        out.append(("first_place", "Time to find a place of your own. Where will you live?",
                    {f"{n} (${fmt(r)}/yr)": S(fn=_set_rental(rid)) for rid, n, r, _ in RENTALS}))
    if state.get("_debt_pressure"):
        out.append(("~debt", f"Debt collectors keep calling about the ${fmt(state.get('debt', 0))} you owe.",
                    {"Set up a repayment plan": with_(S(fn=_repay_plan), mental=1),
                     "Ask your family for help": S(fn=_debt_help),
                     "Ignore the calls": {"mental": -3}}))
    if how == "renting" and age >= 20 and random.random() < 0.12:
        out.append(("~landlord", "Your landlord announces a rent rise and a list of 'house rules'.",
                    {"Grumble and pay": {"mental": -1}, "Negotiate": {"gamble": [{"mental": 1}, {"mental": -2}]},
                     "Start looking for somewhere else": {"mental": 1}}))
    return out
