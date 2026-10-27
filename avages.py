import os
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame;pygame.init()
from avatar import draw_avatar
from constants import SKIN_TONES
scr=pygame.display.set_mode((1500,420));scr.fill((240,235,245))
ages=[1,4,8,12,16,22,35,50,62,75,90]
for row,(g,fh) in enumerate((("Female","None"),("Male","Stubble"))):
  for i,a in enumerate(ages):
    r=pygame.Rect(i*135+5,row*205+5,130,195);pygame.draw.rect(scr,(255,255,255),r,border_radius=10)
    draw_avatar(scr,pygame.Rect(r.x,r.y+20,130,170),g,(70,45,30),"Long" if g=="Female" else "Short",SKIN_TONES[2],fh,a,70)
pygame.image.save(scr,"/tmp/ages.png")
