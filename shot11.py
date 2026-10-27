import os,random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame; pygame.init(); screen=pygame.display.set_mode((900,700))
import people as P, romance as R
from constants import *
random.seed(3)
R_=pygame.Rect(200,320,675,320)
st={"stats":{k:62 for k in ("physical","mental","social","academic","looks","athletic","wealth")},"money":400,"age":24,"actions_remaining":9,"actions_used":{},"gender":"Male","attracted":"Women","_has_partner":True}
p=P.make_person("Partner","partner","Female",closeness=60,age=24); p["compat"]=71; p["status"]="situationship"; p["romance"]=52
surf=pygame.Surface((1400,360)); 
for i,(mode,labels,hdr,note) in enumerate([("prospect",("Ask them out","Keep it casual","Pass"),"Possible partner","Check their stats, then decide."),("invite",R.LABELS["cheated"],R.HEADS["cheated"],"Messages, a friend's tip... what will you do?")]):
    screen.fill((233,236,243)); P.draw_profile(screen,R_,p,(0,0),st,24,mode=mode,header=hdr,labels=labels,note=note)
    surf.blit(screen.subsurface(pygame.Rect(190,310,700,340)),(i*700,0))
screen.fill((233,236,243)); P.draw_profile(screen,R_,p,(0,0),st,24)
surf2=pygame.Surface((1400,700)); surf2.blit(surf,(0,0)); surf2.blit(screen.subsurface(pygame.Rect(190,310,700,340)),(0,360))
import career as C
screen.fill((233,236,243)); 
pygame.image.save(surf2,"/tmp/romance_preview.png")
