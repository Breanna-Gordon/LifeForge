"""Career pathways: how talent turns into a career, and how careers lead into
each other.

  Sport   school team -> scouted -> athletic scholarship or pro academy
          -> college seasons -> draft -> pro -> coach or TV pundit
  Music   singing / music skills -> gigs, busking, viral covers -> record deal
          -> singer; idols -> solo, producer, actor or survival-show judge
  Screen  looks -> street scouting -> modelling -> acting crossover;
          drama club -> casting -> acting -> lead roles

state["path"] keeps the progress; "credits" (acting, modelling, songs) are a
portfolio that makes related jobs easier to get and better paid.
"""
import random
import pygame
from constants import (WHITE, INK, MUTED, OUTLINE, ACCENT, GREEN, LIGHT_GREY, DARK_GREY, font, small_font,
                       draw_text, draw_rounded_rect, fmt)
from stories import S, with_

_COLLEGES = ["State University", "Westbrook College", "Lakeshore University", "Northgate Institute", "Crestview University"]
_LABELS = ["Bluebird Records", "Sundial Music", "Hollow Oak Records", "Paper Moon Label", "Ironside Records"]
_DIRECTORS = ["Mara Quinn", "Theo Valdez", "Iris Holloway", "Ken Ashby", "Lena Brook"]


def P(state):
    p = state.setdefault("path", {})
    p.setdefault("interest", 0)            # how hard college and pro scouts are watching (0-100)
    p.setdefault("credits", {"acting": 0, "modelling": 0, "songs": 0})
    p.setdefault("seasons", 0)             # college seasons played
    p.setdefault("titles", 0)              # championships won at school or college
    return p

def credit(state, kind, n=1):
    c = P(state)["credits"]
    c[kind] = c.get(kind, 0) + n

def stars(state):
    i = P(state)["interest"]
    return 0 if i < 20 else 1 if i < 35 else 2 if i < 50 else 3 if i < 65 else 4 if i < 80 else 5

def _career(state):
    return state.get("_career") or {}

def _fame(state, n=0):
    c = _career(state)
    if n:
        c["fame"] = max(0, min(100, c.get("fame", 0) + n))
    return c.get("fame", 0)

def give_job(state, title, pay, fame=True, base=None):
    """Hand the player a job straight from a story (a contract, a deal, an offer)."""
    import career as C
    c = _career(state)
    job = {"title": title, "min_age": 16, "pay": int(pay), "wealth": 8, "fame": fame, "stats": {}, "skills": {},
           "courses": None, "any_of": None, "min_education": "None", "min_prestige": 0}
    if c.get("job"):
        C.cv_save(state, c["job"])
    c["job"] = C._new_job(job, None)
    if base:
        c["job"]["base"] = base
    return c["job"]

def give_hustle(state, title):
    import career as C
    h = next((h for h in C.HUSTLES if h["title"] == title), None)
    if h:
        _career(state)["hustle"] = dict(h)

def job_base(state):
    j = _career(state).get("job")
    return (j.get("base") or j["title"]) if j else None


# ---------------------------------------------------------------- crossover credits
CREDIT_FOR = {"Actor": "acting", "Model": "modelling", "Singer": "songs", "Musician": "songs", "Music Producer": "songs", "DJ": "songs"}

def credit_boost(j, state):
    """A portfolio in a field opens its jobs: easier entry and better pay."""
    kind = CREDIT_FOR.get(j["title"])
    n = P(state)["credits"].get(kind, 0) if kind else 0
    if not n:
        return j
    j = dict(j)
    j["stats"] = {k: max(0, v - min(25, n * 8)) for k, v in j["stats"].items()}
    j["any_of"], j["skills"] = None, {}
    j["pay"] = int(j["pay"] * (1 + min(1.0, n * 0.12)))
    return j


# ---------------------------------------------------------------- sport
def draft_bonus(state):
    p = P(state)
    return min(6, p["seasons"] * 2) + min(6, p["titles"] * 2) + stars(state)

