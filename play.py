import os,asyncio,random
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame
pygame.init()
import main
from constants import *
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
async def fake_sel(s): return ("Male","Sam",(35,28,24),"Short",SKIN_TONES[2],"None","Both")
main.character_selection_screen=fake_sel
class C:
    def tick(self,*a):return 0
pygame.time.Clock=lambda:C()
frame=[0];res={}
orig_go=main.game_over
async def go(screen,age,reason,hist,score,summary):
    res.update(age=age,reason=reason,summary=summary);return
main.game_over=go
def click(x,y):pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=(x,y),button=1))
orig_flip=pygame.display.flip
def flip():
    frame[0]+=1;f=frame[0]
    r=f%6
    if r==1:
        click(300,480)           # first option
    elif r==2:
        click(450,555)           # next event button (if any)
    elif r==3:
        click(300,480)
    elif r==4:
        click(450,670)           # age up
    elif r==5:
        click(450,670)
    if f%50==10: # visit shop and buy
        click(50,30);click(100,90)
    orig_flip()
pygame.display.flip=flip
random.seed(5)
asyncio.run(asyncio.wait_for(main.run_game(screen),60))
print(res)
