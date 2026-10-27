import os, random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame; pygame.init(); screen=pygame.display.set_mode((900,700))
import assets, shop
random.seed(1)
st={"money":30_000_000,"savings":0,"invest":0,"debt":0,"home":None,"owned":{"licence"},"age":30,"stats":{k:50 for k in("mental","social","looks","physical")},
    "actions_used":{},"bought_this_year":set(),"journal":[]}
L=[]; lg=L.append; assets.ensure(st)
R=pygame.Rect(200,320,675,320)
for t in (0,2,5): assets.buy_property(st,t,t==2,lg)
for t in (1,3,5): assets.buy_car(st,t,lg)
print(st["home"]["name"],st["debt"],"car" in st["owned"])
p=st["properties"][2]
for a in ("rent","reno","party","live"): assets.do_prop(st,p,a,lg)
c=st["cars"][1]
for a in ("wash","service","trip","tune","race"): assets.do_car(st,c,a,lg)
for y in range(10): assets.assets_year(st,30+y,lg)
print(L[-12:])
st["asset_sub"]="property"; st["asset_sel"]=None
shop_view=st.setdefault("shop_view","assets")
for sub,sel in (("property",None),("property",1),("cars",None),("cars",1)):
    st["asset_sub"],st["asset_sel"]=sub,sel
    screen.fill((250,245,240)); b=shop.draw_shop_tab(screen,R,(300,400),st,30)
    pygame.image.save(screen.subsurface((190,300,700,360)),f"/tmp/a_{sub}_{sel}.png")
    # click through
    shop.handle_shop_click(b["assets"][0][1].centerx,b["assets"][0][1].centery,b,st,30,lg)
st["shop_view"]="bank"; shop.draw_shop_tab(screen,R,(0,0),st,30)
st["home"] and shop.handle_shop_click(0,0,{},st,30,lg)
print("worth",assets.net_worth_assets(st))
