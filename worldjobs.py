"""The working world around you.

Everyone you meet (parents, coworkers, partners, classmates when grown up)
has a job, and the job decides their stats and their money:
a surgeon has high Academic, an actor has high Looks and Social, a
footballer has high Athletic. Parents' jobs decide how rich your family is,
your pocket money, and how much they give when you ask."""
import random

STAT_KEYS = ["looks", "social", "academic", "athletic", "mental"]

# (title, yearly pay, stat profile centre, weight in the random pool)
PEOPLE_JOBS = [
    # health
    ("Surgeon", 260000, {"academic": 88, "mental": 70}, 1),
    ("Doctor", 150000, {"academic": 82, "mental": 65}, 3),
    ("Psychiatrist", 170000, {"academic": 84, "social": 62, "mental": 68}, 1),
    ("Dentist", 140000, {"academic": 76, "looks": 55}, 2),
    ("Pharmacist", 95000, {"academic": 74}, 2),
    ("Nurse", 56000, {"academic": 58, "social": 62, "mental": 60}, 5),
    ("Paramedic", 46000, {"athletic": 62, "mental": 60, "academic": 52}, 2),
    ("Physical Therapist", 70000, {"athletic": 64, "academic": 60}, 2),
    ("Vet", 88000, {"academic": 76, "social": 55}, 2),
    # law, finance, business
    ("Lawyer", 130000, {"academic": 80, "social": 66}, 3),
    ("Judge", 190000, {"academic": 86, "mental": 70}, 1),
    ("Accountant", 62000, {"academic": 68}, 4),
    ("Investment Banker", 210000, {"academic": 80, "social": 68, "looks": 58}, 2),
    ("Financial Advisor", 90000, {"academic": 68, "social": 64}, 3),
    ("Business Owner", 110000, {"social": 66, "academic": 60, "mental": 60}, 4),
    ("Company CEO", 420000, {"social": 74, "academic": 72, "looks": 62}, 1),
    ("Manager", 72000, {"social": 62, "academic": 60}, 6),
    ("Estate Agent", 58000, {"social": 70, "looks": 60}, 3),
    ("Salesperson", 42000, {"social": 66, "looks": 56}, 5),
    # tech, science, engineering
    ("Software Engineer", 105000, {"academic": 78, "mental": 55}, 4),
    ("Game Developer", 78000, {"academic": 70, "mental": 52}, 2),
    ("Data Scientist", 112000, {"academic": 82}, 2),
    ("Engineer", 84000, {"academic": 74, "athletic": 50}, 4),
    ("Architect", 88000, {"academic": 72, "looks": 58}, 2),
    ("Scientist", 82000, {"academic": 85, "mental": 55}, 2),
    ("Professor", 90000, {"academic": 88, "social": 56}, 2),
    ("Pilot", 135000, {"academic": 70, "mental": 68, "athletic": 55}, 2),
    # trades and service
    ("Electrician", 54000, {"athletic": 56, "academic": 52}, 4),
    ("Plumber", 52000, {"athletic": 58, "academic": 48}, 4),
    ("Builder", 48000, {"athletic": 68}, 5),
    ("Carpenter", 46000, {"athletic": 62}, 3),
    ("Mechanic", 46000, {"athletic": 58, "academic": 50}, 4),
    ("Chef", 44000, {"social": 55, "mental": 52, "athletic": 52}, 4),
    ("Hairdresser", 34000, {"looks": 66, "social": 68}, 4),
    ("Beautician", 34000, {"looks": 72, "social": 62}, 2),
    ("Shop Assistant", 25000, {"social": 55}, 6),
    ("Waiter", 24000, {"social": 62, "looks": 55}, 4),
    ("Taxi Driver", 31000, {"social": 55}, 3),
    ("Lorry Driver", 40000, {"athletic": 52, "mental": 50}, 3),
    ("Cleaner", 21000, {"athletic": 52}, 4),
    ("Farmer", 38000, {"athletic": 66, "mental": 60}, 2),
    ("Security Guard", 30000, {"athletic": 68}, 3),
    ("Police Officer", 52000, {"athletic": 70, "social": 58, "mental": 58}, 3),
    ("Firefighter", 50000, {"athletic": 80, "mental": 66}, 2),
    ("Soldier", 40000, {"athletic": 80, "mental": 62}, 2),
    # education, care, public
    ("Teacher", 48000, {"academic": 66, "social": 64, "mental": 58}, 6),
    ("Social Worker", 44000, {"social": 66, "mental": 60}, 3),
    ("Journalist", 52000, {"social": 66, "academic": 64}, 2),
    ("Politician", 120000, {"social": 78, "looks": 60, "academic": 62}, 1),
    ("Civil Servant", 46000, {"academic": 58}, 4),
    # creative and entertainment
    ("Actor", 95000, {"looks": 80, "social": 78}, 1),
    ("Model", 85000, {"looks": 92, "social": 66}, 1),
    ("Singer", 90000, {"social": 74, "looks": 72}, 1),
    ("Musician", 36000, {"social": 62, "mental": 52}, 2),
    ("Film Director", 150000, {"social": 72, "academic": 66, "mental": 62}, 1),
    ("Photographer", 38000, {"looks": 62, "social": 58}, 2),
    ("Graphic Designer", 50000, {"academic": 60, "looks": 56}, 3),
    ("Writer", 40000, {"academic": 70, "mental": 55}, 2),
    ("Influencer", 70000, {"looks": 80, "social": 82}, 2),
    ("DJ", 45000, {"social": 74, "looks": 64}, 1),
    ("Comedian", 60000, {"social": 82, "mental": 58}, 1),
    # sport
    ("Footballer", 320000, {"athletic": 90, "looks": 66, "social": 60}, 1),
    ("Basketball Player", 380000, {"athletic": 92, "social": 62}, 1),
    ("Boxer", 120000, {"athletic": 90, "mental": 62}, 1),
    ("Personal Trainer", 40000, {"athletic": 82, "looks": 68, "social": 60}, 2),
    ("Sports Coach", 52000, {"athletic": 72, "social": 64}, 2),
    # the very top
    ("Landowner", 480000, {"social": 58, "mental": 62}, 0.3),
    ("Duke / Duchess", 900000, {"social": 70, "looks": 64, "mental": 66}, 0.2),
    ("Royal Family Member", 2400000, {"social": 78, "looks": 66, "mental": 64}, 0.1),
]
BY_TITLE = {j[0]: j for j in PEOPLE_JOBS}
ROYAL = ("Royal Family Member",)

