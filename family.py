"""The family tree, grandchildren, wills and carrying on as an heir.

When your life ends and you have a child, grandchild or partner, you get to
pick who carries on. They keep your money (after estate tax), property and
businesses and start their own life at their own age."""
import random
import pygame
import asyncio
from constants import fmt, INK, MUTED, OUTLINE, WHITE, ACCENT, GREEN, RED, DARK_GREY
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, font, small_font, title_font, draw_text, draw_rounded_rect
from avatar import draw_avatar
import people as P
import worldjobs

ESTATE_TAX = 0.10
MAX_GRANDKIDS = 6

def is_grandparent(rel):
    return rel.endswith("Grandfather") or rel.endswith("Grandmother")

def is_grandchild(p):
    return bool(p.get("is_grand"))

# ---- grandchildren ---------------------------------------------------------------
def family_year(people, log):
    """Adult children sometimes have children of their own."""
    grands = [p for p in people if is_grandchild(p)]
    if len(grands) >= MAX_GRANDKIDS:
        return
    for c in [p for p in people if p.get("is_child") and 24 <= p.get("age", 0) <= 42]:
        if c.get("kids", 0) >= 3:
            continue
        if random.random() < 0.11 and len(grands) < MAX_GRANDKIDS:
            g = random.choice(["Male", "Female"])
            kid = P.make_person("Grandson" if g == "Male" else "Granddaughter", "family", g, closeness=55, age=0)
            kid["is_grand"] = True
            kid["parent_name"] = c["name"]
            kid["traits"] = list({random.choice(c["traits"]), random.choice(P.TRAITS)})
            base = c.get("stats") or P.random_stats()
            kid["stats"] = {k: max(5, min(98, int(random.gauss(base.get(k, 50), 12)))) for k in P.STAT_KEYS}
            kid["look"]["hair"] = list(c["look"]["hair"])
            kid["look"]["skin"] = list(c["look"]["skin"])
            people.append(kid)
            grands.append(kid)
            c["kids"] = c.get("kids", 0) + 1
            log(f"{c['name']} had a baby, {kid['name']}. You're a grandparent!")