def year(state, career, age, log):
    import sports
    p = P(state)
    sid = sports.my_sport(state)
    perf = state.get("sport_perf", 50)
    ath = state["stats"]["athletic"]
    # scouts start watching high-school players
    if sid and not state.get("pro") and 13 <= age <= 19:
        before = stars(state)
        gain = max(0.0, (ath - 58) / 2 + (perf - 60) / 10 + career.get("fame", 0) / 15)
        p["interest"] = min(100, int(p["interest"] + gain * random.uniform(0.6, 1.2)))
        if stars(state) > before and stars(state) >= 2:
            log(f"Scouts rate you a {stars(state)}-star prospect. College coaches are calling.")
        if random.random() < max(0, perf + ath - 110) / 250:
            p["titles"] += 1
            career["fame"] = min(100, career.get("fame", 0) + 2)
            log(f"Your {sports.SPORT_IDS[sid].lower()} team won the regional championship!")
    elif not sid and not state.get("pro"):
        p["interest"] = int(p["interest"] * 0.8)
    # the pro academy: kids signed at 16 turn pro at 18, or get released
    if p.get("academy") and not state.get("pro"):
        if not sid:
            log(f"You left the {p['academy']} academy.")
            p["academy"] = None
        elif age >= 18:
            if perf >= 50 and ath >= 62:
                tier = 2 if perf >= 75 and ath >= 75 else 3
                log(f"The academy promoted you to the first team at {p['academy']}!")
                sports.sign_pro(state, career, sid, p["academy"], tier, log)
            else:
                log(f"{p['academy']}'s academy released you. You can still try the draft or a trial later.")
            p["academy"] = None
    # college athletes: seasons, titles, and keeping the scholarship
    if career.get("enrolled") and age >= 18 and not state.get("pro"):
        if sid:
            p["seasons"] += 1
            if random.random() < max(0, perf + ath - 100) / 200:
                p["titles"] += 1
                career["fame"] = min(100, career.get("fame", 0) + 4)
                log(f"Your college {sports.SPORT_IDS[sid].lower()} team won the national championship!")
            if p.get("scholar") and perf < 35:
                if p.get("warned"):
                    _lose_scholarship(state, log, "Your form stayed poor and the college withdrew your athletic scholarship.")
                else:
                    p["warned"] = True
                    log("The coach warned you: lift your form or lose your scholarship.")
            elif perf >= 45:
                p["warned"] = False
        elif p.get("scholar"):
            _lose_scholarship(state, log, "You left the team, so the college withdrew your athletic scholarship.")
    if state.get("pro"):
        p["was_pro"] = True
    if p.get("own_academy"):
        state["money"] += p["own_academy"]

def _lose_scholarship(state, log, text):
    p = P(state)
    p["scholar"] = None
    state["scholarship"] = False
    log(text)

def on_retire(state, age):
    P(state)["retired"] = age

def scholarship_pct(state):
    """Share of tuition the athletic scholarship covers (education.funding_plan)."""
    import sports
    p = P(state)
    if not p.get("scholar") or not sports.my_sport(state):
        return 0.0
    return 1.0 if p["scholar"] == "full" else 0.5


# ---------------------------------------------------------------- story actions
def _accept_scholar(kind, college):
    def fn(state):
        p = P(state)
        p["scholar"], p["college"] = kind, college
        state["scholarship"] = True        # recruited athletes get in with lower grades too
        return (f"You committed to {college} on a {'full' if kind == 'full' else 'half'} athletic scholarship. "
                "Apply in the Education tab when you leave school, and stay on the team to keep it.")
    return fn

def _academy(team):
    def fn(state):
        P(state)["academy"] = team
        _fame(state, 3)
        return f"You signed a youth contract with {team}'s academy. Turn pro at 18 if you keep your form."
    return fn

def _declare(state):
    import sports
    c = _career(state)
    sid = sports.my_sport(state)
    notes = []
    if sid and sports.run_draft(state, c, sid, notes.append, bonus=3):
        c["enrolled"] = False
        notes.append("You left college to turn pro.")
    return " ".join(notes) or "Nobody picked you. You went back to college."