# the wealth tiers a family can be in, poorest first
TIERS = ["Struggling", "Comfortable", "Wealthy", "Elite", "Royalty"]

def tier_value(state_or_tier, table):
    """Look up a value that was written for the old three tiers. Elite
    families get 1.5x the Wealthy value and Royalty gets 3x (numbers) or
    the top value (chances)."""
    tier = state_or_tier if isinstance(state_or_tier, str) else state_or_tier.get("family_wealth", "Comfortable")
    if tier in table:
        return table[tier]
    top = table["Wealthy"]
    if isinstance(top, float) and top <= 1.0:
        return min(0.99, top + (0.03 if tier == "Elite" else 0.04))
    return top * (1.5 if tier == "Elite" else 3)

def household_pay(parents):
    return sum(p.get("fin", {}).get("pay", 0) for p in parents if p.get("alive", True) and not p.get("dead"))

def tier_for_pay(pay):
    if pay < 60000: return "Struggling"
    if pay < 150000: return "Comfortable"
    if pay < 350000: return "Wealthy"
    if pay < 1500000: return "Elite"
    return "Royalty"

def pick_job(age=30, bias=None):
    pool = [j for j in PEOPLE_JOBS]
    weights = [j[3] for j in pool]
    if bias:
        weights = [w * (3.0 if j[0] in bias else 1.0) for j, w in zip(pool, weights)]
    return random.choices(pool, weights=weights)[0]

def assign_job(p, job=None, rich_bias=False):
    """Give a grown-up a job, matching stats and a matching pay packet.
    Returns the job title."""
    if p.get("age", 30) < 18:
        return None
    if job is None:
        job = pick_job(p.get("age", 30))
    title, pay, profile, _ = job
    p["job_title"] = title
    p["stats"] = {k: max(5, min(98, int(random.gauss(profile.get(k, random.randint(38, 62)), 9)))) for k in STAT_KEYS}
    age = p.get("age", 30)
    seniority = 0.7 + 0.5 * min(1.0, max(0, age - 20) / 25)   # pay climbs with age
    pay = int(round(pay * seniority * random.uniform(0.85, 1.2), -2))
    if age >= 66:
        pay //= 2
    years = max(0, min(age, 66) - 22)
    p["fin"] = {"pay": pay, "savings": int(pay * years * random.uniform(0.05, 0.35)),
                "debt": random.choice([0, 0, 0, random.randint(2000, 30000)]) if age <= 38 else 0}
    return title

def occupation_text(p):
    a = p.get("age", 30)
    t = p.get("job_title", "office worker")
    t = t[0].upper() + t[1:]
    if a < 5: return "Too young for school"
    if a < 18: return "Student"
    if a >= 66: return "Retired " + t.lower()
    return t

# ---- money from the family ---------------------------------------------------
def pocket_money(state, parents, grandparents=()):
    """Yearly pocket money for a child: a slice of what the parents earn,
    plus the odd grandparent gift."""
    pay = household_pay(parents)
    base = max(60, int(pay * 0.004))
    gift = 0
    for g in grandparents:
        if random.random() < 0.35:
            gift += int(g.get("fin", {}).get("savings", 0) * 0.003)
    return base, gift

