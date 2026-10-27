import os,random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame;pygame.init();screen=pygame.display.set_mode((900,700))
from constants import *
import main, people as P, career as C, activities as A, shop as S, life as L, events as EV
random.seed(9)
R=pygame.Rect(200,320,675,320)
def mk(age):
    return {"stats":{k:60 for k in STAT_ORDER},"money":50,"actions_remaining":12,"actions_used":{},"age":age,"activities":{},"skills":{},"owned":set(),"bought_this_year":set(),"journal":[],"family_wealth":"Comfortable","parents_ok":True,"debt":0,"savings":0,"invest":0,"home":None,"gender":"Male","attracted":"Both","player_traits":[]}
# kid event cost covered
st=mk(9); out=main.apply_consequence(st,{"money":-5,"physical":1}); print("kid money",st["money"],EV.describe(out))
st=mk(30); out=main.apply_consequence(st,{"money":-5}); print("adult money",st["money"])
# lessons: parents
st=mk(10); b={"outs":[(A.OUTINGS[5],pygame.Rect(0,0,300,36))],"views":{},"acts":[]}
logs=[]
for _ in range(4):
    st["actions_used"]={}; A.handle_activities_click(5,5,b,st,10,[],lambda:None,logs.append)
print(logs[-3:],st["money"],st["skills"])
st=mk(10); st["family_wealth"]="Struggling"; st["parents_ok"]=False; logs=[]; A.handle_activities_click(5,5,b,st,10,[],lambda:None,logs.append); print(logs)
# inheritance
st=mk(30); fam=[P.make_person("Mother","family","Female",70,age=99),P.make_person("Paternal Grandfather","family","Male",60,age=99)]
logs=[]
for _ in range(6): P.advance_deaths(fam,[],None,st,logs.append)
print(logs, st["money"], st["home"], st["owned"])
# yearly costs
st=mk(30); L.yearly_costs(st,{}, 30, True); print("rent",st["money"])
st["home"]={"name":"x","value":100}; L.yearly_costs(st,{},30,True); print(st["home"])
st=mk(20); L.yearly_costs(st,{},20,True); print("with parents",st["money"])
st=mk(12); L.health_year(st,12); L.report_card(st,12); L.invest_year(st); print(st["journal"], st["money"])
# retirement
st=mk(67); car={"job":{"title":"Engineer","pay":60},"side_job":None}; L.retirement_year(car,st,67); print(car["job"],st["money"],st["pension"])
# shop paging, bank
st=mk(25); st["money"]=1000
for pg in (0,1):
    st["shop_page"]=pg; st["shop_view"]="shop"; b=S.draw_shop_tab(screen,R,(0,0),st,25); print(pg,len(b["items"]),list(b["views"]))
st["shop_page"]=0
for key,r in [(k,r) for k,r in S.draw_shop_tab(screen,R,(0,0),st,25)["views"].items() if k=="next"]: pass
b=S.draw_shop_tab(screen,R,(0,0),st,25); S.handle_shop_click(*b["views"]["next"].center,b,st,25,lambda t:None); print("page",st["shop_page"])
st["shop_page"]=0; b=S.draw_shop_tab(screen,R,(0,0),st,25)
for it,r in b["items"]:
    if it["id"] in("licence","car","flat"): S.handle_shop_click(*r.center,b,st,25,lambda t:None); b=S.draw_shop_tab(screen,R,(0,0),st,25)
st["shop_page"]=1; b=S.draw_shop_tab(screen,R,(0,0),st,25)
for it,r in b["items"]:
    if it["id"] in("licence","car","flat","house"): S.handle_shop_click(*r.center,b,st,25,lambda t:None); b=S.draw_shop_tab(screen,R,(0,0),st,25)
print("owned",st["owned"],st["home"],st["money"])
st["shop_view"]="bank"; b=S.draw_shop_tab(screen,R,(0,0),st,25); pygame.image.save(screen,"/tmp/t_bank2.png")
for k,r in b["bank"]: S.handle_shop_click(*r.center,b,st,25,lambda t:None); b=S.draw_shop_tab(screen,R,(0,0),st,25)
print("after bank",st["money"],st["invest"],st["home"])
# hustle
st=mk(15); st["stats"].update(social=60); car={"education":"None","enrolled":False,"job":None,"side_job":None,"fame":0,"view":"fame","hustle":None,"browsing_jobs":False,"scroll":0,"experience":0}
b=C.draw_career_tab(screen,R,(0,0),car,st); print(list(b))
C.handle_career_click(*b["hustles"][0][1].center,b,car,st); print(car["hustle"]["title"])
b=C.draw_career_tab(screen,R,(0,0),car,st); pygame.image.save(screen,"/tmp/t_fame2.png")
for k in [x for x in b if x.startswith("f_")]: C.handle_career_click(*b[k].center,b,car,st)
print(st["journal"][-3:],car["fame"]); C.advance_career_year(car,st,15); print(car["fame"],st["money"])
b["view_work"]=b["view_work"]; C.handle_career_click(*b["view_work"].center,b,car,st); b=C.draw_career_tab(screen,R,(0,0),car,st); print(list(b))
