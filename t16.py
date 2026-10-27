import os,random
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame;pygame.init();screen=pygame.display.set_mode((900,700))
import main, love, people as P
from constants import *
random.seed(5)
stats=main.roll_stats()
state={"stats":stats,"money":150000,"age":27,"actions_remaining":20,"actions_used":{},"life_event_resolved":True,"journal":[],"owned":set(),"bought_this_year":set(),"activities":{},"gender":"Female","attracted":"Men","player_traits":["kind","funny"],"family_wealth":"Wealthy","_snapshot":[("Education","Bachelor's"),("Job","Doctor"),("Partner","None"),("Friends / enemies","3 / 0"),("Family wealth","Wealthy"),("Aspiration","Wealthy"),("Savings","$20")]}
career={"education":"None","fame":30,"job":{"title":"Doctor","base":"Doctor","pay":100000,"perf":60},"enrolled":False}
love.ensure(state)
fb=make_vertical_gradient(900,700,(255,235,205),(255,255,255))
out=pygame.Surface((1800,1400))
def snap(i,view):
    state["love_view"]=view
    main.draw_hub_frame(screen,"Mia",27,"Young Adult",stats,stats,(35,28,24),"Long",SKIN_TONES[2],"None","Female",{},None,fb,"Love",False,state,(0,0))
    b=love.draw_love_tab(screen,main.CONTENT_RECT,(0,0),state,27,career,None)
    out.blit(screen,((i%2)*900,(i//2)*700)); return b
# play: use apps
b=snap(0,"apps")
for a,r in b["apps"]:
    res=love.handle_love_click(r.centerx,r.centery,b,state,27,career,None,[],lambda t:print("LOG",t))
    if res and res[0]=="prospect":
        p=res[1]; print(a["id"],p["name"],p["job_title"],p["stats"]["looks"],p["compat"]); love.add_match(state,p,False)
        break
for aid in ("velvet","stardust","matchmaker","office","gold"):
    state["actions_remaining"]=20
    p=love.make_app_prospect(aid,state,27,career); print(aid,p["job_title"],p["age"],p["compat"],p["stats"]["looks"]); love.add_match(state,p,random.random()<.5)
for p in state["love"]: p["spark"]=random.randint(30,90); p["stage"]=random.choice(["Talking","Seeing"])
b=snap(1,"matches")
row=b["rows"][0]; r=row[1]["text"]
print(love.handle_love_click(r.centerx,r.centery,b,state,27,career,None,[],lambda t:print("LOG",t)))
r=row[1]["date"]; print(love.handle_love_click(r.centerx,r.centery,b,state,27,career,None,[],lambda t:print("LOG",t)))
b=snap(2,"social")
for a,r in b["social"]:
    for _ in range(3): love.social_post(a,state,27,career,lambda t:print("LOG",t))
b=snap(3,"social")
partner=P.make_person("Partner","partner","Male",70,28)
print(love.love_year(state,27,partner,[],career,lambda t:print("LOG",t)) is partner)
pygame.image.save(out,"/tmp/love_sheet.png")
