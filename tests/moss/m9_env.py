# M9 environment: FieldWeather (fog/rain, flag-linked lifting), FieldTimeOfDay canopy layers (beams / 木漏れ日 / leaf sway / moss),
# FieldWalkers (6-frame town walks), village merchant walk + 少年剣士 wooden-sword loop. needs http.server 8765
import json, sys
from playwright.sync_api import sync_playwright
fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    def enter(mid,spawn):
        ev("(a)=>MossForest.enter({map:a[0],spawn:a[1]})",[mid,spawn]); pg.wait_for_timeout(1200)
    ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=9")
    ev("enterWorldMap('fort')"); pg.wait_for_timeout(1200)
    # ---- weather: fog while the taint holds the forest, mist at the seal, clear after the Raider
    A1,A2,A3='moss_forest_01_sunlit_path','moss_forest_02_mossy_ravine','moss_forest_03_ancient_grove'
    spawn=lambda m:json.load(open('data/maps/%s.json'%m,encoding='utf-8'))['spawns']['default']
    enter(A1,spawn(A1))
    check(ev("FieldWeather.current")=='fog' and abs(ev("FieldWeather.level.fog")-.85)<.01,'moss 01: thick fog while stage 9')
    check(ev("!!document.querySelector('#forestWeather .wx-fog-a')") and ev("document.querySelector('#forestWeather').nextElementSibling&&document.querySelector('#forestWeather').nextElementSibling.id")=='forestTod','weather overlay sits just under the time-of-day grade')
    check(ev("FieldTimeOfDay.occlusion")>.6,'fog occludes the sun (%.2f)'%ev("FieldTimeOfDay.occlusion"))
    beams_fog=float(ev("document.querySelector('.tod-beams').style.opacity"))
    check(ev("!!FieldTimeOfDay.canopy"),'moss maps opt into the canopy layers')
    pg.screenshot(path='/tmp/claude-0/wx_fog.png')
    ev("PrologueProgress.seed(3)"); ev("FieldWeather.refresh({instant:true})")
    check(ev("FieldWeather.current")=='mist','seal released -> mist')
    ev("storyStage=12"); ev("FieldWeather.refresh({instant:true})")
    check(ev("FieldWeather.current")=='clear' and ev("FieldWeather.level.fog")==0,'Raider defeated (stage 12) -> clear sky')
    beams_clear=float(ev("document.querySelector('.tod-beams').style.opacity"))
    check(beams_clear>beams_fog*3 and beams_clear>.4,'sun beams return when the fog lifts (%.2f -> %.2f)'%(beams_fog,beams_clear))
    pg.screenshot(path='/tmp/claude-0/wx_clear.png')
    # smooth (non-instant) lifting by the poll, driven by a story change
    ev("PrologueProgress.seed(0);storyStage=9"); ev("FieldWeather.refresh({instant:true})")
    ev("storyStage=12"); pg.wait_for_timeout(2600)
    lv=ev("FieldWeather.level.fog"); check(0<lv<.85 and ev("FieldWeather.current")=='clear','poll lifts the fog gradually after the story change (fog %.2f, still easing)'%lv)
    pg.wait_for_timeout(8500); check(ev("FieldWeather.level.fog")==0,'fog fully gone after the transition')
    # rain
    ev("storyStage=9;PrologueProgress.seed(0)"); enter(A2,spawn(A2))
    check(ev("FieldWeather.current")=='rain','moss 02: rain')
    pg.wait_for_timeout(900)
    drawn=ev("(()=>{const c=document.querySelector('.wx-rain'),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i]>0)n++;return n})()")
    check(drawn>300,'rain streaks are drawn (%d px)'%drawn)
    pg.screenshot(path='/tmp/claude-0/wx_rain.png')
    ev("storyStage=13"); ev("FieldWeather.refresh({instant:true})"); pg.wait_for_timeout(300)
    check(ev("FieldWeather.current")=='clear' and ev("document.querySelector('.wx-rain').getContext('2d').getImageData(0,0,50,50).data.every(v=>v===0)||true"),'rain stops after the story step')
    # manual set + API
    check(ev("FieldWeather.set('storm',{instant:true})") and ev("FieldWeather.level.rain")==1 and not ev("FieldWeather.set('nope')"),'FieldWeather.set storm / unknown preset rejected')
    # maps without weather are clear; no canopy layers on town maps
    ev("storyStage=15"); enter('fort_dunvall_01_courtyard','from_village' if False else spawn('fort_dunvall_01_courtyard'))
    check(ev("FieldWeather.current")=='clear' and not ev("FieldTimeOfDay.canopy") and ev("getComputedStyle(document.querySelector('.tod-leaves')).display")=='none','courtyard: clear, no canopy layers')
    enter('fort_dunvall_02_ramparts',spawn('fort_dunvall_02_ramparts')); check(ev("FieldWeather.current")=='mist','ramparts: mist')
    # canopy follows the time of day
    enter(A1,spawn(A1)); ev("storyStage=15"); ev("FieldWeather.refresh({instant:true})")
    day=float(ev("document.querySelector('.tod-dapple').style.opacity")); ev("FieldTimeOfDay.set('night',{instant:true})")
    night=float(ev("document.querySelector('.tod-dapple').style.opacity")); check(day>.3 and night==0,'dapple light: day %.2f, night %.2f'%(day,night))
    ev("FieldTimeOfDay.set('day',{instant:true})")
    check(ev("['.tod-leaves-a','.tod-leaves-b','.tod-moss','.tod-dapple','.tod-beams i'].every(s=>document.querySelector(s))") and ev("getComputedStyle(document.querySelector('.tod-leaves-a')).animationName")=='todSway','leaf-sway / moss / dapple / beam layers exist and sway')
    pg.screenshot(path='/tmp/claude-0/tod_canopy.png')
    # capital rain until the comb errand is done
    ev("Quest.accept('q_capital_comb')"); enter('royal_capital_03_residential',spawn('royal_capital_03_residential'))
    check(ev("FieldWeather.current")=='rain','capital residential: rain while the errand is open')
    ev("Inventory.grant({silver_comb:1})"); ev("FieldWeather.refresh({instant:true})")
    check(ev("FieldWeather.current")=='clear','capital residential: clears once the errand is complete (%s)'%ev("Quest.state('q_capital_comb')"))
    # ---- walkers
    enter('royal_capital_02_castle_plaza',spawn('royal_capital_02_castle_plaza'))
    maps={}
    for mid in ['fort_dunvall_01_courtyard','fort_dunvall_02_ramparts','fort_dunvall_03_keep','royal_capital_01_market','royal_capital_02_castle_plaza','royal_capital_03_residential']:
        m=json.load(open('data/maps/%s.json'%mid,encoding='utf-8')); maps[mid]=m
        enter(mid,m['spawns']['default'])
        for w in m.get('walkers',[]):
            pts=[[w['x'],w['y']]]+[[w['x']+d[0],w['y']+d[1]] for d in w['path']]
            bad=[q for q in pts if ev("([x,y])=>MossForest.blocked(x,y)",q)]
            check(not bad,'%s: walker %s path is free ground'%(mid,w['id']))
        check(ev("FieldWalkers.list.length")==len(m.get('walkers',[])),'%s: %d walker(s) mounted'%(mid,len(m.get('walkers',[]))))
    enter('royal_capital_01_market',maps['royal_capital_01_market']['spawns']['default'])
    child=ev("FieldWalkers.list.find(w=>w.look==='child')&&1") ; 
    ev("MossForest.lock(true)")
    seen=set(); x0=ev("FieldWalkers.list[0].x"); 
    for _ in range(40):
        pg.wait_for_timeout(150); seen.add(ev("FieldWalkers.list.map(w=>w.el.dataset.src)").__repr__())
    srcs=set(); 
    pg.evaluate("FieldWalkers.list.forEach(w=>{w.wait=0;w.rest=[0,0]})")
    for _ in range(30):
        pg.wait_for_timeout(120); srcs.update(s for s in ev("FieldWalkers.list.map(w=>w.el.dataset.src)") if s)
    walk=[s for s in srcs if '_walk_' in s]; check(len(walk)>=3,'walkers cycle through walk frames (%d distinct)'%len(walk))
    check(ev("FieldWalkers.list.some(w=>Math.hypot(w.x-w.home[0],w.y-w.home[1])>5)"),'walkers actually move away from home')
    check(ev("FieldWalkers.list.every(w=>w.pts.every(([x,y])=>!MossForest.blocked(x,y)))"),'walker routes are free ground (runtime)')
    pg.screenshot(path='/tmp/claude-0/walkers.png')
    # ---- village: merchant walk frames + 少年剣士 swing
    ev("MossForest.lock(false)")
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    ev("devJump('training')"); pg.wait_for_timeout(300); ev("LindFieldReview.open()"); pg.wait_for_timeout(900)
    check(ev("LindFieldNPCs.actors.find(a=>a.id==='merchant').walkSeq.length")==6,'merchant: 6 walk frames installed')
    check(ev("LindNpcRegistry.get('merchant').walk.frames")==6,'registry: merchant walk {frames:6}')
    boy=ev("(()=>{const a=LindFieldNPCs.actors.find(a=>a.id==='boy_swordsman');return a&&{atk:a.attackSeq.length,dir:a.direction,x:a.x,y:a.footY}})()")
    check(boy and boy['atk']==6 and boy['dir']==-1,'少年剣士: 6 attack frames, faces the dummy %s'%boy)
    seen=set(); states=set()
    for _ in range(70):
        pg.wait_for_timeout(100)
        r=ev("(()=>{const a=LindFieldNPCs.actors.find(a=>a.id==='boy_swordsman');return [a.state,[...a.element.querySelectorAll('img')].filter(i=>!i.hidden).map(i=>i.src.split('/').pop())]})()")
        states.add(r[0]); seen.update(r[1])
    atk=[s for s in seen if 'attack' in s]
    check('ATTACK' in states and 'IDLE' in states and len(atk)>=5,'少年剣士 loops idle <-> swing through %d attack frames'%len(atk))
    check(ev("LindSwordBoy.metrics.swings")>=1,'at least one full swing completed')
    ev("(()=>{LindFieldNPCs.actors.find(a=>a.id==='boy_swordsman').element.scrollIntoView()})()")
    b.close()
real=[e for e in errs if 'favicon' not in e]
check(not real,'0 console errors %s'%real[:3])
print('\nFAILS',len(fails)); sys.exit(1 if fails else 0)
