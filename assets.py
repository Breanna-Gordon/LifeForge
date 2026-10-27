"""Properties and cars: buy several, live in one, rent out the rest, and
look after your cars. Drawn as the 'Assets' view of the Shop tab."""
import random
import pygame
from constants import (INK, DARK_GREY, GREEN, RED, font, small_font, draw_text,
                       draw_card, draw_pill, fmt, fmt_short)

PROPERTIES = [
    ("Studio flat", 90000, 0.035), ("City flat", 180000, 0.04), ("Townhouse", 320000, 0.04),
    ("Family house", 550000, 0.045), ("Country villa", 1500000, 0.05), ("Penthouse", 4000000, 0.055),
    ("Grand mansion", 12000000, 0.06), ("Private island", 40000000, 0.065),
]
CARS = [
    ("Used banger", 4000, 0.18), ("Hatchback", 18000, 0.13), ("Family SUV", 40000, 0.12),
    ("Sports car", 90000, 0.10), ("Luxury saloon", 160000, 0.10), ("Supercar", 400000, 0.07),
    ("Hypercar", 2000000, 0.04),
]
MAX_PROPS, MAX_CARS = 10, 8

def ensure(state):
    state.setdefault("properties", [])
    state.setdefault("cars", [])
    state.setdefault("asset_sub", "property")
    # older saves: a single `home` becomes the first property
    h = state.get("home")
    if h and not any(p is h for p in state["properties"]):
        for p in state["properties"]:
            if p.get("live") and p["name"] == h["name"] and p["value"] == h["value"]:
                state["home"] = p
                break
        else:
            h.setdefault("tier", 0)
            h["live"] = True
            state["properties"].append(h)
    sync(state)

def sync(state):
    """Keeps `home` (the place you live) and the car perk in step."""
    props = state["properties"]
    live = [p for p in props if p.get("live")]
    for extra in live[1:]:
        extra["live"] = False
    state["home"] = live[0] if live else None
    state["owned"].discard("flat"); state["owned"].discard("house")
    if state["cars"]:
        state["owned"].add("car")
    elif "car" in state["owned"]:
        state["owned"].discard("car")      # the perk follows the cars you actually own

def net_worth_assets(state):
    return sum(p["value"] for p in state.get("properties", [])) + sum(c["value"] for c in state.get("cars", []))

def _max_buy_ok(state, kind):
    return len(state["properties" if kind == "property" else "cars"]) < (MAX_PROPS if kind == "property" else MAX_CARS)

def buy_property(state, tier, mortgage, log):
    name, price, _ = PROPERTIES[tier]
    if not _max_buy_ok(state, "property"):
        return log("You own as many properties as you can manage.")
    if mortgage:
        down = price // 5
        if state["money"] < down:
            return log(f"You need ${fmt(down)} for the deposit.")
        state["money"] -= down
        state["debt"] = state.get("debt", 0) + price - down
        how = f"with a ${fmt(price - down)} mortgage"
    else:
        if state["money"] < price:
            return log(f"You can't afford the {name} yet.")
        state["money"] -= price
        how = "in cash"
    # a little haggling either way
    value = int(price * random.uniform(0.96, 1.06))
    p = {"name": name, "tier": tier, "value": value, "bought": price, "live": not state["properties"] or not state.get("home") and False,
         "rented": False, "reno": 0}
    state["properties"].append(p)
    if not state.get("home"):
        p["live"] = True
    sync(state)
    log(f"Bought a {name} for ${fmt(price)} {how}." + (" You moved in." if p["live"] else ""))

def buy_car(state, tier, log):
    name, price, _ = CARS[tier]
    if "licence" not in state["owned"]:
        return log("You need a driving licence first (buy driving lessons in the Shop).")
    if not _max_buy_ok(state, "car"):
        return log("Your garage is full.")
    if state["money"] < price:
        return log(f"You can't afford the {name} yet.")
    state["money"] -= price
    state["cars"].append({"name": name, "tier": tier, "value": price, "bought": price, "cond": 90, "age": 0})
    sync(state)
    log(f"Bought a {name} for ${fmt(price)}.")

# ---- actions on things you own -------------------------------------------
def prop_actions(p, state):
    acts = []
    if not p.get("live"):
        acts.append(("live", "Move in"))
    if not p.get("live"):
        acts.append(("rent", "Stop renting out" if p.get("rented") else "Rent it out"))
    acts.append(("reno", f"Renovate (${fmt_short(p['value'] // 10)})"))
    if p.get("tier", 0) >= 3:
        acts.append(("party", f"House party (${fmt_short(p['value'] // 100)})"))
    acts.append(("sell", f"Sell (${fmt_short(int(p['value'] * 0.97))})"))
    return acts

