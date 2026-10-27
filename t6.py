import os,random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame;pygame.init()
from constants import *
import career as C, education as E, shop as S
screen=pygame.display.set_mode((900,700))
R=pygame.Rect(200,320,675,320)
random.seed(4)
def mk():
    return {"stats":{k:60 for k in STAT_ORDER},"money":150,"actions_remaining":12,"actions_used":{},"age":18,"activities":{},"skills":{"singing":3},"owned":set(),"bought_this_year":set(),"journal":[],"family_wealth":"Wealthy","parents_ok":True,"debt":0,"savings":0}
car={"education":"None","enrolled":False,"uni_target":None,"uni_years_done":0,"college_name":None,"college_prestige":0,"prestige":0,"course":None,"pending_course":None,"job":None,"browsing_jobs":False,"scroll":0,"side_job":None,"fame":0,"experience":0}
st=mk(); st["stats"]["academic"]=80
def bg(): screen.fill((232,222,248)); pygame.draw.rect(screen,WHITE,R.inflate(10,10),border_radius=8)
# education: choose course then apply
bg(); b=E.draw_education_tab(screen,R,(0,0),18,st,car)
E.handle_education_click(*b["courses"][3][1].center,b,18,st,car)
bg(); b=E.draw_education_tab(screen,R,(0,0),18,st,car); print(list(b))
E.handle_education_click(*b["colleges"][-1][1].center,b,18,st,car); print("pending",car["pending_apply"]["college"]["name"])
bg(); b=E.draw_education_tab(screen,R,(0,0),18,st,car); pygame.image.save(screen,"/tmp/t_fund.png"); print(list(b))
k=[x for x in b if x.startswith("fund_") and x!="fund_cancel"][0]
E.handle_education_click(*b[k].center,b,18,st,car); print("enrolled",car["enrolled"],car["funding"])
for y in range(3): C.advance_career_year(car,st,18+y)
print(car["education"],car["prestige"],st["debt"],st["money"])
# poor family loan
st=mk(); st["family_wealth"]="Struggling"; car.update(enrolled=False,education="None",pending_course="Law",course=None)
car["pending_apply"]={"level":"Bachelor's","college":E.COLLEGES["Bachelor's"][1],"course":"Law"}
E._start_course(st,car,"loan"); C.advance_career_year(car,st,19); print("debt",st["debt"],car["funding"]["owe"])
# vocational
st=mk(); car2=dict(car,enrolled=False,education="None",funding=None,job=None)
car2["pending_apply"]={"level":"Diploma","college":E.COLLEGES["Diploma"][0],"course":"Electrician"}
E._start_course(st,car2,"savings")
for y in range(2): C.advance_career_year(car2,st,17+y)
print(car2["education"],car2.get("trade"),[j["title"] for j in C.eligible_jobs(car2,st)[0]][:4])
# jobs
car2["job"]=C._new_job([j for j in C.JOB_TIERS if j["title"]=="Electrician"][0])
bg(); b=C.draw_career_tab(screen,R,(0,0),car2,st); print(list(b))
for k in ("ot","net"): C.handle_career_click(*b[k].center,b,car2,st)
car2["job"]["since"]=3
for _ in range(5): C.handle_career_click(*b["promo"].center,b,car2,st); 
print(car2["job"]["title"],car2["job"]["pay"])
# side job
b["side_find"]=pygame.Rect(0,0,10,10); C.handle_career_click(5,5,b,car2,st)
bg(); b=C.draw_career_tab(screen,R,(0,0),car2,st); C.handle_career_click(*b["jobs"][0][1].center,b,car2,st); print("side",car2["side_job"]["title"])
# fame job
st["stats"]["looks"]=80; st["stats"]["social"]=70
car2["job"]=C._new_job([j for j in C.JOB_TIERS if j["title"]=="Model"][0]); car2["fame"]=35
bg(); b=C.draw_career_tab(screen,R,(0,0),car2,st); pygame.image.save(screen,"/tmp/t_fame.png")
for k in [x for x in b if x.startswith("f_")]:
    C.handle_career_click(*b[k].center,b,car2,st)
print([t for a,t in st["journal"][-7:]], car2["fame"])
C.advance_career_year(car2,st,22); print("fame after year",car2["fame"])
# bank
st["debt"]=100; st["age"]=22
bg(); st["shop_view"]="bank"; b=S.draw_shop_tab(screen,R,(0,0),st,22); pygame.image.save(screen,"/tmp/t_bank.png")
for key,r in b["bank"]:
    S.handle_shop_click(*r.center,b,st,22,lambda t:None)
print("bank",st["money"],st["savings"],st["debt"])
