import os,sys,time
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame;pygame.init()
from avatar import draw_avatar
from constants import *
scr=pygame.display.set_mode((1500,900));scr.fill((240,235,245))
hc=[(35,28,24),(120,70,30),(200,150,60),(30,30,30),(150,40,30),(90,60,120),(35,28,24),(120,70,30)]
t=time.time()
for i,s in enumerate(HAIRSTYLES):
    for row,(g,age,fh) in enumerate((("Female",25,"None"),("Male",25,"Beard"))):
        r=pygame.Rect(i*185+5,row*190+5,175,175)
        pygame.draw.rect(scr,WHITE,r,border_radius=12)
        draw_avatar(scr,r,g,hc[i],s,SKIN_TONES[(i*2+row+1)%8],fh,age,70)
ages=[2,9,16,30,55,72]
for i,a in enumerate(ages):
    r=pygame.Rect(i*185+5,400,175,175);pygame.draw.rect(scr,WHITE,r,border_radius=12)
    draw_avatar(scr,r,"Female" if i%2 else "Male",(60,40,30),"Short" if i!=1 else "Curly",SKIN_TONES[2],"Stubble" if i==5 else "None",a,70)
for i,(mo,fh) in enumerate(((20,"Moustache"),(50,"Stubble"),(90,"Beard"))):
    r=pygame.Rect(i*185+5,600,175,175);pygame.draw.rect(scr,WHITE,r,border_radius=12)
    draw_avatar(scr,r,"Male",(60,40,30),"Short",SKIN_TONES[4],fh,22,mo)
# big
for i,(g,s) in enumerate((("Female","Long"),("Male","Short"))):
    r=pygame.Rect(600+i*410,590,400,300);pygame.draw.rect(scr,WHITE,r,border_radius=12)
    draw_avatar(scr,r,g,(35,28,24),s,SKIN_TONES[2 if g=="Female" else 5],"None",24,70)
print("render s",round(time.time()-t,2))
pygame.image.save(scr,"/tmp/av3.png")
