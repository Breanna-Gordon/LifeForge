import os,asyncio,random
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame
pygame.init()
import main
from constants import *
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
st=main.roll_stats()
state={"stats":st,"money":150,"age":20,"actions_remaining":5,"actions_used":{},"life_event_resolved":True,"journal":[],"owned":set(),"bought_this_year":set(),"activities":{"chess":3,"football":2},"scholarship":True}
career={"education":"None","enrolled":False,"uni_target":None,"uni_years_done":0,"college_name":None,"college_prestige":0,"prestige":0,"course":None,"pending_course":None,"job":None,"browsing_jobs":True,"scroll":0}
fb=make_vertical_gradient(SCREEN_WIDTH,SCREEN_HEIGHT,(255,235,205),WHITE)
def hub(tab):main.draw_hub_frame(screen,"Sam",20,"Young Adult",st,st,(35,28,24),"Short",SKIN_TONES[2],"None","Male",{},None,fb,tab,False,state,(0,0))
hub("Activities");main.draw_activities_tab(screen,main.CONTENT_RECT,(0,0),state,20);pygame.image.save(screen,"/tmp/n_act.png")
hub("Education");main.draw_education_tab(screen,main.CONTENT_RECT,(0,0),20,state,career);pygame.image.save(screen,"/tmp/n_edu.png")
career["pending_course"]="Business"
hub("Education");main.draw_education_tab(screen,main.CONTENT_RECT,(0,0),20,state,career);pygame.image.save(screen,"/tmp/n_edu2.png")
hub("Career");main.draw_career_tab(screen,main.CONTENT_RECT,(0,0),career,state);pygame.image.save(screen,"/tmp/n_car.png")
async def roll():
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
    return None
# stats roll screen
import types
orig=pygame.display.flip
def fl():
    pygame.image.save(screen,"/tmp/n_roll.png");pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN));orig()
pygame.display.flip=fl
asyncio.run(main.stats_roll_screen(screen,"Sam","Male",(35,28,24),"Short",SKIN_TONES[2],"None"))
