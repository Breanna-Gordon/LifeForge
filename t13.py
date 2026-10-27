import os,random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame; pygame.init(); pygame.display.set_mode((900,700))
import romance as R, people as P
random.seed(11)
def st(m=100000):
    return {"stats":{k:70 for k in ("physical","mental","social","academic","looks","athletic","wealth")},"money":m,"age":28,"journal":[],"player_traits":["kind"],"gender":"Male","attracted":"Women","actions_remaining":5,"actions_used":{"__propose__":1},"parents_ok":True,"family_wealth":"Wealthy","debt":0}
L=[]; lg=L.append
p=P.make_person("Partner","partner","Female",closeness=80,age=28); p["trust"]=80; p["romance"]=80; p["compat"]=70; p["years"]=3
print("fin",P.finances(p),P.wealth_tier(p),P.money_lines(p))
s=st()
for tries in range(6):
    R.resolve_card({"kind":"ringchoice","person":p},"Lavish $15,000",p,[],s,lg)
    if p.get("engaged"): break
print("engaged",p.get("engaged"),p.get("ring"))
inv={"kind":"weddingchoice","person":p}
R.resolve_card(inv,"Grand $50,000",p,[],s,lg); print("married",p["married"],p["relation"],s["money"])
poor=st(100); p2=P.make_person("Partner","partner","Female",closeness=80,age=28); p2["engaged"]=True
inv2={"kind":"weddingchoice","person":p2}; R.resolve_card(inv2,"Classic $15,000",p2,[],poor,lg); print("retry",inv2.get("_retry"))
# merge
before=s["money"]; ok=any(R.try_merge(p,s,lg) for _ in range(8)); print("merged",p.get("merged"),s["money"]-before, R.household_income(p))
print(P.profile_names(p,{"_has_partner":True,"actions_remaining":3,"gender":"Male","attracted":"Women"},28))
# proposed
random.seed(3); hit=0
for i in range(200):
    q=P.make_person("Partner","partner","Female",closeness=80,age=28); q["trust"]=80;q["romance"]=80;q["years"]=3
    q2,cards=R.romance_year(st(),28,q,[],lg,lambda:P.make_person("A","partner","Female"),0)
    hit+=any(c["kind"]=="proposed" for c in cards)
print("proposal cards of 200:",hit)
c={"kind":"proposed","person":q,"ring":"classic"}; R.resolve_card(c,"Say yes",q,[],st(),lg); print("engaged by proposal",q["engaged"])
print([l for l in L][-5:])
