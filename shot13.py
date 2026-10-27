import os,random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame; pygame.init(); screen=pygame.display.set_mode((900,700))
import people as P, romance as R
random.seed(8)
Rr=pygame.Rect(200,320,675,320)
st={"stats":{k:62 for k in ("physical","mental","social","academic","looks","athletic","wealth")},"money":90000,"age":28,"actions_remaining":9,"actions_used":{},"gender":"Male","attracted":"Women","_has_partner":True}
p=P.make_person("Partner","partner","Female",closeness=70,age=28); p["compat"]=71; p["married"]=True; p["relation"]="Spouse"; p["romance"]=70
q=P.make_person("Admirer","partner","Female",closeness=40,age=27); q["compat"]=64
out=pygame.Surface((1400,700))
for i,(mode,pp,labels,hdr,note) in enumerate([("profile",p,None,"",""),("prospect",q,("Ask them out","Keep it casual","Pass"),"Possible partner","Check their stats."),
    ("invite",p,R.LABELS["ringchoice"],R.HEADS["ringchoice"],"A better ring improves your odds."),("invite",p,R.LABELS["weddingchoice"],R.HEADS["weddingchoice"],"Bigger weddings cost more.")]):
    screen.fill((233,236,243)); P.draw_profile(screen,Rr,pp,(0,0),st,28,mode=mode,header=hdr,labels=labels,note=note)
    out.blit(screen.subsurface(pygame.Rect(190,310,700,340)),((i%2)*700,(i//2)*350))
pygame.image.save(out,"/tmp/marriage_preview.png")