# ---- money ----------------------------------------------------------------------
def estate_value(state):
    import assets
    v = state["money"] + state.get("savings", 0) + state.get("invest", 0) - state.get("debt", 0)
    v += assets.net_worth_assets(state)
    v += sum(b["value"] * b.get("equity", 100) // 100 for b in state.get("businesses", []))
    return max(0, int(v))

def heirs(people, partner):
    out = []
    for p in people:
        if p.get("is_child"):
            out.append({"p": p, "kind": "Child"})
    if partner:
        out.append({"p": partner, "kind": "Spouse" if partner.get("married") else "Partner"})
    for p in people:
        pass
    gk = sorted([p for p in people if is_grandchild(p)], key=lambda q: -q.get("age", 0))
    out += [{"p": p, "kind": "Grandchild"} for p in gk]
    return out[:6]

def share_for(kind, n):
    """What fraction of the estate (before tax) the chosen heir carries on with."""
    if n == 1:
        return 1.0
    return {"Spouse": 0.6, "Partner": 0.4, "Child": 0.55, "Grandchild": 0.4}.get(kind, 0.4)

# ---- the Family tab -------------------------------------------------------------
def _person_look(p):
    lk = p["look"]
    return p["gender"], tuple(lk["hair"]), lk["style"], tuple(lk["skin"]), lk.get("facial", "None")

SHORT = {"Mother": "Mum", "Father": "Dad", "Son": "Son", "Daughter": "Daughter", "Grandson": "Grandkid", "Granddaughter": "Grandkid",
         "Sibling": "Sibling", "Half-Sibling": "Half-sib", "Step-Sibling": "Step-sib", "Brother": "Brother", "Sister": "Sister"}

def short_rel(rel):
    if rel.endswith("Grandfather"):
        return "Grandpa"
    if rel.endswith("Grandmother"):
        return "Grandma"
    return SHORT.get(rel, rel)

def _node(screen, x, y, p, mouse_pos, hits, tag=None, heir=False, me=False, av=72):
    r = pygame.Rect(x - av // 2, y, av, av)
    if me:
        pygame.draw.circle(screen, ACCENT, (x, y + av // 2), av // 2 + 4, 3)
    g, hc, hs, sk, fh = _person_look(p)
    draw_avatar(screen, r, g, hc, hs, sk, fh, p.get("age", 30), 60, (p.get("look") or {}).get("feat"))
    name = p["name"].split()[0]
    draw_text(screen, name, small_font, INK, x, y + av + 8, centre=True)
    sub = tag or f"{p.get('age', '?')}"
    draw_text(screen, sub, small_font, MUTED, x, y + av + 23, centre=True)
    if p.get("dead"):
        draw_text(screen, "passed", small_font, MUTED, x, y + av + 37, centre=True)
    if heir:
        t = small_font.render("HEIR", True, (255, 255, 255))
        b = pygame.Rect(x - t.get_width() // 2 - 5, y - 8, t.get_width() + 10, 16)
        draw_rounded_rect(screen, ACCENT, b, radius=6)
        screen.blit(t, (b.x + 5, b.y + 1))
    hits.append((p, r.inflate(10, 36)))

def _row(screen, y_label, label, rect, y, nodes, mouse_pos, hits, state, av=72):
    draw_text(screen, label, small_font, MUTED, rect.x, y + av // 2 - 6)
    n = len(nodes)
    if not n:
        return
    left = rect.x + 90
    span = rect.right - left - 20
    step = min(96, span // max(1, n))
    start = left + (span - step * (n - 1)) // 2
    for i, (p, tag, me) in enumerate(nodes):
        _node(screen, start + i * step, y, p, mouse_pos, hits, tag, av=av, heir=(state.get("heir_name") == p["name"] and not me and (p.get("is_child") or p.get("is_grand") or p.get("category") == "partner")), me=me)

def draw_family_tab(screen, rect, mouse_pos, state, people, partner, me_look, player_name, age):
    """Plain tree drawn straight on the background: no boxes."""
    hits = []
    gps = [p for p in people if is_grandparent(p["relation"])]
    pars = [p for p in people if p["relation"] in ("Mother", "Father")]
    sibs = [p for p in people if "Sibling" in p["relation"]]
    kids = [p for p in people if p.get("is_child")]
    grands = [p for p in people if is_grandchild(p)]
    draw_text(screen, "Family tree", font, INK, rect.x, rect.y - 2)
    ev = estate_value(state)
    draw_text(screen, f"Estate ${fmt(ev)}", small_font, GREEN, rect.x + 130, rect.y + 2)
    if kids or partner or grands:
        draw_text(screen, "Click a child, partner or grandchild to name your heir.", small_font, MUTED, rect.x + 270, rect.y + 2)
    else:
        draw_text(screen, "No heirs yet: have a child or marry so your story goes on.", small_font, MUTED, rect.x + 270, rect.y + 2)
    y = rect.y + 24
    rows = []
    if gps:
        rows.append(("Grandparents", [(p, short_rel(p["relation"]) + " " + str(p["age"]), False) for p in gps]))
    if pars or sibs:
        rows.append(("Parents", [(p, short_rel(p["relation"]) + " " + str(p["age"]), False) for p in pars]))
    me = {"name": player_name, "gender": me_look[0], "age": age,
          "look": {"hair": list(me_look[1]), "style": me_look[2], "skin": list(me_look[3]), "facial": me_look[4], "feat": state.get("feat")}}
    mine = [(me, "You " + str(age), True)] + [(p, short_rel(p["relation"]) + " " + str(p["age"]), False) for p in sibs]
    if partner:
        mine.append((partner, ("Spouse " if partner.get("married") else "Partner ") + str(partner["age"]), False))
    rows.append(("You", mine))
    if kids:
        rows.append(("Children", [(p, short_rel(p["relation"]) + " " + str(p["age"]), False) for p in kids]))
    if grands:
        rows.append(("Grandchildren", [(p, short_rel(p["relation"]) + " " + str(p["age"]), False) for p in grands]))
    avail = rect.height - 34
    rh = min(124, avail // max(1, len(rows)))
    av = max(34, min(72, rh - 40))
    for label, nodes in rows:
        _row(screen, y, label, rect, y, nodes[:8], mouse_pos, hits, state, av)
        # a little connector line from this generation to the next
        y += rh
    return {"hits": hits, "me": me["name"]}

def handle_family_click(mx, my, b, state):
    for p, r in b.get("hits", []):
        if r.collidepoint(mx, my):
            if p.get("is_child") or is_grandchild(p) or p.get("category") == "partner":
                state["heir_name"] = None if state.get("heir_name") == p["name"] else p["name"]
            return

# ---- succession -----------------------------------------------------------------
async def succession_screen(screen, data, options, death_age, name):
    """Returns the chosen option dict, or None to end the family line."""
    clock = pygame.time.Clock()
    st = data["state"]
    ev = estate_value(st) if "money" in st else 0
    sel = 0
    pref = st.get("heir_name")
    for i, o in enumerate(options):
        if o["p"]["name"] == pref:
            sel = i
    while True:
        rects = []
        n = len(options)
        cw = min(190, (SCREEN_WIDTH - 60) // max(1, n))
        x0 = (SCREEN_WIDTH - cw * n) // 2
        for i in range(n):
            rects.append(pygame.Rect(x0 + i * cw, 190, cw - 8, 300))
        go = pygame.Rect(SCREEN_WIDTH // 2 - 130, 590, 260, 44)
        end = pygame.Rect(SCREEN_WIDTH // 2 - 90, 645, 180, 30)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT:
                    sel = (sel - 1) % n
                elif e.key == pygame.K_RIGHT:
                    sel = (sel + 1) % n
                elif e.key == pygame.K_RETURN:
                    return options[sel]
                elif e.key == pygame.K_ESCAPE:
                    return None
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(rects):
                    if r.collidepoint(e.pos):
                        sel = i
                if go.collidepoint(e.pos):
                    return options[sel]
                if end.collidepoint(e.pos):
                    return None
        screen.fill((24, 22, 34))
        draw_text(screen, "Who carries the fire on?", title_font, (255, 236, 210), SCREEN_WIDTH // 2, 48, centre=True)
        draw_text(screen, f"{name} died at {death_age}. Estate ${fmt(ev)}, estate tax {int(ESTATE_TAX * 100)}%.", font, (200, 195, 215), SCREEN_WIDTH // 2, 100, centre=True)
        draw_text(screen, "Pick who you play next. They keep property, businesses and their share of the money.", small_font, (160, 155, 180), SCREEN_WIDTH // 2, 132, centre=True)
        mouse = pygame.mouse.get_pos()
        for i, (o, r) in enumerate(zip(options, rects)):
            p = o["p"]
            on = i == sel
            if on:
                pygame.draw.rect(screen, (255, 160, 70), r, 2, border_radius=14)
            elif r.collidepoint(mouse):
                pygame.draw.rect(screen, (90, 85, 110), r, 1, border_radius=14)
            g, hc, hs, sk, fh = _person_look(p)
            draw_avatar(screen, pygame.Rect(r.centerx - 60, r.y + 12, 120, 130), g, hc, hs, sk, fh, p.get("age", 30), 60, (p.get("look") or {}).get("feat"))
            draw_text(screen, p["name"], font, (255, 255, 255), r.centerx, r.y + 154, centre=True)
            draw_text(screen, f"{o['kind']}, age {p.get('age', '?')}", small_font, (190, 185, 205), r.centerx, r.y + 178, centre=True)
            job = P.occupation(p) if p.get("age", 0) >= 18 else "Too young to work"
            draw_text(screen, job[:26], small_font, (160, 155, 180), r.centerx, r.y + 198, centre=True)
            amt = int(ev * (1 - ESTATE_TAX) * share_for(o["kind"], n))
            draw_text(screen, f"Inherits ${fmt(amt)}", small_font, (120, 220, 150), r.centerx, r.y + 226, centre=True)
            st_ = p.get("stats", {})
            l1 = f"Looks {st_.get('looks', 0)}  Social {st_.get('social', 0)}"
            l2 = f"Brains {st_.get('academic', 0)}  Athletic {st_.get('athletic', 0)}"
            draw_text(screen, l1, small_font, (160, 155, 180), r.centerx, r.y + 250, centre=True)
            draw_text(screen, l2, small_font, (160, 155, 180), r.centerx, r.y + 268, centre=True)
            if pref == p["name"]:
                draw_text(screen, "Named in your will", small_font, (255, 190, 110), r.centerx, r.y + 276, centre=True)
        draw_rounded_rect(screen, (255, 140, 50) if go.collidepoint(mouse) else (235, 120, 40), go, radius=12)
        draw_text(screen, f"Play as {options[sel]['p']['name'].split()[0]}", font, (255, 255, 255), go.centerx, go.centery, centre=True)
        draw_text(screen, "End the family line", small_font, (170, 165, 190), end.centerx, end.centery, centre=True)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

def build_heir_save(data, option, grandchild_parent_note=None):
    """Turns the finished life (`data`, in the save format) into the save for
    the heir's new life."""
    p = option["p"]
    st = data["state"]
    people = data["people"]
    friends = data["friends"]
    old_partner = data["partner"]
    ev = estate_value(st)
    n = len(heirs(people, old_partner))
    cash = int(ev * (1 - ESTATE_TAX) * share_for(option["kind"], n))
    old_name = data["name"]
    kind = option["kind"]
    age = p.get("age", 18)
    lk = p["look"]

    # --- the new cast of relatives ---
    new_people = []
    def rel(src, relation, cat="family"):
        c = dict(src)
        c["relation"] = relation
        c["category"] = cat
        for k in ("is_child", "is_grand", "kids", "parent_name"):
            c.pop(k, None)
        c["contacted"] = False
        return c
    if kind == "Child":
        for sp, r in ((old_partner, None),):
            if sp and sp.get("name") != p["name"]:
                new_people.append(rel(sp, "Mother" if sp["gender"] == "Female" else "Father"))
        for c in people:
            if c.get("is_child") and c["name"] != p["name"]:
                new_people.append(rel(c, "Brother" if c["gender"] == "Male" else "Sister"))
            if c["relation"] in ("Mother", "Father") and False:
                pass
        for c in people:
            if is_grandchild(c) and c.get("parent_name") == p["name"]:
                new_people.append(rel(c, "Son" if c["gender"] == "Male" else "Daughter"))
                new_people[-1]["is_child"] = True
        gp_rel = "Grandfather" if data["gender"] == "Male" else "Grandmother"
    elif kind == "Grandchild":
        par = next((c for c in people if c.get("name") == p.get("parent_name")), None)
        if par:
            new_people.append(rel(par, "Mother" if par["gender"] == "Female" else "Father"))
        for c in people:
            if is_grandchild(c) and c["name"] != p["name"] and c.get("parent_name") == p.get("parent_name"):
                new_people.append(rel(c, "Brother" if c["gender"] == "Male" else "Sister"))
        if old_partner and old_partner.get("category") != "enemy":
            new_people.append(rel(old_partner, "Paternal Grandfather" if old_partner["gender"] == "Male" else "Paternal Grandmother"))
    else:  # Spouse / Partner carries on
        for c in people:
            if c.get("is_child"):
                new_people.append(c)
        for c in people:
            if is_grandchild(c):
                new_people.append(c)
        for c in people:
            if c["relation"] in ("Mother", "Father") or "Sibling" in c["relation"] or is_grandparent(c["relation"]):
                pass
    # a young heir needs someone to live with
    if age < 18 and not any(q["relation"] in ("Mother", "Father") for q in new_people):
        g = random.choice(["Male", "Female"])
        guard = P.make_person("Father" if g == "Male" else "Mother", "family", g, closeness=65, age=age + random.randint(26, 36))
        new_people.append(guard)
    for q in new_people:
        q.setdefault("stats", P.random_stats())
    people_out = new_people
    p_pop = [x for x in people_out if x.get("name") == p["name"]]
    for x in p_pop:
        people_out.remove(x)

    stats = {"physical": 75, "wealth": 10, "mental": 70}
    ps = p.get("stats") or P.random_stats()
    for k in P.STAT_KEYS:
        stats[k] = ps.get(k, 50)
    if kind in ("Spouse", "Partner"):
        stats["physical"] = max(40, 85 - max(0, age - 30))
    elif age < 18:
        stats["physical"] = 85
    stats["wealth"] = min(100, cash // 500)

    new_state = {
        "stats": stats,
        "family_wealth": "Wealthy" if cash > 400000 else ("Comfortable" if cash > 40000 else "Struggling"),
        "debt": st.get("debt", 0), "savings": 0, "invest": 0,
        "home": None,
        "money": cash, "age": age,
        "actions_remaining": 20, "actions_used": {}, "life_event_resolved": False,
        "journal": [(age, f"You are {p['name']}. You carry on after {old_name}."), (age, f"You inherited ${fmt(cash)} (estate tax paid).")],
        "owned": ["heirloom"] if "heirloom" in st.get("owned", []) else [],
        "activities": {}, "scholarship": False,
        "player_traits": list(p.get("traits", random.sample(P.TRAITS, 2))), "feat": dict(lk.get("feat") or {}),
        "gender": p["gender"], "attracted": p.get("attracted", "Both"),
        "skills": {}, "aspiration": random.choice(["Wealthy", "Family-minded", "Scholar", "Athlete", "Social butterfly", "Soulmate", "Performer"]),
        "aspiration_done": False,
        "properties": st.get("properties", []), "cars": st.get("cars", []),
        "businesses": st.get("businesses", []), "_biz_migrated": True,
        "achievements": st.get("achievements", []),
        "generation": st.get("generation", 1) + 1,
        "lineage": (st.get("lineage", []) + [old_name]),
        "econ_v": 2,
    }
    for b in new_state["businesses"]:
        b["run"] = "manager" if age < 21 else b["run"]
    if kind in ("Spouse", "Partner"):
        pf = P.finances(p)
        new_state["money"] += pf.get("savings", 0)
    if st.get("home") or any(pr.get("live") for pr in st.get("properties", [])):
        pass
    career = {"education": "High School" if age >= 18 else "None", "enrolled": False, "uni_target": None, "uni_years_done": 0,
              "college_name": None, "college_prestige": 0, "prestige": 0, "course": None,
              "pending_course": None, "job": None, "browsing_jobs": False, "scroll": 0,
              "side_job": None, "fame": 0, "experience": 0, "hustle": None}
    new_partner = None
    if kind == "Child" and False:
        pass
    if kind in ("Spouse", "Partner"):
        pass
    hist = [dict(stats)]
    return {"gender": p["gender"], "name": p["name"], "hair_colour": list(lk["hair"]), "hairstyle": lk["style"],
            "skin_tone": list(lk["skin"]), "facial_hair": lk.get("facial", "None"),
            "stats": stats, "history": hist, "last_event_text": {}, "recent_events": [],
            "people": people_out, "friends": [f for f in friends if f.get("category") == "friend"][:3] if kind in ("Spouse", "Partner") else [],
            "partner": new_partner, "career": career, "state": new_state, "age": age}
