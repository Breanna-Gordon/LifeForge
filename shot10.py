import os,random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame; pygame.init(); screen=pygame.display.set_mode((900,700))
import lifestyle as L, achievements as A
from constants import *
R=pygame.Rect(200,320,675,320)
st={"stats":{k:62 for k in ("physical","mental","social","academic","looks","athletic","wealth")},"money":400,"age":20,"actions_remaining":9,
    "actions_used":{},"journal":[],"owned":{"licence","car"},"activities":{},"skills":{},"parents_ok":True,"_has_partner":False,"act_view":"life","achievements":["Saver","Graduate","In Love"],"pets":[{"name":"Mochi","kind":"cat","age":2,"life":14}]}
L.ensure_state(st); car={"fame":10}
out=[]
for i,(cat,name) in enumerate([(None,"hub"),("mind","mind"),("industries","ind")]):
    screen.fill((233,236,243)); st["_ls_cat"]=cat
    import activities
    activities.draw_activities_tab(screen,R,(0,0),st,20,car)
    pygame.image.save(screen.subsurface(pygame.Rect(190,300,700,360)),f"/tmp/ls_{name}.png")
screen.fill((233,236,243)); A.draw_view_toggle(screen,R,(0,0),"awards"); A.draw_awards(screen,R,st)
pygame.image.save(screen.subsurface(pygame.Rect(190,300,700,360)),"/tmp/ls_ach.png")