def _after_sport(choice):
    def fn(state):
        f = _fame(state)
        P(state)["after_sport"] = choice
        if choice == "coach":
            give_job(state, "Sports Coach", 42000 + f * 600, fame=False)
            return "You became a coach, passing on everything you learned."
        if choice == "pundit":
            give_job(state, "Sports Pundit", 50000 + f * 1500, base="Sports Pundit")
            return "You joined a TV channel as a pundit. Your opinions are now national news."
        if choice == "academy":
            state["money"] = max(0, state["money"] - 60000)
            P(state)["own_academy"] = 18000 + f * 300
            return "You opened your own sports academy for kids."
        return ""
    return fn

def _viral(state):
    P(state)["viral"] = True
    _fame(state, 8)
    return "Millions watched. Your follower count exploded overnight."

def _record_deal(label):
    def fn(state):
        f = _fame(state)
        P(state)["label"] = label
        give_job(state, "Singer", 40000 * (1 + f / 40))
        _fame(state, 6)
        credit(state, "songs", 2)
        return f"You signed with {label}. Your debut single is already in the works."
    return fn

def _idol_route(state):
    import idol
    notes = []
    idol.audition(state, notes.append)
    return " ".join(notes)

def _sell_beat(state):
    state["money"] += 2500
    credit(state, "songs")
    return "You sold the beat for $2,500. Your name is in the credits."

def _go_producer(state):
    give_job(state, "Music Producer", 30000 * (1 + P(state)["credits"].get("songs", 0) * 0.15))
    credit(state, "songs")
    return "You went pro as a music producer."

def _model(state):
    p = P(state)
    p["scouted"] = True
    credit(state, "modelling")
    if state.get("age", 0) < 18:
        give_hustle(state, "Part-time Modelling")
        return "You signed with the agency. Shoots after school and in the holidays."
    give_job(state, "Model", 40000 * (1 + _fame(state) / 50))
    return "You signed with the agency and booked your first campaign."

def _cast(state):
    p = P(state)
    p["scouted"] = True
    credit(state, "acting")
    _fame(state, 6)
    state["money"] += 5000
    return "You were cast in a TV series. Your first acting credit."

def _crossover(state):
    P(state)["crossover"] = True
    credit(state, "acting")
    give_job(state, "Actor", 45000 * (1 + _fame(state) / 40))
    _fame(state, 5)
    return "You landed the part. You're an actor now."

def _lead(state):
    P(state)["lead"] = True
    credit(state, "acting", 2)
    _fame(state, 12)
    j = _career(state).get("job")
    if j:
        j["pay"] = int(j["pay"] * 1.5)
    return "The film was a hit. You're a leading name now."

def _after_idol(choice):
    def fn(state):
        f, p = _fame(state), P(state)
        p["after_idol"] = choice
        if choice == "singer":
            give_job(state, "Singer", 40000 * (1 + f / 30))
            credit(state, "songs")
            return "You signed a solo deal as a singer. Your fans came with you."
        if choice == "actor":
            credit(state, "acting")
            give_job(state, "Actor", 45000 * (1 + f / 35))
            return "You moved into acting. The first scripts arrived within a week."
        if choice == "producer":
            give_job(state, "Music Producer", 40000 * (1 + p["credits"].get("songs", 0) * 0.15))
            return "You moved behind the scenes as a producer, writing for the next generation of idols."
        if choice == "judge":
            state["money"] += 80000 + f * 2000
            _fame(state, 4)
            return "You joined a survival show as a judge. Trainees cried when you spoke."
        state["stats"]["mental"] = min(100, state["stats"]["mental"] + 6)
        return "You stepped away from the spotlight. It's quiet. You like it."
    return fn

def _produce_idols(state):
    state["money"] += 30000 + _fame(state) * 800
    _fame(state, 4)
    credit(state, "songs")
    return "The group's debut song went to number one. Agencies want you now."