def car_actions(c, state):
    acts = [("wash", "Wash ($50)"), ("service", f"Service (${fmt_short(max(200, c['bought'] // 25))})")]
    if c["tier"] >= 1:
        acts.append(("trip", f"Road trip (${fmt_short(max(300, c['bought'] // 40))})"))
    if c["tier"] >= 3:
        acts.append(("race", "Street race"))
    if c["tier"] >= 1:
        acts.append(("tune", f"Upgrade (${fmt_short(c['bought'] // 8)})"))
    acts.append(("sell", f"Sell (${fmt_short(c['value'])})"))
    return acts

def do_prop(state, p, act, log):
    st = state["stats"]
    if act == "live":
        for q in state["properties"]:
            q["live"] = False
            q["rented"] = q["rented"] if q is not p else False
        p["live"] = True
        sync(state)
        log(f"You moved into your {p['name']}.")
    elif act == "rent":
        p["rented"] = not p.get("rented")
        log(f"Your {p['name']} is " + ("now rented out." if p["rented"] else "no longer rented out."))
    elif act == "reno":
        cost = p["value"] // 10
        if state["money"] < cost or state["actions_used"].get("reno" + str(id(p)), 0):
            return log("You can't renovate that right now." if state["money"] < cost else "It was already renovated this year.")
        state["money"] -= cost
        p["value"] = int(p["value"] * random.uniform(1.04, 1.14))
        state["actions_used"]["reno" + str(id(p))] = 1
        log(f"You renovated the {p['name']}. Its value rose to ${fmt(p['value'])}.")
    elif act == "party":
        cost = p["value"] // 100
        if state["money"] < cost or state["actions_used"].get("party", 0):
            return log("You can't throw a party right now." if state["money"] < cost else "One party a year is enough.")
        state["money"] -= cost
        state["actions_used"]["party"] = 1
        st["social"] = min(100, st["social"] + 5)
        st["mental"] = min(100, st["mental"] + 2)
        log(f"You threw a party at your {p['name']}. Everyone's talking about it.")
    elif act == "sell":
        got = int(p["value"] * 0.97)
        state["money"] += got
        state["properties"].remove(p)
        sync(state)
        log(f"Sold your {p['name']} for ${fmt(got)}." + ("" if state["home"] or not state["properties"] else ""))
        if not state["home"] and state["properties"]:
            state["properties"][0]["live"] = True
            sync(state)
            log(f"You moved into your {state['properties'][0]['name']}.")

