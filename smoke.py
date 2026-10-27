import os,asyncio,random
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame
pygame.init()
import main,events,shop
from constants import *
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
# logic sim: events never crash across all ages and contexts
career={"education":"None","enrolled":False,"job":{"title":"x","pay":1,"wealth":1},"college_name":None}
for age in range(0,100):
    st=main.get_age_stage(age)
    for partner in (None,{"name":"P"}):
        ctx={"career":career,"partner":partner,"friends":[1],"money":random.choice([0,500]),"stats":{"academic":70,"physical":30,"social":20,"mental":50,"wealth":50,"looks":70,"athletic":70}}
        for _ in range(20):
            evs=events.pick_year_events(age,ctx,main.choice_events[st]["choices"],main.special_events.get(st,{}),None)
            state={"stats":dict(ctx["stats"]),"money":50,"journal":[],"age":age}
            for t,o in evs:
                for k,v in o.items():
                    out=main.apply_consequence(state,v);events.describe(v);events.describe(out)
print("events ok")
# render each tab
state={"stats":{"physical":50,"wealth":50,"mental":50,"social":50,"academic":50},"money":120,"age":20,"actions_remaining":5,"actions_used":{},"life_event_resolved":True,
"journal":[(i//2,"Event text number %d You chose: Something."%i) for i in range(30)],"owned":{"bike"},"bought_this_year":{"treat"}}
career={"education":"None","enrolled":False,"uni_target":None,"uni_years_done":0,"college_name":None,"college_prestige":0,"prestige":0,"job":None,"browsing_jobs":False}
fb=make_vertical_gradient(SCREEN_WIDTH,SCREEN_HEIGHT,(255,235,205),WHITE)
people=main.generate_family()
for tab in main.TABS:
    main.draw_hub_frame(screen,"Sam",20,"Young Adult",state["stats"],state["stats"],(35,28,24),"Short",SKIN_TONES[2],"None","Male",{},None,fb,tab,tab=="Career",state,(0,0))
    if tab=="Life": main.draw_life_tab(screen,main.CONTENT_RECT,"Your boss offers you a project nobody else wants.",["Take it on","Politely refuse"],None,(0,0),True,0,"Wealth +3, Mental -3, +$20",True,1,2)
    if tab=="People": main.draw_people_tab(screen,main.CONTENT_RECT,people,[],None,0,(0,0),state,20,"Meet Someone New")
    if tab=="Education": main.draw_education_tab(screen,main.CONTENT_RECT,(0,0),20,state,career)
    if tab=="Career": main.draw_career_tab(screen,main.CONTENT_RECT,(0,0),career,state)
    if tab=="Shop": main.draw_shop_tab(screen,main.CONTENT_RECT,(0,0),state,20)
    if tab=="Journal": main.draw_journal_tab(screen,main.CONTENT_RECT,state["journal"],0)
    pygame.image.save(screen,f"/tmp/lf_{tab}.png")
print("render ok")