def ask_amount(person, age):
    """About how much a relative would hand over if you asked."""
    f = person.get("fin") or {}
    pay, sav = f.get("pay", 0), f.get("savings", 0)
    if age < 13:
        amt = pay * 0.0003
    elif age < 18:
        amt = pay * 0.0008
    else:
        amt = pay * 0.012 + sav * 0.01
    if person.get("relation", "").endswith(("Grandfather", "Grandmother")):
        amt = max(amt, sav * 0.006)
    cap = max(20, int(sav * 0.25 + pay * 0.05))
    return max(5, min(int(amt), cap))

def parents_of(people):
    return [p for p in people if p.get("relation") in ("Mother", "Father") and not p.get("dead")]

def grandparents_of(people):
    return [p for p in people if p.get("relation", "").endswith(("Grandfather", "Grandmother")) and not p.get("dead")]

def update_family_wealth(state, people):
    """Family wealth follows what the parents actually earn (royal jobs make
    a royal family). Returns the tier; writes it to `state` if a dict."""
    par = parents_of(people)
    if not par:
        return state.get("family_wealth", "Comfortable") if state else "Comfortable"
    for p in par:
        if p.get("age", 30) >= 18 and "fin" not in p:
            pass
    pay = household_pay(par)
    tier = "Royalty" if any(p.get("job_title") in ROYAL for p in par) else tier_for_pay(pay)
    if isinstance(state, dict):
        state["family_wealth"] = tier
    return tier

def stay_home(p):
    """A parent who looks after the home: no wage, but savings stay."""
    p["job_title"] = "Stay-at-home parent"
    p.setdefault("fin", {"pay": 0, "savings": 3000, "debt": 0})["pay"] = 0

# Career title -> the world jobs your colleagues might have
WORKPLACE = {
    "Doctor": ["Doctor", "Nurse", "Surgeon", "Paramedic", "Pharmacist"],
    "Surgeon": ["Surgeon", "Doctor", "Nurse"],
    "Nursing Assistant": ["Nurse", "Doctor", "Paramedic"],
    "Paramedic": ["Paramedic", "Nurse", "Firefighter"],
    "Lawyer": ["Lawyer", "Judge", "Civil Servant", "Accountant"],
    "Judge": ["Judge", "Lawyer"],
    "Teacher": ["Teacher", "Sports Coach", "Social Worker"],
    "University Professor": ["Professor", "Scientist"],
    "Software Engineer": ["Software Engineer", "Game Developer", "Data Scientist"],
    "Game Developer": ["Game Developer", "Software Engineer", "Graphic Designer"],
    "Actor": ["Actor", "Film Director", "Model", "Singer"],
    "Model": ["Model", "Photographer", "Actor", "Influencer"],
    "Singer": ["Singer", "Musician", "DJ", "Actor"],
    "Musician": ["Musician", "Singer", "DJ"],
    "Music Producer": ["DJ", "Musician", "Singer"],
    "Influencer": ["Influencer", "Photographer", "Model"],
    "Professional Athlete": ["Footballer", "Basketball Player", "Boxer", "Sports Coach", "Personal Trainer"],
    "Fitness Instructor": ["Personal Trainer", "Sports Coach"],
    "Sports Coach": ["Sports Coach", "Personal Trainer", "Teacher"],
    "Accountant": ["Accountant", "Financial Advisor", "Manager"],
    "Manager": ["Manager", "Salesperson", "Accountant", "Estate Agent"],
    "Engineer": ["Engineer", "Architect", "Builder", "Scientist"],
    "Architect": ["Architect", "Engineer", "Builder"],
    "Designer": ["Graphic Designer", "Photographer", "Architect"],
    "Chef": ["Chef", "Waiter"],
    "Electrician": ["Electrician", "Builder", "Plumber"],
    "Plumber": ["Plumber", "Builder", "Electrician"],
    "Mechanic": ["Mechanic", "Lorry Driver", "Engineer"],
    "Hairdresser": ["Hairdresser", "Beautician"],
    "Beautician": ["Beautician", "Hairdresser"],
    "Cashier": ["Shop Assistant", "Manager"],
    "Waiter": ["Waiter", "Chef"],
    "Police Officer": ["Police Officer", "Security Guard", "Social Worker"],
    "Firefighter": ["Firefighter", "Paramedic"],
    "Pilot": ["Pilot", "Engineer"],
}

def coworker_job(player_title):
    base = player_title
    for pre in ("Senior ", "Lead ", "Head of ", "Director of ", "Chief "):
        if base.startswith(pre):
            base = base[len(pre):]
    pool = WORKPLACE.get(base)
    if pool:
        title = random.choice(pool)
    elif base in BY_TITLE:
        title = base
    else:
        return pick_job()
    return BY_TITLE.get(title) or pick_job()
