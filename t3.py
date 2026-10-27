import os,random
os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame;pygame.init();pygame.display.set_mode((900,700))
import people, activities, events
random.seed(1)
st={"stats":{k:50 for k in ["physical","mental","social","academic","looks","athletic","wealth"]},"money":50,"actions_remaining":5,"actions_used":{},"gender":"Male","age":10,"activities":{},"skills":{}}
fam=people.generate_family((200,150,100),(30,30,30))
mum=fam[0]
print("ages",[ (p["relation"],p["age"]) for p in fam])
print(people.ask_for_money(mum,st,10),st["money"],st["actions_remaining"])
print("can ask again:",people.can_ask_money(mum,st))
# deaths
old=people.make_person("Paternal Grandfather","family","Male",60,age=99); fr=people.make_person("Friend","friend",age=90); pt=people.make_person("Partner","partner",age=99); pt["married"]=True
lst=[old]; fl=[fr]; logs=[]
p=people.advance_deaths(lst,fl,pt,st,logs.append); print(logs,p,st["money"])
# outings
acts={}
b={"outs":[(o,pygame.Rect(0,i*40,300,36)) for i,o in enumerate(activities.OUTINGS)],"views":{},"acts":[]}
lg=[]
for i,o in enumerate(activities.OUTINGS):
    st["actions_remaining"]=5; st["money"]=100
    activities.handle_activities_click(5,i*40+5,b,st,20,[],lambda:{"name":"Z"},lg.append)
print(lg[:6],st["skills"])
st["skills"]={"singing":3}; st["actions_remaining"]=5;st["actions_used"]={}
activities.handle_activities_click(5,4*40+5,b,st,20,[],lambda:{"name":"Z"},lg.append); print(lg[-1])
# events filter
ctx={"career":{"job":None,"enrolled":False,"education":"None"},"partner":None,"friends":[],"people":fam,"money":10,"stats":st["stats"]}
seen=set()
for _ in range(300):
    for t,_o in events.pick_year_events(24,ctx,__import__("choices").choice_events["Young Adult"]["choices"],{},None): seen.add(t)
print("overtime seen w/o job:", "Your workplace offers overtime." in seen, "| serious rel:", "A relationship starts to get serious." in seen)
ctx["career"]["job"]={"title":"x"}
seen=set()
for _ in range(300):
    for t,_o in events.pick_year_events(24,ctx,__import__("choices").choice_events["Young Adult"]["choices"],{},None): seen.add(t)
print("overtime with job:", "Your workplace offers overtime." in seen)
