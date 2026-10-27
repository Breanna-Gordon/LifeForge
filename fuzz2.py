import os,asyncio,random,sys
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame
pygame.init()
import main
from constants import *
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
async def fake_sel(s): return ("Female","Sam",(35,28,24),"Short",SKIN_TONES[2],"None","Both")
async def fake_roll(*a): return main.roll_stats(),["kind","funny"]
main.character_selection_screen=fake_sel;main.stats_roll_screen=fake_roll
class C:
    def tick(self,*a):return 0
pygame.time.Clock=lambda:C()
seed=int(sys.argv[1]);random.seed(seed)
res={};frame=[0];J=[]
async def go(screen,age,reason,hist,score,summary): res.update(age=age,reason=reason,summary=summary);return
main.game_over=go
def click(x,y):pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=(x,y),button=1))
flip=pygame.display.flip
orig_log=main.log
def lg(state,t):
    J.append((state["age"],t));orig_log(state,t)
main.log=lg
def f():
    frame[0]+=1;r=random.random()
    if frame[0]%40==1: click(50,30)
    elif frame[0]%40==3: click(110,132)
    elif r<.25: click(random.choice([300,500,700]),336)  # top buttons
    elif r<.5: click(random.randint(560,870),random.choice([395,453,511,569]))  # row buttons
    elif r<.6: click(345,670)
    flip()
pygame.display.flip=f
asyncio.run(asyncio.wait_for(main.run_game(screen),120))
keys=("Started dating","Married","Welcomed","turned down","ended the","divorce","Divorce","not ready","wasn't ready","no luck","turned 18","tight")
print(seed,res.get("age"),res.get("reason"),res.get("summary"))
print([t for a,t in J if any(k in t for k in keys)][:10])
