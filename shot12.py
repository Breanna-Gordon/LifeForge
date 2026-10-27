import os,random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame; pygame.init(); screen=pygame.display.set_mode((900,700))
import people as P
random.seed(4)
R=pygame.Rect(200,320,675,320)
st={"stats":{k:62 for k in ("physical","mental","social","academic","looks","athletic","wealth")},"money":400,"age":15,"actions_remaining":9,"actions_used":{},"gender":"Male","attracted":"Women","_in_school":True,"_has_partner":False}
fam=P.generate_family((220,170,130),(35,28,24),{k:60 for k in P.STAT_KEYS})
fr=[P.make_person("Friend","friend",age=15) for _ in range(3)]
partner=P.make_person("Partner","partner","Female",closeness=60,age=15); partner["compat"]=70; partner["status"]="situationship"
P.refresh_classmates(st,15,True,fr)
ex=P.make_person("Ex","friend",age=15); ex["relation"]="Ex"
fr.append(ex)
out=pygame.Surface((1400,700))
for i,g in enumerate(["romance","family","friends","classmates"]):
    st["_ptab"]=g; screen.fill((233,236,243))
    P.draw_people_tab(screen,R,fam,fr,partner,0,(0,0),st,15,"Meet Someone at School")
    out.blit(screen.subsurface(pygame.Rect(190,310,700,340)),((i%2)*700,(i//2)*350))
pygame.image.save(out,"/tmp/people_tabs.png")
# click test
st["_ptab"]="friends"
tabs=P.group_tab_rects(R)
print(P.handle_people_click(*tabs["classmates"].center,R,fam,fr,partner,0,st,15), st["_ptab"])
print(P.handle_people_click(R.x+50,R.y+40,R,fam,fr,partner,0,st,15))
