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
def new_sibling(people, player_age, log, chance=0.14):
    """While you're young, your parents may have another baby."""
    mum = next((p for p in people if p["relation"] == "Mother"), None)
    dad = next((p for p in people if p["relation"] == "Father"), None)
    if not mum or not dad or mum.get("age", 99) > 42 or not 1 <= player_age <= 12:
        return None
    younger = [p for p in people if p["relation"] == "Sibling" and p.get("age", 0) < player_age]
    if len(younger) >= 3 or random.random() >= chance:
        return None
    g = random.choice(["Male", "Female"])
    baby = P.make_person("Sibling", "family", g, closeness=60, age=0, skin=(mum.get("look") or {}).get("skin"))
    sibs = [p for p in people if p["relation"] == "Sibling" and p.get("stats")]
    if sibs:
        baby["stats"] = P.random_stats(sibs[0]["stats"], 13)
    people.append(baby)
    log(f"Your parents had a baby: your little {'brother' if g == 'Male' else 'sister'}, {baby['name'].split()[0]}.")
    return baby

def family_year(people, log):
    """Adult children sometimes have children of their own."""
    grands = [p for p in people if is_grandchild(p)]
    if len(grands) >= MAX_GRANDKIDS:
        return
    for c in [p for p in people if p.get("is_child") and 24 <= p.get("age", 0) <= 45]:
        if not c.get("spouse_name") and random.random() < 0.08:
            sg = random.choice(["Male", "Female"])
            sp = P.make_person("Son-in-law" if sg == "Male" else "Daughter-in-law", "family", sg, closeness=50,
                               age=max(22, c["age"] + random.randint(-4, 4)))
            sp["is_inlaw"] = True
            sp["inlaw_of"] = c["name"]
            people.append(sp)
            c["spouse_name"] = sp["name"]
            log(f"{c['name']} got married to {sp['name']}.")
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
# ---- heirlooms ---------------------------------------------------------------------
HEIRLOOMS = ["Pocket watch", "Wedding ring", "Oil painting", "Violin", "War medal", "Pearl necklace", "Antique clock",
             "Silver locket", "Old guitar", "Signet ring", "Rare coin set", "Family bible"]

def add_heirloom(state, from_name, mult=1.0):
    h = {"name": random.choice(HEIRLOOMS), "value": int(random.randint(2000, 40000) * max(0.5, mult)), "from": from_name, "gens": 0}
    state.setdefault("heirlooms", []).append(h)
    try:
        state["owned"].add("heirloom")
    except Exception:
        pass
    return h

def heirloom_year(state):
    """Kept heirlooms slowly gain value."""
    for h in state.get("heirlooms", []):
        h["value"] = int(h["value"] * random.uniform(1.02, 1.07))

# ---- money ----------------------------------------------------------------------
def pool_value(state):
    """Cash, savings and investments minus debt."""
    return state["money"] + state.get("savings", 0) + state.get("invest", 0) - state.get("debt", 0)

