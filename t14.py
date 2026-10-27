import os, random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame; pygame.init(); pygame.display.set_mode((900,600))
import romance, shop
from people import make_person, finances, money_lines
random.seed(3)
logs=[]; lg=logs.append
# partner work
p = make_person("Partner","partner",None,60,age=30)
p["married"]=False; p["engaged"]=True
for y in range(40):
    p["age"]=30+y; romance._partner_work(p,lg)
print(len(logs), logs[:6], money_lines(p))
# prenup
st={"money":500000,"savings":0,"invest":0,"stats":{"mental":50,"social":50,"looks":50,"health":50,"smarts":50},"actions_remaining":1,"actions_used":{}}
cards=[]
p2=make_person("Partner","partner",None,60,age=30); p2["engaged"]=True; p2["traits"]=[]
_,c=romance.romance_year(st,30,p2,[],lg,lambda *a:None,0)
print([x["kind"] for x in c])
inv=[x for x in c if x["kind"].startswith("prenup")]
if inv: romance.resolve_card(inv[0],"Ask for a prenup",p2,[],st,lg); print(p2.get("prenup"),logs[-1])
p2["married"]=True; print("divorce share",romance.divorce_share(p2))
# bank
s=shop
state={"money":2_500_000,"savings":0,"invest":0,"debt":0,"_income":300000,"home":None,"owned":set(),"age":30}
for amt in (1000,None):
    state["bank_amt"]=amt
    print(amt,[ (k,s._chosen(state,k,30)) for k,_ in s.BANK_BUTTONS])
state["auto_bank"]="invest"; s.bank_auto(state,lg); print(state["money"],state["invest"],logs[-1])
