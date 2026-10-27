import os,random
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame;pygame.init()
import main, people as P, career as C, education as E, activities as A, shop as S
from constants import *
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
random.seed(7)
stats=main.roll_stats()
fam=P.generate_family(SKIN_TONES[2],(35,28,24),stats)
fr=[P.make_person("Friend","friend",age=20,closeness=70),P.make_person("Rival","enemy",age=21,closeness=10)]; fr[1]["conflict"]=62
pt=P.make_person("Partner","partner","Female",60,age=22); pt["romance"]=70
state={"stats":stats,"money":150,"age":20,"actions_remaining":9,"actions_used":{},"life_event_resolved":True,"journal":[(18,"Started a part-time job: Cafe Assistant."),(19,"Joined the Chess Club."),(20,"Took out a $100 loan.")],"owned":set(),"bought_this_year":set(),"activities":{"chess":1},"debt":40,"gender":"Male","skills":{"singing":2},"_snapshot":[("Education","Studying Bachelor's"),("Job","Cafe Assistant"),("Partner","Fay"),("Friends / enemies","1 / 1"),("Family wealth","Comfortable"),("Aspiration","Scholar"),("Savings","$20")],"family_wealth":"Wealthy","parents_ok":True}
car={"education":"None","enrolled":False,"uni_target":None,"uni_years_done":0,"college_name":None,"college_prestige":0,"prestige":0,"course":None,"pending_course":None,"job":None,"browsing_jobs":False,"scroll":0,"side_job":None,"fame":35,"experience":0}
fb=make_vertical_gradient(SCREEN_WIDTH,SCREEN_HEIGHT,(255,235,205),WHITE)
def hub(tab):main.draw_hub_frame(screen,"Sam",20,"Young Adult",stats,stats,(35,28,24),"Short",SKIN_TONES[2],"None","Male",{},None,fb,tab,False,state,(0,0))
R=main.CONTENT_RECT
hub("People");P.draw_people_tab(screen,R,fam,fr,pt,0,(0,0),state,20,"Meet Someone New");pygame.image.save(screen,"/tmp/h_people.png")
hub("Career");car["job"]=C._new_job([j for j in C.JOB_TIERS if j["title"]=="Model"][0]);C.draw_career_tab(screen,R,(0,0),car,state);pygame.image.save(screen,"/tmp/h_career.png")
hub("Activities");A.draw_activities_tab(screen,R,(0,0),state,20);pygame.image.save(screen,"/tmp/h_act.png")
hub("Education");car["job"]=None;E.draw_education_tab(screen,R,(0,0),20,state,car);pygame.image.save(screen,"/tmp/h_edu.png")
hub("Shop");S.draw_shop_tab(screen,R,(0,0),state,20);pygame.image.save(screen,"/tmp/h_shop.png")
hub("Life");P.draw_profile(screen,R,pt,(0,0),state,20);pygame.image.save(screen,"/tmp/h_prof.png")
screen.fill((255,255,255));pygame.image.save(screen,"/tmp/_x.png")
sheet=pygame.Surface((1800,1400))
for n,f in enumerate(["people","career","act","edu","shop","prof"]):
    sheet.blit(pygame.image.load(f"/tmp/h_{f}.png"),((n%2)*900,(n//2)*700*1))
pygame.image.save(sheet.subsurface((0,0,1800,1400)),"/tmp/h_sheet.png")