def estate_value(state):
    import assets
    v = pool_value(state) + assets.net_worth_assets(state)
    v += sum(b["value"] * b.get("equity", 100) // 100 for b in state.get("businesses", []))
    v += sum(h["value"] for h in state.get("heirlooms", []))
    return max(0, int(v))

def heirs(people, partner):
    out = []
    for p in people:
        if p.get("is_child"):
            out.append({"p": p, "kind": "Child"})
    if partner:
        out.append({"p": partner, "kind": "Spouse" if partner.get("married") else "Partner"})
    gk = sorted([p for p in people if is_grandchild(p)], key=lambda q: -q.get("age", 0))
    out += [{"p": p, "kind": "Grandchild"} for p in gk]
    return out[:6]

def start_ages(heir_age):
    """Ages the heir's new life can begin at."""
    ages = {heir_age, 0, 18, 25, 35, 50}
    if heir_age >= 60:
        ages |= {30}
    return sorted(a for a in ages if 0 <= a <= max(heir_age, 50))

def default_plan(state, people, partner, option, options):
    n = len(options)
    pct = {}
    others = [o for o in options if o is not option]
    each = 10 if others else 0
    for o in others:
        pct[o["p"]["name"]] = each
    return {"age": option["p"].get("age", 18), "pct": pct, "charity": 0, "assets": {}}

def heir_pct(plan):
    return max(0, 100 - sum(plan["pct"].values()) - plan["charity"])

def asset_entries(state):
    out = []
    for i, p in enumerate(state.get("properties", [])):
        out.append(("prop%d" % i, p["name"], p["value"], "asset"))
    for i, c in enumerate(state.get("cars", [])):
        out.append(("car%d" % i, c["name"], c["value"], "asset"))
    for i, b in enumerate(state.get("businesses", [])):
        out.append(("biz%d" % i, b["name"], b["value"] * b.get("equity", 100) // 100, "asset"))
    for i, h in enumerate(state.get("heirlooms", [])):
        out.append(("hl%d" % i, h["name"], h["value"], "heirloom"))
    return out

# ---- the Family tab -------------------------------------------------------------
SHORT = {"Mother": "Mum", "Father": "Dad", "Son": "Son", "Daughter": "Daughter", "Grandson": "Grandkid", "Granddaughter": "Grandkid",
         "Sibling": "Sibling", "Half-Sibling": "Half-sib", "Step-Sibling": "Step-sib", "Brother": "Brother", "Sister": "Sister",
         "Aunt": "Aunt", "Uncle": "Uncle",
         "Aunt by marriage": "Aunt-in-law", "Uncle by marriage": "Uncle-in-law", "Son-in-law": "Son-in-law", "Daughter-in-law": "Dau-in-law", "Grandkid": "Grandkid"}

def short_rel(rel):
    if rel.endswith("Grandfather"):
        return "Grandpa"
    if rel.endswith("Grandmother"):
        return "Grandma"
    return SHORT.get(rel, rel)

_TINY = pygame.font.Font(None, 17)

def _person_look(p):
    lk = p["look"]
    return p["gender"], tuple(lk["hair"]), lk["style"], tuple(lk["skin"]), lk.get("facial", "None")

def _node(screen, x, y, p, mouse_pos, hits, tag=None, heir=False, me=False, av=72):
    r = pygame.Rect(x - av // 2, y, av, av)
    if me:
        pygame.draw.circle(screen, ACCENT, (x, y + av // 2), av // 2 + 4, 3)
    g, hc, hs, sk, fh = _person_look(p)
    draw_avatar(screen, r, g, hc, hs, sk, fh, p.get("age", 30), 60, (p.get("look") or {}).get("feat"))
    draw_text(screen, p["name"].split()[0], _TINY, INK, x, y + av + 7, centre=True)
    draw_text(screen, tag or f"{p.get('age', '?')}", _TINY, MUTED, x, y + av + 21, centre=True)
    if heir:
        t = small_font.render("HEIR", True, (255, 255, 255))
        b = pygame.Rect(x - t.get_width() // 2 - 5, y - 8, t.get_width() + 10, 16)
        draw_rounded_rect(screen, ACCENT, b, radius=6)
        screen.blit(t, (b.x + 5, b.y + 1))
    hits.append((p, r.inflate(10, 36)))

def _row(screen, label, rect, y, nodes, mouse_pos, hits, state, av):
    draw_text(screen, label, small_font, MUTED, rect.x, y + av // 2 - 6)
    n = len(nodes)
    if not n:
        return
    left = rect.x + 96
    span = rect.right - left - 16
    step = min(96, span // max(1, n))
    start = left + (span - step * (n - 1)) // 2
    for i, (p, tag, me) in enumerate(nodes):
        ok = p.get("is_child") or p.get("is_grand") or p.get("category") == "partner"
        _node(screen, start + i * step, y, p, mouse_pos, hits, tag, av=av, heir=(state.get("heir_name") == p["name"] and not me and ok), me=me)

def _pill(screen, r, label, mouse, on=False):
    if on:
        draw_rounded_rect(screen, ACCENT, r, radius=10)
    draw_text(screen, label, small_font, INK if on or r.collidepoint(mouse) else MUTED, r.centerx, r.centery, centre=True)


LINE = (96, 88, 120)
def _draw_tree(screen, body, mouse, state, me, age, gps, pars, aunts, sibs, kids, grands, partner, people, hits, tag_par, tag_sib):
    """A proper family tree: couples joined by a marriage line, children hanging
    from a bar under their parents, in-laws beside the relative they married."""
    av = 46
    byname = {p["name"]: p for p in people}
    spouse_of = {}
    for p in people:
        if p.get("is_inlaw") and p.get("inlaw_of") in byname:
            spouse_of[p["inlaw_of"]] = p
    inlaws = {id(v) for v in spouse_of.values()}
    # generation rows, each a list of (person, tag) in order, with the unit info we need
    def tag(p, base=None):
        return base or f"{short_rel(p['relation'])} {p.get('age', '?')}"
    rowh = 112
    step = 88
    pos = {}        # id(person) -> (x, row)
    rowsets = [[], [], [], [], []]

    def side_of(p):
        return p.get("side") or ("Paternal" if p["relation"].startswith("Paternal") else "Maternal" if p["relation"].startswith("Maternal") else "")
    dad = next((p for p in pars if p["relation"] == "Father"), None)
    mum = next((p for p in pars if p["relation"] == "Mother"), None)
    others = [p for p in pars if p is not dad and p is not mum]
    pat = [p for p in aunts if side_of(p) == "Paternal"]
    mat = [p for p in aunts if side_of(p) != "Paternal"]
    # ---- parents row, x in "slots"
    x = 0.0
    slots = {}
    def put(p, row, slot):
        slots[id(p)] = (slot, row)
    cur = 0.0
    for a in pat:
        put(a, 2, cur); cur += 1
        if a["name"] in spouse_of:
            put(spouse_of[a["name"]], 2, cur); cur += 1
    pat_end = cur
    if dad:
        put(dad, 2, cur); dad_x = cur; cur += 1.9
    elif mum:
        dad_x = None
    if mum:
        put(mum, 2, cur); mum_x = cur; cur += 1
    else:
        mum_x = None
    cur += 0.2
    for a in mat:
        put(a, 2, cur); cur += 1
        if a["name"] in spouse_of:
            put(spouse_of[a["name"]], 2, cur); cur += 1
    for o in others:
        put(o, 2, cur + 0.4); cur += 1.4
    # ---- grandparents centred over their own side
    gp_side = {"Paternal": [p for p in gps if p["relation"].startswith("Paternal")],
               "Maternal": [p for p in gps if p["relation"].startswith("Maternal")]}
    side_members = {"Paternal": [p for p in pat] + ([dad] if dad else []), "Maternal": ([mum] if mum else []) + [p for p in mat]}
    for sd, gl in gp_side.items():
        mem = side_members[sd]
        if not gl or not mem:
            for g in gl:
                put(g, 1, (cur if not mem else slots[id(mem[0])][0]))
            continue
        mid = sum(slots[id(m)][0] for m in mem) / len(mem)
        for i, g in enumerate(sorted(gl, key=lambda q: q["gender"])):
            put(g, 1, mid + (i - (len(gl) - 1) / 2) * 1.0)
    # ---- me row, centred under parents
    pcs = [slots[id(p)][0] for p in (dad, mum) if p]
    mid_par = sum(pcs) / len(pcs) if pcs else cur / 2
    my_row = [("s", s) for s in sibs] + [("me", me)]
    ms = len(my_row) + (1 if partner else 0)
    first = mid_par - (ms - 1) / 2
    slot_me = None
    for i, (k, p) in enumerate(my_row):
        sl = first + i
        if k == "me":
            slot_me = sl
        put(p, 3, sl)
    if partner:
        put(partner, 3, first + ms - 1)
    # ---- children and grandchildren
    couple_mid = slot_me if not partner else (slot_me + slots[id(partner)][0]) / 2
    kids_s = sorted(kids, key=lambda q: -q.get("age", 0))
    units = sum(2 if k["name"] in spouse_of else 1 for k in kids_s)
    cur2 = couple_mid - (units - 1) / 2
    kid_slot = {}
    for k in kids_s:
        put(k, 4, cur2); kid_slot[k["name"]] = cur2; cur2 += 1
        if k["name"] in spouse_of:
            put(spouse_of[k["name"]], 4, cur2); cur2 += 1
    # grandchildren go in a 6th row
    gk = {}
    for g in grands:
        gk.setdefault(g.get("parent_name"), []).append(g)
    gcur = None
    for pn, gl in sorted(gk.items(), key=lambda kv: slots[id(byname[kv[0]])][0] if byname.get(kv[0]) is not None and id(byname[kv[0]]) in slots else 99):
        par = byname.get(pn)
        if par is None or id(par) not in slots:
            anchor = couple_mid
        else:
            anchor = slots[id(par)][0] + (0.5 if pn in spouse_of else 0)
        start = anchor - (len(gl) - 1) / 2
        if gcur is not None:
            start = max(start, gcur)
        for i, g in enumerate(gl):
            put(g, 5, start + i)
        gcur = start + len(gl)
    # resolve overlaps within each row (push right), then fit width
    rows_used = sorted({r for _, r in slots.values()})
    byrow = {}
    people_by_id = {id(p): p for p in [me, partner] + list(people) if p}
    for pid, (sl, r) in slots.items():
        byrow.setdefault(r, []).append([sl, pid])
    for r, lst in byrow.items():
        lst.sort()
        for i in range(1, len(lst)):
            if lst[i][0] < lst[i - 1][0] + 1.0:
                lst[i][0] = lst[i - 1][0] + 1.0
        for sl, pid in lst:
            slots[pid] = (sl, r)
    allx = [sl for sl, _ in slots.values()]
    lo, hi = min(allx), max(allx)
    avail = body.width - 40
    st = min(step, max(56, avail / max(1.0, hi - lo))) if hi > lo else step
    cx0 = body.x + 20 + (avail - (hi - lo) * st) / 2
    def X(sl):
        return int(cx0 + (sl - lo) * st)
    rowlist = sorted({r for _, r in slots.values()})
    rowy = {r: body.y + 18 + i * rowh for i, r in enumerate(rowlist)}
    total = rowh * len(rowlist)
    maxscroll = max(0, total - body.height + 10)
    scr = max(0, min(state.get("_fam_scroll", 0), maxscroll))
    state["_fam_scroll"] = scr
    clip = screen.get_clip()
    screen.set_clip(body)
    def cxy(p):
        sl, r = slots[id(p)]
        return X(sl), rowy[r] - scr
    def line(a, b, col=LINE, w=2):
        pygame.draw.line(screen, col, a, b, w)
    label_names = {1: "Grandparents", 2: "Parents", 3: "You", 4: "Children", 5: "Grandchildren"}
    def bar(parents, kidlist):
        """parents: persons forming a couple (or one); kidlist: their children."""
        kidlist = [k for k in kidlist if id(k) in slots]
        parents = [p for p in parents if id(p) in slots]
        if not kidlist or not parents:
            return
        pxs = [cxy(p)[0] for p in parents]
        mid = sum(pxs) // len(pxs)
        py = cxy(parents[0])[1] + av // 2
        ky = cxy(kidlist[0])[1]
        by = ky - 14
        line((mid, py), (mid, by))
        xs = [cxy(k)[0] for k in kidlist] + [mid]
        line((min(xs), by), (max(xs), by))
        for k in kidlist:
            kx = cxy(k)[0]
            line((kx, by), (kx, ky))
    def couple(a, b):
        if id(a) in slots and id(b) in slots:
            (xa, ya), (xb, yb) = cxy(a), cxy(b)
            line((xa + av // 2, ya + av // 2), (xb - av // 2, yb + av // 2), ACCENT, 3)
    # lines first
    if dad and mum:
        couple(dad, mum)
    for sd in ("Paternal", "Maternal"):
        bar(gp_side[sd][:1] and [g for g in gp_side[sd]], side_members[sd])
        gl = gp_side[sd]
        if len(gl) == 2:
            couple(gl[0], gl[1]) if cxy(gl[0])[0] < cxy(gl[1])[0] else couple(gl[1], gl[0])
    for a in aunts:
        if a["name"] in spouse_of:
            sp = spouse_of[a["name"]]
            (couple(a, sp) if cxy(a)[0] < cxy(sp)[0] else couple(sp, a))
    par_couple = [p for p in (dad, mum) if p]
    bar(par_couple, [me] + sibs)
    if partner:
        couple(me, partner) if cxy(me)[0] < cxy(partner)[0] else couple(partner, me)
    bar([me] + ([partner] if partner else []) if False else ([me, partner] if partner else [me]), kids_s)
    for k in kids_s:
        if k["name"] in spouse_of:
            sp = spouse_of[k["name"]]
            (couple(k, sp) if cxy(k)[0] < cxy(sp)[0] else couple(sp, k))
    for pn, gl in gk.items():
        par = byname.get(pn)
        if par is not None and id(par) in slots:
            bar([par] + ([spouse_of[pn]] if pn in spouse_of else []), gl)
    # half / step siblings: dashed link to their other parent
    for o in others:
        for s in sibs:
            if s.get("other_parent") == o["name"] and id(o) in slots and id(s) in slots:
                a, b = cxy(o), cxy(s)
                n = 12
                for i in range(0, n, 2):
                    p0 = (a[0] + (b[0] - a[0]) * i / n, a[1] + av // 2 + (b[1] - a[1] - av // 2) * i / n)
                    p1 = (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + av // 2 + (b[1] - a[1] - av // 2) * (i + 1) / n)
                    pygame.draw.line(screen, LINE, p0, p1, 1)
    # people on top
    def tg(p):
        if p is me:
            return "You " + str(age)
        if p is partner:
            return ("Spouse " if partner.get("married") else "Partner ") + str(partner["age"])
        if p in pars:
            return tag_par(p)
        if p in sibs:
            return tag_sib(p)
        return tag(p)
    for pid, (sl, r) in slots.items():
        p = people_by_id.get(pid)
        if p is None:
            continue
        x_, y_ = cxy(p)
        if y_ < body.y - 80 or y_ > body.bottom:
            continue
        ok = p.get("is_child") or p.get("is_grand") or p.get("category") == "partner"
        _node(screen, x_, y_, p, mouse, hits, tg(p), av=av, heir=(state.get("heir_name") == p["name"] and p is not me and ok), me=(p is me))
    screen.set_clip(clip)
    return scr

def draw_family_tab(screen, rect, mouse_pos, state, people, partner, me_look, player_name, age):
    """Plain tree drawn straight on the background: no boxes. Scroll with the wheel."""
    hits, views = [], {}
    view = state.get("_fam_view", "tree")
    draw_text(screen, "Family", font, INK, rect.x, rect.y - 2)
    xs = 80
    for i, (k, lab, w) in enumerate((("tree", "Tree", 56), ("grow", "Grow family", 100), ("heir", "Heirlooms", 90))):
        r = pygame.Rect(rect.x + xs, rect.y - 2, w, 24)
        xs += w + 8
        _pill(screen, r, lab, mouse_pos, view == k)
        views[k] = r
    sur = pygame.Rect(rect.right - 120, rect.y - 2, 120, 24)
    if state.get("_surrender_ask"):
        draw_text(screen, "End this life?", small_font, RED, rect.right - 290, rect.y + 3)
        yes = pygame.Rect(rect.right - 180, rect.y - 2, 56, 24)
        no = pygame.Rect(rect.right - 120, rect.y - 2, 56, 24)
        _pill(screen, yes, "Yes", mouse_pos)
        _pill(screen, no, "No", mouse_pos)
        views["sur_yes"], views["sur_no"] = yes, no
    else:
        draw_text(screen, "Give up this life", small_font, (170, 90, 90) if sur.collidepoint(mouse_pos) else MUTED, sur.centerx, sur.centery, centre=True)
        views["sur"] = sur
    body = pygame.Rect(rect.x, rect.y + 28, rect.width, rect.height - 28)
    b = {"hits": hits, "views": views, "discard": []}
    if view == "heir":
        _draw_heirlooms(screen, body, mouse_pos, state, b)
        return b
    if view == "grow":
        import kids
        kids.draw_grow(screen, body, mouse_pos, state, people, partner, age, b)
        return b
    ev = estate_value(state)
    draw_text(screen, f"Estate ${fmt(ev)}", small_font, GREEN, rect.x + 360, rect.y + 2)
    gps = [p for p in people if is_grandparent(p["relation"])]
    pars = [p for p in people if p["relation"] in ("Mother", "Father") or p.get("is_other_parent")]
    aunts = [p for p in people if p["relation"] in ("Aunt", "Uncle")]
    sibs = [p for p in people if "Sibling" in p["relation"]]
    kids = [p for p in people if p.get("is_child")]
    grands = [p for p in people if is_grandchild(p)]
    me = {"name": player_name, "gender": me_look[0], "age": age,
          "look": {"hair": list(me_look[1]), "style": me_look[2], "skin": list(me_look[3]), "facial": me_look[4], "feat": state.get("feat")}}
    def tag_par(p):
        if p.get("is_other_parent"):
            return f"{'Mum' if p['gender'] == 'Female' else 'Dad'} of {p.get('for_sibling', '?').split()[0]}"
        return f"{short_rel(p['relation'])} {p['age']}"
    def tag_sib(p):
        t = f"{short_rel(p['relation'])} {p['age']}"
        return t
    sc = _draw_tree(screen, body, mouse_pos, state, me, age, gps, pars, aunts, sibs, kids, grands, partner, people, hits, tag_par, tag_sib)
    if sc:
        pass
    if not (kids or partner or grands):
        draw_text(screen, "No heirs yet: have a child or marry so your story goes on.", small_font, MUTED, rect.x + 8, rect.bottom - 22)
    return b

def _draw_heirlooms(screen, body, mouse, state, b):
    hl = state.get("heirlooms", [])
    if not hl:
        draw_text(screen, "No heirlooms yet. Relatives sometimes leave you one when they pass away.", small_font, MUTED, body.x, body.y + 10)
        draw_text(screen, "Kept heirlooms grow in value every year and pass on to your heir.", small_font, MUTED, body.x, body.y + 32)
        return
    draw_text(screen, "Kept heirlooms gain value each year and pass to your heir.", small_font, MUTED, body.x, body.y + 2)
    y = body.y + 26
    for i, h in enumerate(hl[:9]):
        draw_text(screen, h["name"], font, INK, body.x, y)
        draw_text(screen, f"from {h['from']}" + (f", {h['gens']} generations" if h.get("gens") else ""), small_font, MUTED, body.x + 200, y + 3)
        draw_text(screen, f"${fmt(h['value'])}", font, GREEN, body.x + 440, y)
        r = pygame.Rect(body.right - 80, y - 2, 74, 24)
        _pill(screen, r, "Discard", mouse)
        b["discard"].append((h, r))
        y += 30

def handle_family_click(mx, my, b, state):
    for k, r in b.get("views", {}).items():
        if r.collidepoint(mx, my):
            if k in ("tree", "heir", "grow"):
                state["_fam_view"] = k
            elif k == "sur":
                state["_surrender_ask"] = True
            elif k == "sur_no":
                state["_surrender_ask"] = False
            elif k == "sur_yes":
                state["_surrender_ask"] = False
                state["_surrender"] = True
            return
    for key, r in b.get("grow", []):
        if r.collidepoint(mx, my):
            return ("grow", key)
    for h, r in b.get("discard", []):
        if r.collidepoint(mx, my):
            state["heirlooms"].remove(h)
            if not state["heirlooms"]:
                state["owned"].discard("heirloom")
            return
    for p, r in b.get("hits", []):
        if r.collidepoint(mx, my):
            if p.get("is_child") or is_grandchild(p) or p.get("category") == "partner":
                state["heir_name"] = None if state.get("heir_name") == p["name"] else p["name"]
            return

# ---- succession: step 1, who and from what age --------------------------------------
def _btn(screen, r, label, mouse, big=False, hot=True):
    col = ((255, 140, 50) if r.collidepoint(mouse) else (235, 120, 40)) if hot else (70, 66, 86)
    draw_rounded_rect(screen, col, r, radius=12)
    draw_text(screen, label, font, (255, 255, 255), r.centerx, r.centery, centre=True)

async def succession_screen(screen, data, options, death_age, name, reason=""):
    """Step 1. Returns {"option": .., "age": ..} or None to end the family line."""
    clock = pygame.time.Clock()
    st = data["state"]
    ev = estate_value(st)
    sel = 0
    pref = st.get("heir_name")
    for i, o in enumerate(options):
        if o["p"]["name"] == pref:
            sel = i
    ages = {}
    while True:
        o = options[sel]
        opts_ages = start_ages(o["p"].get("age", 18))
        cur_age = ages.get(sel, o["p"].get("age", 18))
        rects = []
        n = len(options)
        cw = min(190, (SCREEN_WIDTH - 60) // max(1, n))
        x0 = (SCREEN_WIDTH - cw * n) // 2
        for i in range(n):
            rects.append(pygame.Rect(x0 + i * cw, 170, cw - 8, 300))
        age_rects = []
        ax = SCREEN_WIDTH // 2 - (len(opts_ages) * 76) // 2
        for i, a in enumerate(opts_ages):
            age_rects.append((a, pygame.Rect(ax + i * 76, 520, 70, 28)))
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
                    return {"option": options[sel], "age": cur_age}
                elif e.key == pygame.K_ESCAPE:
                    return None
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(rects):
                    if r.collidepoint(e.pos):
                        sel = i
                for a, r in age_rects:
                    if r.collidepoint(e.pos):
                        ages[sel] = a
                if go.collidepoint(e.pos):
                    return {"option": options[sel], "age": cur_age}
                if end.collidepoint(e.pos):
                    return None
        screen.fill((24, 22, 34))
        draw_text(screen, "Who carries the fire on?", title_font, (255, 236, 210), SCREEN_WIDTH // 2, 44, centre=True)
        draw_text(screen, f"{name} {'gave up this life' if reason == 'surrender' else 'died'} at {death_age}. Estate ${fmt(ev)}.", font, (200, 195, 215), SCREEN_WIDTH // 2, 92, centre=True)
        draw_text(screen, "Pick who you play next, and the age you pick the story back up.", small_font, (160, 155, 180), SCREEN_WIDTH // 2, 124, centre=True)
        mouse = pygame.mouse.get_pos()
        for i, (oo, r) in enumerate(zip(options, rects)):
            p = oo["p"]
            on = i == sel
            if on:
                pygame.draw.rect(screen, (255, 160, 70), r, 2, border_radius=14)
            elif r.collidepoint(mouse):
                pygame.draw.rect(screen, (90, 85, 110), r, 1, border_radius=14)
            g, hc, hs, sk, fh = _person_look(p)
            draw_avatar(screen, pygame.Rect(r.centerx - 60, r.y + 12, 120, 130), g, hc, hs, sk, fh, ages.get(i, p.get("age", 30)), 60, (p.get("look") or {}).get("feat"))
            draw_text(screen, p["name"], font, (255, 255, 255), r.centerx, r.y + 154, centre=True)
            draw_text(screen, f"{oo['kind']}, age {p.get('age', '?')}", small_font, (190, 185, 205), r.centerx, r.y + 178, centre=True)
            job = P.occupation(p) if p.get("age", 0) >= 18 else "Too young to work"
            draw_text(screen, job[:26], small_font, (160, 155, 180), r.centerx, r.y + 198, centre=True)
            st_ = p.get("stats", {})
            draw_text(screen, f"Looks {st_.get('looks', 0)}  Social {st_.get('social', 0)}", small_font, (160, 155, 180), r.centerx, r.y + 232, centre=True)
            draw_text(screen, f"Brains {st_.get('academic', 0)}  Athletic {st_.get('athletic', 0)}", small_font, (160, 155, 180), r.centerx, r.y + 250, centre=True)
            if pref == p["name"]:
                draw_text(screen, "Named in your will", small_font, (255, 190, 110), r.centerx, r.y + 278, centre=True)
        draw_text(screen, "Start their life at age", small_font, (160, 155, 180), SCREEN_WIDTH // 2, 500, centre=True)
        for a, r in age_rects:
            on = a == cur_age
            if on:
                draw_rounded_rect(screen, (255, 140, 50), r, radius=10)
            draw_text(screen, ("Birth" if a == 0 else str(a)) + (" (now)" if a == o["p"].get("age", 18) else ""), small_font, (255, 255, 255) if on else (190, 185, 205), r.centerx, r.centery, centre=True)
        _btn(screen, go, "Next: the will", mouse)
        draw_text(screen, "End the family line", small_font, (170, 165, 190), end.centerx, end.centery, centre=True)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

# ---- succession: step 2, the will ----------------------------------------------------
ASSET_CYCLE = {"asset": ["heir", "sell", "charity"], "heirloom": ["keep", "discard"]}
ASSET_LABEL = {"heir": "Heir keeps", "sell": "Sell for cash", "charity": "Give to charity", "keep": "Keep", "discard": "Delete"}

async def will_screen(screen, data, option, options, plan):
    """Step 2. Edits `plan` and returns it, or None to go back."""
    clock = pygame.time.Clock()
    st = data["state"]
    heir_p = option["p"]
    others = [o for o in options if o is not option]
    entries = asset_entries(st)[:14]
    pool = max(0, pool_value(st))
    while True:
        mouse = pygame.mouse.get_pos()
        screen.fill((24, 22, 34))
        draw_text(screen, "The will", title_font, (255, 236, 210), SCREEN_WIDTH // 2, 40, centre=True)
        sold = sum(v for k, n_, v, t in entries if t == "asset" and plan["assets"].get(k) == "sell")
        total = pool + int(sold * 0.9)
        after = int(total * (1 - ESTATE_TAX))
        draw_text(screen, f"Cash and savings ${fmt(pool)}  +  sold assets ${fmt(int(sold * 0.9))}  -  {int(ESTATE_TAX * 100)}% estate tax  =  ${fmt(after)} to share out",
                  small_font, (190, 185, 205), SCREEN_WIDTH // 2, 80, centre=True)
        btns = []
        draw_text(screen, "Who gets the money", font, (255, 200, 140), 60, 112)
        y = 146
        rows = [(heir_p["name"] + " (you play)", None, heir_pct(plan))] + [(o["p"]["name"] + f" ({o['kind'].lower()})", o["p"]["name"], plan["pct"].get(o["p"]["name"], 0)) for o in others] + [("Charity", "_charity", plan["charity"])]
        for label, key, pct in rows:
            draw_text(screen, label[:28], font, (255, 255, 255), 60, y + 4)
            draw_text(screen, f"{pct}%", font, (120, 220, 150), 330, y + 4)
            draw_text(screen, f"${fmt(int(after * pct / 100))}", small_font, (160, 155, 180), 380, y + 7)
            if key is not None:
                m = pygame.Rect(270, y, 26, 28)
                pl = pygame.Rect(298, y, 26, 28)
                for r, s in ((m, "-"), (pl, "+")):
                    draw_rounded_rect(screen, (70, 66, 86) if not r.collidepoint(mouse) else (100, 94, 120), r, radius=8)
                    draw_text(screen, s, font, (255, 255, 255), r.centerx, r.centery, centre=True)
                btns.append((key, -5, m))
                btns.append((key, 5, pl))
            y += 40
        draw_text(screen, "Charity gifts are good for the soul. Other heirs add the money to their own savings.", small_font, (130, 126, 150), 60, y + 6)
        _tt = __import__("titles")
        if st.get("title"):
            heir_kind = next((o["kind"] for o in options if o["p"] is heir_p), "Child")
            nt = _tt.pass_on(st["title"], heir_kind)
            lab = _tt.label(st, data.get("gender"))
            draw_text(screen, f"Title: {lab} " + (f"passes to {heir_p['name'].split()[0]}." if nt else "does not pass to a partner. It ends with you."),
                      small_font, (255, 200, 140), 60, y + 30)
        # assets
        draw_text(screen, "Property, businesses and heirlooms", font, (255, 200, 140), 500, 112)
        ay = 146
        abtns = []
        if not entries:
            draw_text(screen, "Nothing to hand out here.", small_font, (130, 126, 150), 500, ay)
        for k, nm, val, typ in entries:
            cur = plan["assets"].get(k, ASSET_CYCLE[typ][0])
            draw_text(screen, nm[:22], small_font, (255, 255, 255), 500, ay + 5)
            draw_text(screen, f"${fmt(val)}", small_font, (120, 220, 150), 650, ay + 5)
            r = pygame.Rect(740, ay, 130, 24)
            draw_rounded_rect(screen, (70, 66, 86) if not r.collidepoint(mouse) else (100, 94, 120), r, radius=8)
            draw_text(screen, ASSET_LABEL[cur], small_font, (255, 255, 255), r.centerx, r.centery, centre=True)
            abtns.append((k, typ, r))
            ay += 30
        go = pygame.Rect(SCREEN_WIDTH // 2 - 130, 620, 260, 44)
        back = pygame.Rect(60, 628, 100, 30)
        _btn(screen, go, f"Play as {heir_p['name'].split()[0]}", mouse)
        draw_text(screen, "< Back", small_font, (170, 165, 190), back.centerx, back.centery, centre=True)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    return plan
                if e.key == pygame.K_ESCAPE:
                    return None
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if go.collidepoint(e.pos):
                    return plan
                if back.collidepoint(e.pos):
                    return None
                for key, d, r in btns:
                    if r.collidepoint(e.pos):
                        cur = plan["charity"] if key == "_charity" else plan["pct"].get(key, 0)
                        room = heir_pct(plan) if d > 0 else 100
                        new = max(0, min(100, cur + d)) if d < 0 else cur + min(d, room)
                        if key == "_charity":
                            plan["charity"] = new
                        else:
                            plan["pct"][key] = new
                for k, typ, r in abtns:
                    if r.collidepoint(e.pos):
                        cyc = ASSET_CYCLE[typ]
                        cur = plan["assets"].get(k, cyc[0])
                        plan["assets"][k] = cyc[(cyc.index(cur) + 1) % len(cyc)]

async def succession_flow(screen, final, options, death_age, name, reason=""):
    """Both screens. Returns the new life's save dict, or None."""
    while True:
        r = await succession_screen(screen, final, options, death_age, name, reason)
        if not r:
            return None
        plan = default_plan(final["state"], final["people"], final["partner"], r["option"], options)
        plan["age"] = r["age"]
        res = await will_screen(screen, final, r["option"], options, plan)
        if res:
            return build_heir_save(final, r["option"], res)

def build_heir_save(data, option, plan=None):
    """Turns the finished life (`data`, in the save format) into the save for
    the heir's new life."""
    p = option["p"]
    st = data["state"]
    people = data["people"]
    friends = data["friends"]
    old_partner = data["partner"]
    kind = option["kind"]
    old_age = p.get("age", 18)
    plan = plan or {"age": old_age, "pct": {}, "charity": 0, "assets": {}}
    age = plan.get("age", old_age)
    delta = age - old_age
    old_name = data["name"]
    lk = p["look"]

    # --- money: pool plus sold assets, tax, then the percentages ---
    entries = asset_entries(st)
    sold = sum(v for k, n_, v, t in entries if t == "asset" and plan["assets"].get(k) == "sell")
    charity_assets = sum(v for k, n_, v, t in entries if t == "asset" and plan["assets"].get(k) == "charity")
    pool = pool_value(st) + int(sold * 0.9)
    after = int(max(0, pool) * (1 - ESTATE_TAX))
    hp = heir_pct(plan)
    if not plan["pct"] and not plan["charity"]:
        hp = int(share_for(kind, len(heirs(people, old_partner))) * 100)
    cash = int(after * hp / 100)
    charity_total = int(after * plan.get("charity", 0) / 100) + charity_assets
    new_debt = max(0, -pool)

    # --- the new cast of relatives ---
    new_people = []
    def rel(src, relation, cat="family"):
        c = dict(src)
        c["relation"] = relation
        c["category"] = cat
        for k in ("is_child", "is_grand", "kids", "parent_name", "is_other_parent", "for_sibling", "shared_parent", "other_parent"):
            c.pop(k, None)
        c["contacted"] = False
        return c
    if kind == "Child":
        if old_partner and old_partner.get("name") != p["name"]:
            new_people.append(rel(old_partner, "Mother" if old_partner["gender"] == "Female" else "Father"))
        for c in people:
            if c.get("is_child") and c["name"] != p["name"]:
                new_people.append(rel(c, "Brother" if c["gender"] == "Male" else "Sister"))
            elif "Sibling" in c["relation"]:
                new_people.append(rel(c, "Uncle" if c["gender"] == "Male" else "Aunt"))
        for c in people:
            if is_grandchild(c) and c.get("parent_name") == p["name"]:
                new_people.append(rel(c, "Son" if c["gender"] == "Male" else "Daughter"))
                new_people[-1]["is_child"] = True
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
            if c.get("is_child") or is_grandchild(c):
                new_people.append(c)
    if age < 18 and not any(q["relation"] in ("Mother", "Father") for q in new_people):
        g = random.choice(["Male", "Female"])
        new_people.append(P.make_person("Father" if g == "Male" else "Mother", "family", g, closeness=65, age=age + random.randint(26, 36)))
    # shift ages if the new life starts at a different age
    if delta:
        for q in new_people:
            a = q.get("age", 30) + delta
            if q["relation"] in ("Mother", "Father"):
                a = max(a, age + 18)
            elif q["relation"].endswith(("Grandfather", "Grandmother")):
                a = max(a, age + 40)
            elif q["relation"] in ("Brother", "Sister"):
                a = max(0, a)
            q["age"] = max(0, a)
    for q in new_people:
        q.setdefault("stats", P.random_stats())
    people_out = [x for x in new_people if x.get("name") != p["name"]]
    # other chosen heirs who are still in the family get their share as savings
    for nm, pct in plan.get("pct", {}).items():
        for q in people_out:
            if q.get("name") == nm and pct:
                P.finances(q)["savings"] += int(after * pct / 100)

    stats = {"physical": max(30, min(90, 90 - max(0, age - 35))), "wealth": 10, "mental": 70}
    ps = p.get("stats") or P.random_stats()
    for k in P.STAT_KEYS:
        stats[k] = ps.get(k, 50)
    stats["wealth"] = min(100, cash // 500)

    # --- assets: each one goes to the heir, gets sold, or goes to charity ---
    props = [x for i, x in enumerate(st.get("properties", [])) if plan["assets"].get("prop%d" % i, "heir") == "heir"]
    cars = [x for i, x in enumerate(st.get("cars", [])) if plan["assets"].get("car%d" % i, "heir") == "heir"]
    bizs = [x for i, x in enumerate(st.get("businesses", [])) if plan["assets"].get("biz%d" % i, "heir") == "heir"]
    hls = []
    for i, h in enumerate(st.get("heirlooms", [])):
        if plan["assets"].get("hl%d" % i, "keep") == "keep":
            h = dict(h)
            h["gens"] = h.get("gens", 0) + 1
            hls.append(h)
    for b in bizs:
        if age < 21:
            b["run"] = "manager"
    pf = P.finances(p) if kind in ("Spouse", "Partner") else {"savings": 0}
    journal = [(age, f"You are {p['name']}. You carry on after {old_name}."), (age, f"You inherited ${fmt(cash)} (estate tax paid).")]
    if charity_total:
        journal.append((age, f"${fmt(charity_total)} from the estate went to charity."))
    new_state = {
        "stats": stats,
        "family_wealth": "Wealthy" if cash > 400000 else ("Comfortable" if cash > 40000 else "Struggling"),
        "debt": new_debt, "savings": 0, "invest": 0, "home": None,
        "money": cash + pf.get("savings", 0), "age": age,
        "actions_remaining": 20, "actions_used": {}, "life_event_resolved": False,
        "journal": journal,
        "owned": ["heirloom"] if hls else [],
        "activities": {}, "scholarship": False,
        "player_traits": list(p.get("traits", random.sample(P.TRAITS, 2))), "feat": dict(lk.get("feat") or {}),
        "gender": p["gender"], "attracted": p.get("attracted", "Both"),
        **({"title": tt} if (tt := __import__("titles").pass_on(st.get("title"), kind)) else {}),
        "skills": {}, "aspiration": random.choice(["Wealthy", "Family-minded", "Scholar", "Athlete", "Social butterfly", "Soulmate", "Performer"]),
        "aspiration_done": False,
        "properties": props, "cars": cars, "businesses": bizs, "heirlooms": hls, "_biz_migrated": True,
        "achievements": st.get("achievements", []),
        "generation": st.get("generation", 1) + 1,
        "lineage": (st.get("lineage", []) + [old_name]),
        "charity_total": st.get("charity_total", 0) + charity_total,
        "econ_v": 2,
    }
    career = {"education": "High School" if age >= 18 else "None", "enrolled": False, "uni_target": None, "uni_years_done": 0,
              "college_name": None, "college_prestige": 0, "prestige": 0, "course": None,
              "pending_course": None, "job": None, "browsing_jobs": False, "scroll": 0,
              "side_job": None, "fame": 0, "experience": 0, "hustle": None}
    return {"gender": p["gender"], "name": p["name"], "hair_colour": list(lk["hair"]), "hairstyle": lk["style"],
            "skin_tone": list(lk["skin"]), "facial_hair": lk.get("facial", "None"),
            "stats": stats, "history": [dict(stats)], "last_event_text": {}, "recent_events": [],
            "people": people_out,
            "friends": [f for f in friends if f.get("category") == "friend"][:3] if kind in ("Spouse", "Partner") else [],
            "partner": None, "career": career, "state": new_state, "age": age}