# ---------------------------------------------------------------- story beats
def beats(state, ctx, age):
    import sports, idol
    import skills as SK
    p, out = P(state), []
    c = _career(state)
    sid = sports.my_sport(state)
    base = job_base(state)
    fame = c.get("fame", 0)
    looks = state["stats"]["looks"]
    # sport
    if sid and 16 <= age <= 18 and not p.get("scholar") and not p.get("academy") and not state.get("pro"):
        college = random.choice(_COLLEGES)
        if p["interest"] >= 55:
            opts = {"Accept the full scholarship": S(fn=_accept_scholar("full", college)),
                    "Keep your options open": {"mental": 1}}
            if p["interest"] >= 75 and sid in ("football", "basket", "rugby"):
                team = random.choice([n for n, t in sports.TEAMS[sid] if t >= 2])
                opts[f"Join {team}'s academy instead"] = S(fn=_academy(team))
            out.append(("sp_offer", f"A coach from {college} watched you play and offered you a full athletic scholarship.", opts))
        elif p["interest"] >= 35:
            out.append(("sp_offer_half", f"{college} offered you a half athletic scholarship if you keep playing.",
                        {"Accept": S(fn=_accept_scholar("half", college)), "Hold out for a better offer": {"mental": -1}}))
    if sid and p["seasons"] >= 2 and 19 <= age <= 23 and c.get("enrolled") and not state.get("pro") and state["stats"]["athletic"] >= 60:
        out.append(("sp_declare", "Pro scouts say you'd go early in the draft. Do you declare, or finish your degree?",
                    {"Declare for the draft": S(fn=_declare), "Finish your degree first": {"academic": 2, "mental": 1}}))
    if p.get("retired") is not None and not p.get("after_sport") and age - p["retired"] <= 2:
        opts = {"Become a coach": S(fn=_after_sport("coach")), "Open a sports academy (-$60k)": S(fn=_after_sport("academy")),
                "Take a long holiday": with_(S(fn=_after_sport("rest")), mental=5)}
        if fame >= 30:
            opts["Become a TV pundit"] = S(fn=_after_sport("pundit"))
        out.append(("sp_after", "Your playing days are over. What comes next?", opts))
    # music
    sing = max(SK.level_of(state, "singing"), SK.level_of(state, "music"))
    gigging = (c.get("hustle") or {}).get("base") == "Musician" or base in ("Musician", "Singer")
    if 12 <= age <= 32 and sing >= 2 and not p.get("viral") and not idol.active(state) and (gigging or sing >= 3):
        out.append(("mu_viral", "A video of you singing went viral overnight.",
                    {"Post more covers": S(fn=_viral), "Lie low, it's a bit much": {"mental": 1}}))
    if p.get("viral") and not p.get("label") and 16 <= age <= 35 and not idol.active(state):
        label = random.choice(_LABELS)
        opts = {"Sign the record deal": S(fn=_record_deal(label)), "Stay independent": with_(S(fn=lambda s: _fame(s, 3) and ""), mental=1)}
        if age <= 23:
            opts["Audition for an idol agency instead"] = S(fn=_idol_route)
        out.append(("mu_label", f"{label} wants to sign you after your viral cover.", opts))
    if SK.level_of(state, "music") >= 3 and 15 <= age <= 45 and base != "Music Producer":
        out.append(("mu_beat", "A rapper heard your beats online and wants to buy one.",
                    {"Sell it": S(fn=_sell_beat), "Go pro as a producer": S(fn=_go_producer), "Keep it for yourself": {"mental": 1}}))
    if base == "Music Producer" and fame >= 15 and age <= 60:
        out.append(("~mu_idols", "An idol agency wants you to produce their new group's debut.",
                    {"Take the job": S(fn=_produce_idols), "You're too busy": {"mental": 1}}))
    # screen & fashion
    if 14 <= age <= 24 and looks >= 70 and not p.get("scouted") and base != "Model":
        out.append(("fa_scout", "A modelling scout stopped you in the street and handed you a card.",
                    {"Call the agency": S(fn=_model), "Throw the card away": {"mental": 1}}))
    if 10 <= age <= 20 and ("drama" in state.get("activities", {}) or (c.get("hustle") or {}).get("base") == "Actor") and not p["credits"]["acting"]:
        out.append(("sc_casting", "A casting director was in the audience at your last play.",
                    {"Take the role": S(fn=_cast), "Focus on school": {"academic": 2}}))
    if base == "Model" and (fame >= 30 or p["credits"]["modelling"] >= 3) and not p.get("crossover"):
        d = random.choice(_DIRECTORS)
        out.append(("fa_crossover", f"Film director {d} saw your campaign and wants you to read for a part.",
                    {"Audition": {"gamble": [S(fn=_crossover), {"mental": -2}]}, "Stay in fashion": {"looks": 1}}))
    if base == "Actor" and p["credits"]["acting"] >= 2 and fame >= 40 and not p.get("lead"):
        out.append(("sc_lead", "You're offered the lead in a big-budget film.",
                    {"Take it": {"gamble": [S(fn=_lead), with_(S(fn=lambda s: _fame(s, -4) and ""), mental=-3)]},
                     "Stick to smaller roles": {"mental": 1}}))
    # life after idol
    d = idol.data(state)
    if d and d["stage"] == "ended" and d.get("group") and not p.get("after_idol"):
        opts = {"Keep singing as a solo artist": S(fn=_after_idol("singer")),
                "Step away from the spotlight": S(fn=_after_idol("rest"))}
        if p["credits"]["acting"] or d["skills"]["visual"] >= 60:
            opts["Move into acting"] = S(fn=_after_idol("actor"))
        if d.get("pen", 0) >= 25 or SK.level_of(state, "music") >= 3:
            opts["Become a producer"] = S(fn=_after_idol("producer"))
        if fame >= 40:
            opts["Judge a survival show"] = S(fn=_after_idol("judge"))
        out.append(("id_after", "Your idol days are over. Offers are coming in. What's next?", opts))
    return out


