import os,asyncio,random
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame;pygame.init()
from constants import *
import main, people, activities, character
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
random.seed(3)
R=main.CONTENT_RECT
fam=people.generate_family(SKIN_TONES[2],(35,28,24))
fr=[people.make_person("Friend","friend",age=15) for _ in range(2)]
pt=people.make_person("Partner","partner","Female",50,age=17); pt["married"]=False
for p in fam+fr+[pt]: p["history"]=[[15,"Had a good chat."],[16,"Spent time together."]]
st={"stats":{k:60 for k in STAT_ORDER},"money":120,"actions_remaining":4,"actions_used":{},"gender":"Male","age":16,"activities":{},"skills":{"singing":3},"owned":set(),"bought_this_year":set(),"journal":[]}
def bg():
    screen.fill((232,222,248)); pygame.draw.rect(screen,(255,255,255),R.inflate(10,10),border_radius=8)
bg(); people.draw_people_tab(screen,R,fam,fr,pt,0,(0,0),st,16,"Meet Someone");pygame.image.save(screen,"/tmp/s_people.png")
bg(); people.draw_profile(screen,R,fam[0],(0,0),st,16);pygame.image.save(screen,"/tmp/s_profile.png")
bg(); st["act_view"]="outings"; activities.draw_activities_tab(screen,R,(0,0),st,16);pygame.image.save(screen,"/tmp/s_out.png")
# creator
flip=pygame.display.flip
class Stop(Exception):pass
n=[0]
def f():
    n[0]+=1
    if n[0]==3:
        pygame.image.save(screen,"/tmp/s_create.png"); raise Stop
    flip()
pygame.display.flip=f
async def go():
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=(385,246),button=1))
    await character.character_selection_screen(screen)
try: asyncio.run(go())
except Stop: pass
