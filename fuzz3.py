import os,asyncio,random,sys
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame
pygame.init()
import main, activities, lifestyle, achievements
from constants import *
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
async def fake_sel(s): return ("Female","Sam",(35,28,24),"Short",SKIN_TONES[2],"None","Both")
main.character_selection_screen=fake_sel
_orig=main.draw_activities_tab
def wrap(screen,rect,mp,state,age,career=None):
    if random.random()<0.05: state["act_view"]="life"
    if random.random()<0.02: state["_jview"]=random.choice(["log","awards","stuff"])
    if random.random()<0.03: state["jail"]=random.choice([0,0,2])
    return _orig(screen,rect,mp,state,age,career)
main.draw_activities_tab=wrap
class C:
    def tick(self,*a):return 0
pygame.time.Clock=lambda:C()
seed=int(sys.argv[1]);random.seed(seed)
res={};frame=[0]
async def go(screen,age,reason,hist,score,summary): res.update(age=age,reason=reason);return
main.game_over=go
import family
async def ss(*a,**k): return None
family.succession_screen=ss
def click(x,y):pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=(x,y),button=1))
flip=pygame.display.flip
def f():
    frame[0]+=1
    r=random.random()
    if r<.10: click(8+62*random.randint(0,9)+31,664)  # open menu, pick tab
    elif r<.55: click(random.randint(200,880),random.randint(330,640))
    elif r<.60: click(640+50,652+10)
    elif r<.605: click(798+50,652+10)  # skip
    elif r<.65: pygame.event.post(pygame.event.Event(pygame.MOUSEWHEEL,x=0,y=random.choice([-1,1])))
    flip()
pygame.display.flip=f
asyncio.run(asyncio.wait_for(main.run_game(screen),120))
print(seed,res,frame[0])