# ---------------------------------------------------------------- the Paths view
def _tracks(state, career):
    import sports, idol
    import skills as SK
    p = P(state)
    cr = p["credits"]
    base = job_base(state)
    d = idol.data(state)
    sid = sports.my_sport(state)
    sport = [("Join a school team", bool(sid or state.get("pro") or p.get("was_pro"))),
             (f"Get scouted ({'*' * stars(state) or 'no stars'})", stars(state) >= 2 or p.get("was_pro")),
             ("Scholarship or academy", bool(p.get("scholar") or p.get("academy") or p["seasons"])),
             (f"College seasons ({p['seasons']})", p["seasons"] >= 1 or p.get("was_pro")),
             ("Drafted, go pro", bool(state.get("pro") or p.get("was_pro"))),
             ("Coach, pundit, academy", bool(p.get("after_sport")))]
    music = [("Learn singing or music", max(SK.level_of(state, "singing"), SK.level_of(state, "music")) >= 1),
             ("Gigs, busking, audition", bool(p.get("viral") or d or (career.get("hustle") or {}).get("base") == "Musician")),
             ("Go viral or debut", bool(p.get("viral") or (d and d.get("group")))),
             ("Record deal or idol group", bool(p.get("label") or (d and d.get("group")))),
             ("Solo star or producer", base in ("Singer", "Music Producer") and (p.get("label") or p.get("after_idol")) or bool(d and d["stage"] == "solo"))]
    screen = [("Looks or drama club", state["stats"]["looks"] >= 60 or "drama" in state.get("activities", {})),
              ("Scouted or cast", bool(p.get("scouted") or cr["acting"] or cr["modelling"])),
              ("Paid modelling or acting", base in ("Model", "Actor") or cr["acting"] + cr["modelling"] >= 2),
              ("Cross over", bool(p.get("crossover") or (cr["acting"] and cr["modelling"]))),
              ("Lead roles", bool(p.get("lead")))]
    hints = {
        "Sport": ("Join a sports team in Activities." if not sid and not state.get("pro") else
                  "Train and keep your form up: scouts watch ages 13-19." if stars(state) < 3 and not p.get("scholar") else
                  "Go to college on your scholarship, or wait for the draft at 20." if not state.get("pro") else
                  "You're pro. Retire well and new doors open."),
        "Music": ("Take singing or music lessons in Activities." if not music[0][1] else
                  "Busk, gig (Fame tab) or audition (Idol tab)." if not music[1][1] else
                  "Keep performing: labels and agencies are watching." if not music[3][1] else
                  "Writing your own songs leads to producing."),
        "Screen & fashion": ("Join the Drama Society or work on your looks." if not screen[0][1] else
                             "Scouts look for striking faces aged 14-24." if not screen[1][1] else
                             "Build credits: they make Actor and Model jobs easier to get." if not screen[3][1] else
                             "Fame 40+ and two acting credits bring lead roles."),
    }
    return [("Sport", (80, 170, 200), sport), ("Music", (236, 120, 160), music), ("Screen & fashion", (240, 170, 70), screen)], hints

