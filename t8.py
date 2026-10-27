import os,asyncio,random
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame;pygame.init()
import main, people as P
from constants import *
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
async def fake_sel(s): return ("Male","Sam",(35,28,24),"Short",SKIN_TONES[2],"None","Both")
main.character_selection_screen=fake_sel
async def fr(*a): return ({k:80 for k in STAT_ORDER}, ["kind","funny"])
main.stats_roll_screen=fr
def gen(state,age,friends,partner,fame,people):
    if age<14: return []
    out=[]
    for k in ("dance" if age<16 else "date","friend","hangout"):
        p=P.make_prospect(state,age,state["player_traits"]) if k in("dance","date") else P.make_person("Friend","friend",age=age,closeness=60)
        if k=="hangout": p=people[0]
        out.append({"kind":k,"person":p,"text":f"{p['name']} test invite.","why":"Test."})
    return out
main.generate_invites=gen
class C:
    def tick(self,*a):return 0
pygame.time.Clock=lambda:C()
res={};n=[0];fl=pygame.display.flip
async def go(screen,age,reason,hist,score,summary): res.update(age=age,reason=reason,summary=summary)
main.game_over=go
random.seed(3)
def click(x,y):pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=(x,y),button=1))
def f():
    n[0]+=1
    r=n[0]%8
    if r==1: click(492,611)       # accept
    elif r==3: click(712,611)     # decline
    elif r==5: click(340,670)     # age up
    elif r==6 and n[0]%40==6: click(50,30); click(110,132)  # people tab
    elif r==7 and n[0]%40==7: click(480,336)  # look for partner
    elif r==7 and n[0]%40==15: click(500,611)  # ask them out
    if n[0]>1500: raise SystemExit
    fl()
pygame.display.flip=f
try: asyncio.run(main.run_game(screen))
except SystemExit: pass
print(res.get("age"),res.get("reason"),n[0])
