import os,random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame; pygame.init(); pygame.display.set_mode((900,700))
import career as C
random.seed(2)
def mkstate(age=25, fame=0):
    st={"stats":{k:70 for k in ("physical","mental","social","academic","looks","athletic","wealth")},"money":0,"age":age,"journal":[],"owned":set(),"activities":{"drama":3},"skills":{},"actions_remaining":12,"actions_used":{},"debt":0,"savings":0,"family_wealth":"Comfortable"}
    car={"education":"None","enrolled":False,"uni_target":None,"uni_years_done":0,"prestige":0,"course":None,"job":None,"side_job":None,"fame":fame,"experience":0,"hustle":None}
    return st,car
for fame in (0,30,60,90):
    st,car=mkstate(fame=fame)
    ok,_=C.eligible_jobs(car,st)
    actor=[j for j in ok if j["title"]=="Actor"]
    print("fame",fame,"actor offered:",bool(actor),"start pay",actor[0]["pay"] if actor else None)
# career run for actor w/ fame 60
st,car=mkstate(fame=60)
car["job"]=C._new_job([j for j in C.eligible_jobs(car,st)[0] if j["title"]=="Actor"][0])
for y in range(8):
    st["age"]+=1; car["fame"]=min(100,car["fame"]+8); car["job"]["perf"]=min(100,car["job"]["perf"]+10)
    m0=st["money"]; C.advance_career_year(car,st,st["age"])
    print(st["age"],car["job"]["title"],"pay",car["job"]["pay"],"fame",car["fame"],"earned",st["money"]-m0)
print([t for _,t in st["journal"] if "romot" in t][:5])
st,car=mkstate(age=18); car["job"]=C._new_job(C.JOB_TIERS[0])
for y in range(5):
    st["age"]+=1; m0=st["money"]; C.advance_career_year(car,st,st["age"]); print("cashier",car["job"]["title"] if car["job"] else None,st["money"]-m0)