def draw_panel(screen, rect, mouse, state, career):
    tracks, hints = _tracks(state, career)
    draw_text(screen, "Career paths", font, INK, rect.x, rect.y)
    draw_text(screen, "Every talent can turn into a career, and careers lead into each other.", small_font, MUTED, rect.x, rect.y + 28)
    w = (rect.width - 24) // 3
    for n, (name, col, steps) in enumerate(tracks):
        card = pygame.Rect(rect.x + n * (w + 12), rect.y + 56, w, 300)
        draw_rounded_rect(screen, WHITE, card, radius=12)
        pygame.draw.rect(screen, OUTLINE, card, 1, border_radius=12)
        draw_rounded_rect(screen, col, (card.x, card.y, card.w, 6), radius=3)
        draw_text(screen, name, small_font, INK, card.x + 12, card.y + 14)
        cur = next((i for i, (_, ok) in enumerate(steps) if not ok), len(steps))
        for i, (label, ok) in enumerate(steps):
            y = card.y + 42 + i * 31
            if i < len(steps) - 1:
                pygame.draw.line(screen, col if ok else LIGHT_GREY, (card.x + 21, y + 10), (card.x + 21, y + 41), 3)
            pygame.draw.circle(screen, col if ok else (WHITE if i != cur else (255, 240, 228)), (card.x + 21, y + 10), 9)
            pygame.draw.circle(screen, col if ok or i == cur else LIGHT_GREY, (card.x + 21, y + 10), 9, 2)
            if ok:
                pygame.draw.lines(screen, WHITE, False, [(card.x + 16, y + 10), (card.x + 20, y + 14), (card.x + 26, y + 6)], 2)
            draw_text(screen, label, small_font, INK if ok or i == cur else DARK_GREY, card.x + 38, y + 1)
        hint = hints[name]
        words, line, ly = hint.split(), "", card.bottom - 60
        for wd in words:          # wrap the hint inside the card
            if small_font.size(line + " " + wd)[0] > w - 24 and line:
                draw_text(screen, line, small_font, MUTED, card.x + 12, ly)
                line, ly = wd, ly + 18
            else:
                line = (line + " " + wd).strip()
        draw_text(screen, line, small_font, MUTED, card.x + 12, ly)
    cr = P(state)["credits"]
    p = P(state)
    y = rect.y + 372
    draw_text(screen, "Credits", small_font, INK, rect.x, y)
    chips = [f"Acting {cr['acting']}", f"Modelling {cr['modelling']}", f"Songs {cr['songs']}",
             f"College seasons {p['seasons']}", f"Titles {p['titles']}"]
    x = rect.x + 70
    for ch in chips:
        cw = small_font.size(ch)[0] + 20
        draw_rounded_rect(screen, (244, 242, 250), (x, y - 3, cw, 24), radius=12)
        draw_text(screen, ch, small_font, INK, x + 10, y)
        x += cw + 8
    draw_text(screen, "Credits in a field make its jobs easier to get and better paid. Idols earn them too:",
              small_font, MUTED, rect.x, y + 30)
    draw_text(screen, "dramas count as acting, ads as modelling, and songs you write as songs.", small_font, MUTED, rect.x, y + 50)
    return {"_paths": True}
