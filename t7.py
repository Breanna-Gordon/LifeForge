import os,random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame;pygame.init();screen=pygame.display.set_mode((900,700))
from constants import *
import people as P
random.seed(5)
R=pygame.Rect(200,320,675,320)
stats={k:60 for k in STAT_ORDER}; stats.update(looks=85,social=80)
st={"stats":stats,"money":100,"actions_remaining":12,"actions_used":{},"gender":"Male","attracted":"Women","age":17,"player_traits":["kind","funny"],"_has_partner":False,"_fame":30,"family_wealth":"Comfortable"}
fam=P.generate_family((200,150,100),(30,30,30),stats)
fr=[P.make_person("Friend","friend",age=17,closeness=60)]
kinds={}
for age in (10,14,17,22,30):
    n=0
    for _ in range(300):
        inv=P.generate_invites(st,age,fr,None,30,fam); n+=len(inv)
        for i in inv: kinds[(age,i["kind"])]=kinds.get((age,i["kind"]),0)+1
    print(age,n/300)
print(sorted(kinds.items())[:12])
log=[].append
logs=[]
for kind in ("dance","date","friend","hangout"):
    for acc in (True,False):
        inv=None
        while not inv:
            inv=[i for i in P.generate_invites(st,14 if kind=='dance' else 18,fr,None,40,fam) if i["kind"]==kind]
        inv=inv[0]; friends=list(fr)
        if acc: part=P.accept_invite(inv,st,18,friends,None,logs.append)
        else: P.decline_invite(inv,st,18,friends,logs.append); part=None
        print(kind,acc,"partner" if part else "-",len(friends))
print(logs[-4:])
# draw cards
inv=[i for i in P.generate_invites(st,17,fr,None,40,fam) if i["kind"] in("date","dance")][0] if False else None
pros=P.make_prospect(st,19,st["player_traits"])
pygame.draw.rect(screen,(232,222,248),(0,0,900,700))
P.draw_profile(screen,R,pros,(0,0),st,19,mode="prospect",header="Possible partner",labels=("Ask them out","Pass"),note="Check their stats and personality, then decide.")
pygame.image.save(screen,"/tmp/t_prosp.png")
pygame.draw.rect(screen,(232,222,248),(0,0,900,700))
fr[0]["category"]="enemy"; fr[0]["conflict"]=65; fr[0]["relation"]="Rival"
P.draw_profile(screen,R,fr[0],(0,0),st,19)
pygame.image.save(screen,"/tmp/t_enemy.png")
# enemy decay + friend->enemy
f2=P.make_person("Friend","friend",closeness=20); f2["conflict"]=75; frs=[f2,fr[0]]; fr[0]["conflict"]=10
pt=P.make_person("Partner","partner"); pt["closeness"]=10; pt["conflict"]=90
for _ in range(10):
    pt=P.advance_relationships(fam,frs,pt,logs.append)
    if pt is None: break
print([ (f["name"],f["category"]) for f in frs], logs[-4:])
