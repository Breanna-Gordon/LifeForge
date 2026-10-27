import os,random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame; pygame.init(); pygame.display.set_mode((900,700))
import lifestyle as L, achievements as A
random.seed(5)
def mk(age, money=1000):
    st={"stats":{k:60 for k in ("physical","mental","social","academic","looks","athletic","wealth")},"money":money,"age":age,"actions_remaining":999,
        "actions_used":{},"journal":[],"owned":set(),"activities":{},"skills":{},"parents_ok":True,"family_wealth":"Wealthy","_has_partner":True,"debt":0}
    L.ensure_state(st); return st
logs=[]
fr=[{"name":"F","closeness":50}]
mf=lambda: {"name":"N"}
count=0
for age in (6,12,16,20,40):
    for cat in list(L.ITEMS)+["industries"]:
        st=mk(age); car={"fame":50,"job":None,"enrolled":True}
        for it in L.items_for(cat,st,age):
            for _ in range(3):
                L._use(it,st,age,car,fr,mf,logs.append); count+=1
                st["actions_remaining"]=999
                if st["jail"]: st["jail"]=0
            assert st["money"]>=-10000
        L.advance_lifestyle_year(st,car,age,logs.append)
# money never reduced for kids beyond covered
st=mk(10,100); car={}
for it in L.ITEMS["mind"]+L.ITEMS["health"]+L.ITEMS["leisure"]:
    L._use(it,st,10,car,fr,mf,logs.append)
print("kid money after many activities:",st["money"])
assert st["money"]==100
# crime -> prison
st=mk(20,100); car={"job":{"title":"x"},"enrolled":False}
for _ in range(60):
    it=[i for i in L.ITEMS["crime"] if i["id"]=="burgle"][0]
    L._use(it,st,20,car,fr,mf,logs.append)
    if st["jail"]: break
print("jail",st["jail"],"job",car["job"],"record",st["record"])
A.check_achievements(st,car,fr,None,[],logs.append); print(st["achievements"][:5])
print("items run:",count)
print([l for l in logs if "business" in l][:3])
