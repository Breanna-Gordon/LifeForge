from constants import fmt
import random

# Everyday money and health, run once a year. Children never pay for
# anything: their family covers it.
RENT = 6000
LIVE_WITH_PARENTS_UNTIL = 24
RETIRE_AGE = 67
STATE_PENSION = 9000

def _log(state, text):
    state["journal"].append((state["age"], text))

def yearly_costs(state, career, age, parents_ok):
    """Rent (unless you own a home or still live with your parents), home
    value growth, and a small yearly comfort boost from owning a home."""
    stats = state["stats"]
    home = state.get("home")
    if home:
        stats["mental"] = min(100, stats["mental"] + 1)
        return
    if age < 18:
        return
    if age < LIVE_WITH_PARENTS_UNTIL and parents_ok:
        return                      # still at the family home
    if state["money"] >= RENT:
        state["money"] -= RENT
    else:
        paid = state["money"]
        state["money"] = 0
        stats["mental"] = max(0, stats["mental"] - 2)
        stats["wealth"] = max(0, stats["wealth"] - 2)
        _log(state, f"You could only pay ${fmt(paid)} of your ${fmt(RENT)} rent. It was a stressful year.")

def health_year(state, age):
    """Illness and injury. Adults pay the bill; children don't."""
    stats = state["stats"]
    if "check" in state.get("bought_this_year", ()):
        return
    chance = 0.07 + max(0, 55 - stats["physical"]) / 250 + (0.04 if age >= 65 else 0)
    if random.random() >= chance:
        return
    what = random.choice(["a nasty flu", "a sports injury", "a stomach bug", "a bad infection", "a broken bone"])
    stats["physical"] = max(0, stats["physical"] - random.randint(3, 7))
    if age < 18:
        _log(state, f"You were ill with {what}. Your family sorted out the doctor.")
        return
    bill = random.randint(300, 2500)
    paid = min(bill, state["money"])
    state["money"] -= paid
    _log(state, f"You had {what} and paid ${fmt(paid)} in medical bills.")

def report_card(state, age):
    if not 6 <= age <= 17:
        return
    a = state["stats"]["academic"]
    grade = "A" if a >= 80 else "B" if a >= 65 else "C" if a >= 50 else "D" if a >= 35 else "F"
    if grade == "A":
        state["stats"]["mental"] = min(100, state["stats"]["mental"] + 1)
    elif grade in ("D", "F"):
        state["stats"]["mental"] = max(0, state["stats"]["mental"] - 1)
    _log(state, f"School report: grade {grade}.")

def invest_year(state):
    inv = state.get("invest", 0)
    if inv <= 0:
        return
    change = max(-0.5, min(0.8, random.gauss(0.05, 0.22)))
    new = max(0, int(round(inv * (1 + change))))
    state["invest"] = new
    pct = int(round(change * 100))
    _log(state, f"Your investments {'grew' if pct >= 0 else 'fell'} {abs(pct)}% (now ${fmt(new)}).")

def retirement_year(career, state, age):
    """At 67 you retire and draw a pension based on your last pay."""
    if age >= RETIRE_AGE and career["job"]:
        state["pension"] = max(state.get("pension", 0), career["job"]["pay"] // 2)
        _log(state, f"You retired from your job as {career['job']['title']}. Pension: ${fmt(state['pension'])} a year.")
        career["job"] = None
        career["side_job"] = None
    if age >= RETIRE_AGE:
        income = state.get("pension", STATE_PENSION)
        state["money"] += max(income, STATE_PENSION)
