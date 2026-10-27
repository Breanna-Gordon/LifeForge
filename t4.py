import os,asyncio,random,json
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame;pygame.init()
import main
from constants import *
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
d=json.load(open("lifeforge_save.json")) if os.path.exists("lifeforge_save.json") else None
print("save present",bool(d))
if d:
    for p in d["people"]+d["friends"]+([d["partner"]] if d["partner"] else []):
        for k in ("gender","age","look","attracted","job_title","history"): p.pop(k,None)
    for k in ("gender","attracted","skills","aspiration","aspiration_done"): d["state"].pop(k,None)
    class C:
        def tick(self,*a):return 0
    pygame.time.Clock=lambda:C()
    n=[0];fl=pygame.display.flip
    def f():
        n[0]+=1
        if n[0]>200: raise SystemExit
        if n[0]%20==5: pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=(50,30),button=1));pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=(110,132),button=1))
        if n[0]%20==9: pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=(300,350),button=1))
        fl()
    pygame.display.flip=f
    async def go(*a):return
    main.game_over=go
    try: asyncio.run(main.run_game(screen,resume=d))
    except SystemExit: print("resume ok")
