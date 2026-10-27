import os,asyncio,random,sys
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame
pygame.init()
import main
from constants import *
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
async def fake_sel(s): return ("Female","Sam",(35,28,24),"Short",SKIN_TONES[2],"None","Both")
main.character_selection_screen=fake_sel
class C:
    def tick(self,*a):return 0
pygame.time.Clock=lambda:C()
seed=int(sys.argv[1]);random.seed(seed)
res={};frame=[0]
async def go(screen,age,reason,hist,score,summary): res.update(age=age,reason=reason);return
main.game_over=go
def click(x,y):pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=(x,y),button=1))
flip=pygame.display.flip
def f():
    frame[0]+=1
    r=random.random()
    if r<.10: click(50,30); click(110,86+46*random.randint(0,6))  # open menu, pick tab
    elif r<.55: click(random.randint(200,880),random.randint(330,640))
    elif r<.60: click(345,670)
    elif r<.605: click(560,670)  # skip
    elif r<.65: pygame.event.post(pygame.event.Event(pygame.MOUSEWHEEL,x=0,y=random.choice([-1,1])))
    flip()
pygame.display.flip=f
asyncio.run(asyncio.wait_for(main.run_game(screen),120))
print(seed,res,frame[0])