def do_car(state, c, act, log):
    st = state["stats"]
    used = state["actions_used"]
    key = f"{act}{id(c)}"
    if act == "sell":
        state["money"] += c["value"]
        state["cars"].remove(c)
        sync(state)
        return log(f"Sold your {c['name']} for ${fmt(c['value'])}.")
    cost = {"wash": 50, "service": max(200, c["bought"] // 25), "trip": max(300, c["bought"] // 40),
            "tune": c["bought"] // 8, "race": 0}[act]
    if state["money"] < cost:
        return log("You can't afford that right now.")
    if used.get(key):
        return log("You've already done that this year.")
    used[key] = 1
    state["money"] -= cost
    if act == "wash":
        c["cond"] = min(100, c["cond"] + 4)
        log(f"Washed your {c['name']}. It gleams.")
    elif act == "service":
        c["cond"] = min(100, c["cond"] + 25)
        log(f"Serviced your {c['name']}. It runs like new.")
    elif act == "trip":
        st["mental"] = min(100, st["mental"] + 4); st["social"] = min(100, st["social"] + 2)
        c["cond"] = max(0, c["cond"] - 4)
        log(f"A road trip in your {c['name']} was just what you needed.")
    elif act == "tune":
        c["value"] = int(c["value"] * 1.06); c["cond"] = min(100, c["cond"] + 10)
        log(f"Upgraded your {c['name']}. It's worth a little more.")
    elif act == "race":
        r = random.random()
        st["social"] = min(100, st["social"] + 3)
        if r < 0.15:
            bill = c["value"] // 5
            state["money"] = max(0, state["money"] - bill)
            st["physical"] = max(0, st["physical"] - 6)
            c["cond"] = max(0, c["cond"] - 40)
            log(f"You crashed during a street race! Repairs and fines cost ${fmt(bill)}.")
        elif r < 0.3:
            fine = max(500, c["bought"] // 40)
            state["money"] = max(0, state["money"] - fine)
            state["record"] = state.get("record", 0) + 1
            log(f"The police stopped the race. You were fined ${fmt(fine)}.")
        else:
            win = c["bought"] // 20
            state["money"] += win
            log(f"You won a street race and ${fmt(win)} in side bets!")

# ---- yearly ----------------------------------------------------------------
def assets_year(state, age, log):
    ensure(state)
    st = state["stats"]
    for p in list(state["properties"]):
        _, _, drift = PROPERTIES[min(p.get("tier", 0), len(PROPERTIES) - 1)]
        p["value"] = max(1000, int(p["value"] * (1 + random.gauss(drift, 0.05))))
    # `life.yearly_costs` already grew your own home by 4%; the rest are handled here
    for p in state["properties"]:
        upkeep = int(p["value"] * (0.004 if p.get("live") else 0.008))
        state["money"] = max(0, state["money"] - upkeep)
        if p.get("rented"):
            if random.random() < 0.88:
                rent = int(p["value"] * 0.055)
                state["money"] += rent
                if p["value"] >= 1000000 and random.random() < 0.3:
                    log(f"Your {p['name']} earned ${fmt(rent)} in rent.")
            elif random.random() < 0.5:
                dmg = p["value"] // 100
                state["money"] = max(0, state["money"] - dmg)
                log(f"Tenants damaged your {p['name']}. Repairs cost ${fmt(dmg)}.")
    for c in list(state["cars"]):
        _, _, dep = CARS[c["tier"]]
        c["age"] += 1
        c["value"] = max(500, int(c["value"] * (1 - dep)))
        c["cond"] = max(0, c["cond"] - random.randint(4, 10))
        state["money"] = max(0, state["money"] - c["bought"] // 40)   # insurance and fuel
        if c["tier"] >= 3:
            st["social"] = min(100, st["social"] + 1)
        if c["tier"] >= 4:
            st["looks"] = min(100, st["looks"] + 1)
        if random.random() < 0.03 + (0.05 if c["cond"] < 30 else 0):
            bill = max(300, c["bought"] // 12)
            state["money"] = max(0, state["money"] - bill)
            log(f"Your {c['name']} was in a fender-bender. Repairs cost ${fmt(bill)}.")
        elif c["cond"] <= 10 and random.random() < 0.4:
            state["cars"].remove(c)
            log(f"Your {c['name']} broke down for good and was scrapped.")
    sync(state)

# ---- drawing ---------------------------------------------------------------
def _sub_tabs(screen, rect, mouse, state, hits):
    for n, (k, lab) in enumerate((("property", "Properties"), ("cars", "Cars"))):
        r = pygame.Rect(rect.x + 120 + n * 108, rect.y - 2, 100, 26)
        draw_pill(screen, r, lab, small_font, mouse, selected=state["asset_sub"] == k)
        hits.append((("sub", k), r))

def draw_assets(screen, rect, mouse, state, age):
    ensure(state)
    sub = state["asset_sub"]
    props = sub == "property"
    hits = []
    draw_text(screen, "Assets", font, INK, rect.x, rect.y)
    _sub_tabs(screen, rect, mouse, state, hits)
    owned = state["properties"] if props else state["cars"]
    worth = sum(x["value"] for x in owned)
    draw_text(screen, f"{'Property' if props else 'Cars'} worth ${fmt(worth)}   Cash ${fmt(state['money'])}   Debt ${fmt(state.get('debt', 0))}",
              small_font, DARK_GREY, rect.x, rect.y + 28)
    sel = state.get("asset_sel")
    obj = owned[sel] if isinstance(sel, int) and 0 <= sel < len(owned) else None
    if obj is not None:
        _detail(screen, rect, mouse, state, props, obj, hits)
        return hits
    # list: owned first, then things for sale
    rows = [("own", i, x) for i, x in enumerate(owned)] + [("buy", i, t) for i, t in enumerate(PROPERTIES if props else CARS)]
    per = 6
    pages = max(1, -(-len(rows) // per))
    page = max(0, min(state.get("asset_page", 0), pages - 1))
    state["asset_page"] = page
    if pages > 1:
        for k, lab, dx in (("prev", "<", 0), ("next", ">", 34)):
            r = pygame.Rect(rect.right - 338 + dx, rect.y - 2, 30, 26)
            draw_pill(screen, r, lab, small_font, mouse)
            hits.append((("page", k), r))
    y = rect.y + 50
    for kind, i, x in rows[page * per:(page + 1) * per]:
        r = pygame.Rect(rect.x, y, rect.width, 38)
        draw_card(screen, r, radius=10, shadow=False)
        if kind == "own":
            tag = "Lives here" if props and x.get("live") else "Rented out" if props and x.get("rented") else "Empty" if props else f"Condition {x['cond']}%"
            draw_text(screen, x["name"], small_font, INK, r.x + 12, r.y + 3)
            draw_text(screen, f"Worth ${fmt(x['value'])}   {tag}", small_font, DARK_GREY, r.x + 12, r.y + 20)
            b = pygame.Rect(r.right - 96, r.y + 5, 86, 28)
            draw_pill(screen, b, "Manage", small_font, mouse, primary=True)
            hits.append((("manage", i), b))
        else:
            name, price, _ = x
            ok_age = age >= (18 if props else 17)
            draw_text(screen, name, small_font, INK, r.x + 12, r.y + 3)
            sub_txt = (f"${fmt(price)}" + (f"   deposit ${fmt_short(price // 5)}" if props else "")) if ok_age else "Too young"
            draw_text(screen, sub_txt, small_font, DARK_GREY, r.x + 12, r.y + 20)
            b = pygame.Rect(r.right - 96, r.y + 5, 86, 28)
            can = ok_age and state["money"] >= price
            draw_pill(screen, b, "Buy", small_font, mouse, disabled=not can)
            hits.append((("buy", i), b)) if can else None
            if props:
                m = pygame.Rect(r.right - 196, r.y + 5, 92, 28)
                can_m = ok_age and age >= 21 and state["money"] >= price // 5
                draw_pill(screen, m, "Mortgage", small_font, mouse, disabled=not can_m)
                hits.append((("mortgage", i), m)) if can_m else None
        y += 42
    if not owned:
        pass
    return hits

def _detail(screen, rect, mouse, state, props, obj, hits):
    r = pygame.Rect(rect.x, rect.y + 50, rect.width, 262)
    draw_card(screen, r, radius=12, shadow=False)
    draw_text(screen, obj["name"], font, INK, r.x + 14, r.y + 8)
    bought = obj["bought"] if "bought" in obj else obj["value"]
    gain = obj["value"] - bought
    col = GREEN if gain >= 0 else RED
    draw_text(screen, f"Worth ${fmt(obj['value'])}", small_font, INK, r.x + 14, r.y + 38)
    draw_text(screen, f"{'+' if gain >= 0 else '-'}${fmt(abs(gain))} since you bought it", small_font, col, r.x + 150, r.y + 38)
    if props:
        status = "You live here" if obj.get("live") else "Rented out (about 5.5% a year)" if obj.get("rented") else "Empty (costs upkeep)"
    else:
        status = f"Condition {obj['cond']}%   Age {obj['age']} yrs   Loses value each year"
    draw_text(screen, status, small_font, DARK_GREY, r.x + 14, r.y + 60)
    acts = prop_actions(obj, state) if props else car_actions(obj, state)
    for n, (k, lab) in enumerate(acts):
        b = pygame.Rect(r.x + 14 + (n % 2) * 322, r.y + 92 + (n // 2) * 44, 310, 36)
        draw_pill(screen, b, lab, small_font, mouse, primary=(k == "sell"))
        hits.append((("act", k), b))
    back = pygame.Rect(r.right - 100, r.y + 8, 86, 28)
    draw_pill(screen, back, "Back", small_font, mouse)
    hits.append((("back", 0), back))

def handle_assets_click(mx, my, hits, state, age, log):
    ensure(state)
    for (kind, val), r in hits:
        if not r.collidepoint(mx, my):
            continue
        sub = state["asset_sub"]
        props = sub == "property"
        owned = state["properties"] if props else state["cars"]
        if kind == "sub":
            state["asset_sub"], state["asset_sel"], state["asset_page"] = val, None, 0
        elif kind == "page":
            state["asset_page"] = max(0, state.get("asset_page", 0) + (1 if val == "next" else -1))
        elif kind == "manage":
            state["asset_sel"] = val
        elif kind == "back":
            state["asset_sel"] = None
        elif kind in ("buy", "mortgage"):
            if props:
                buy_property(state, val, kind == "mortgage", log)
            else:
                buy_car(state, val, log)
        elif kind == "act":
            sel = state.get("asset_sel")
            if isinstance(sel, int) and 0 <= sel < len(owned):
                obj = owned[sel]
                (do_prop if props else do_car)(state, obj, val, log)
                if val == "sell" or val == "live":
                    state["asset_sel"] = None if val == "sell" else sel
        return True
    return False
