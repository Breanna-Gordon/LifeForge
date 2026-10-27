import os,asyncio,random
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame;pygame.init()
import main
from constants import *
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
async def fake_sel(s): return ("Male","Sam",(35,28,24),"Short",SKIN_TONES[2],"None","Women")
main.character_selection_screen=fake_sel
async def fr(*a): return (main.roll_stats(), ["kind","funny"])
main.stats_roll_screen=fr
class C:
    def tick(self,*a):return 0
pygame.time.Clock=lambda:C()
random.seed(2);n=[0];fl=pygame.display.flip
def f():
    n[0]+=1
    if n[0]>250: raise SystemExit
    if n[0]%3==0: pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=(450,670),button=1))
    fl()
pygame.display.flip=f
try: asyncio.run(main.run_game(screen))
except SystemExit: pass
