import os,random,sys
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame;pygame.init()
import main
from constants import *
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
random.seed(2)
st=main.roll_stats()
state={"stats":st,"money":150,"age":20,"actions_remaining":9,"actions_used":{},"life_event_resolved":False,"journal":[],"owned":set(),"bought_this_year":set(),"activities":{},"debt":40,"journal":[(18,"Started a part-time job: Cafe Assistant."),(19,"Joined the Chess Club."),(19,"Made a new friend: Mia."),(20,"Took out a $100 loan.")],"_snapshot":[("Education","Studying Bachelor's"),("Job","Cafe Assistant"),("Partner","Single"),("Friends / enemies","3 / 1"),("Family wealth","Comfortable"),("Aspiration","Scholar"),("Savings","$20")],"_badge":2}
fb=make_vertical_gradient(SCREEN_WIDTH,SCREEN_HEIGHT,(255,235,205),WHITE)
icons={}
main.draw_hub_frame(screen,"Sam",20,"Young Adult",st,st,(35,28,24),"Short",SKIN_TONES[2],"None","Male",icons,None,fb,"Life",False,state,(0,0))
main.draw_life_tab(screen,main.CONTENT_RECT,"You receive an offer for further education.",["Accept","Decline"],None,(0,0),False,None)
pygame.image.save(screen,"/tmp/hub0.png")
