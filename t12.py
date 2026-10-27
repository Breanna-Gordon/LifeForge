import os,random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame; pygame.init(); pygame.display.set_mode((900,700))
import romance as R, people as P
random.seed(7)
def st():
    s={"stats":{k:70 for k in ("physical","mental","social","academic","looks","athletic","wealth")},"money":50000,"age":25,"journal":[],"player_traits":["kind"],"gender":"Male","attracted":"Women","actions_remaining":12,"actions_used":{}}
    return s
logs=[]; L=logs.append
kinds=set(); ended=0
for trial in range(400):
    s=st(); friends=[]
    partner=P.make_person("Partner","partner","Female",closeness=50,age=25); partner["romance"]=random.randint(10,80); partner["trust"]=random.randint(10,80); partner["compat"]=60
    if trial%3==0: partner["status"]="situationship"
    if trial%5==0: partner["married"]=True
    if trial%4==0: s["fling"]=P.make_person("Admirer","partner","Female",closeness=40,age=25)
    for y in range(10):
        if partner is None: break
        partner,cards=R.romance_year(s,26+y,partner,friends,L,lambda: P.make_person("Admirer","partner","Female",closeness=40,age=25),30)
        for c in cards:
            kinds.add(c["kind"])
            pick=random.choice(R.LABELS[c["kind"]])
            partner=R.resolve_card(c,pick,partner,friends,s,L)
            if partner is None: break
print("card kinds",kinds)
# break up + get back + official
s=st(); friends=[]; p=P.make_person("Partner","partner","Female",closeness=60,age=25); p["compat"]=60; p["status"]="situationship"
for _ in range(5): R.make_official(p,s,L)
print("status after official tries",p.get("status"))
R.break_up(p,friends,s,L); print(p["category"],p["relation"])
if p["category"]=="friend":
    ok=any(R.get_back_together(dict(p),s,L) for _ in range(10)); print("get back possible",ok)
print(P.profile_names(p,{"_has_partner":False,"actions_remaining":3,"gender":"Male","attracted":"Women"},25))
print([l for l in logs if "cheat" in l.lower() or "ghost" in l.lower()][:4])
# labels all valid
for k,v in R.LABELS.items(): assert k in R.HEADS
print("ok")
