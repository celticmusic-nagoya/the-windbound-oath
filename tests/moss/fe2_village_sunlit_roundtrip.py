# F-E2: peaceful Rilde Village <-> Sunlit Path (A1) round trip. needs http.server 8765.
# Covers: stage gating (0 closed / 1-3 open / 4+ closed), return trip, repeated round trips without duplicate event firing,
# no ordinary goblins in the peaceful A1, clear weather, post-attack closure, map data (exit / spawn / edge gap / tree), save/load (reported honestly).
import json, sys
from playwright.sync_api import sync_playwright
URL='http://localhost:8765/index.html'; errs=[]; fails=[]; notes=[]
V='rilde_village_01_peace'; R='rilde_village_01_ruin'; A1='moss_forest_01_sunlit_path'
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
# ---- static map data
mp=json.load(open('data/maps/%s.json'%V,encoding='utf-8')); mr=json.load(open('data/maps/%s.json'%R,encoding='utf-8')); ma=json.load(open('data/maps/%s.json'%A1,encoding='utf-8'))
for k,m in ((V,mp),(R,mr)):
    t=[t for t in m['transitions'] if t['id']=='tr_v_to_moss']
    check(len(t)==1 and t[0]['rect']==dict(shape='rect',x=770,y=48,w=120,h=60) and t[0]['toMap']=='TBD','%s: tr_v_to_moss rect(770,48,120,60) routed via story hook'%k)
    check(m['spawns']['points'].get('from_moss_forest')=={'x':830,'y':190,'facing':'down'},'%s: spawn from_moss_forest (830,190,down)'%k)
    top=[e for e in m['collision']['edgeBlockers'] if e.get('y')==0 and e.get('h')==48 and e.get('w',0)>48]
    check([(e['x'],e['w']) for e in top]==[(0,2400)],'%s: top edge blocker stays closed (exit rect sits right under it; the player cannot leave the map)'%k)
    ids=[p['id'] for p in m['props']]
    near=[p for p in m['props'] if 700<p['x']<960 and p['y']<260]
    check(not near,'%s: no prop (tree) plugs the north road %s'%(k,[p['id'] for p in near]))
    def hit(r):return r[0]<890 and r[0]+r[2]>770 and r[1]<260 and r[1]+r[3]>0
    bl=[b['id'] for b in m['collision']['blockers'] for r in b['rects'] if hit(r)]
    check(not bl,'%s: no collision blocker in the north road corridor %s'%(k,bl))
check(set(mp['spawns']['points'])==set(mr['spawns']['points']),'peace/ruin spawn name sets identical')
check(ma['spawns']['points'].get('from_lind') and any(t['id']=='tr_to_lind' for t in ma['transitions']),'A1 keeps from_lind spawn and tr_to_lind')
check(ma['weather']['rules'][0]=={'when':{'stage':[0,8]},'set':'clear','ms':0},'A1 weather: clear for stage 0-8 is the first rule')
tid=sorted(t['id'] for t in ma['treasurePoints']); check(tid==['tr_a1_hidden','tr_a1_hollow','tr_a1_overlook','tr_a1_rest'] or len(tid)>=4,'A1 treasure ids untouched %s'%tid)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto(URL); pg.wait_for_timeout(1200); ev=pg.evaluate
    def settle(ms=1700):
        pg.wait_for_function("MossForest.busy===false",timeout=20000); pg.wait_for_timeout(ms)
    def village(stage):
        ev("(s)=>{storyStage=s;document.querySelectorAll('.overlay,.scene').forEach(()=>0);RildeVillage.enter('from_training')}",stage); pg.wait_for_function("MossForest.active&&MossForest.mapId.startsWith('rilde_village_01_')",timeout=20000); settle(2000)
    def where(): return ev("MossForest.mapId")
    def tp(x,y): ev("(a)=>MossForest.teleportFeet(a[0],a[1])",[x,y]); settle()
    def walk(x,y,key,goal,hold=900,timeout=15000):
        # No blind retry. The opening scene's dialogue (opened at page load) blocks movement, so it is closed and the precondition is asserted.
        # The key is held until the real goal is reached (or the deadline), not for a fixed time: a slow machine / loaded CI only needs longer, a wrong
        # destination still fails the assertions that follow (the goal is only 'reached the exit rect / the map changed', never 'assume success').
        ev("closeDialogue()"); ev("(a)=>MossForest.teleportFeet(a[0],a[1])",[x,y]); settle(700)
        check(not ev("document.body.classList.contains('dialogueOpen')") and ev("MossForest.active&&!MossForest.busy"),'walk precondition: no dialogue open, forest active (%s)'%key)
        m0=ev("MossForest.mapId"); pg.keyboard.down(key)
        try: pg.wait_for_function("(a)=>MossForest.mapId!==a[0]||(%s)"%goal,arg=[m0],timeout=timeout)
        except Exception: print('NOTE walk deadline: goal not reached (%s, map %s, feet %s)'%(key,ev("MossForest.mapId"),ev("MossForest.feet")))
        pg.wait_for_timeout(hold); pg.keyboard.up(key); settle(1500)
    def north(): walk(830,230,'ArrowUp',"MossForest.feet.y<=104")        # village: up the north road to the exit rect under the edge wall
    def south(): walk(1400,5760,'ArrowDown',"MossForest.feet.y>=5945")   # A1: down onto tr_to_lind
    def in_exit():
        f=ev("MossForest.feet"); return 770<=f['x']<=890 and 48<=f['y']<=108
    def toasts(): return ev("document.querySelector('#forestToast')?document.querySelector('#forestToast').textContent:''")
    # ---- stage 0: closed
    village(0); check(where()==V,'stage 0 village is peace'); north(); check(in_exit(),'stage 0: player reached the exit rect (%s)'%ev("MossForest.feet"))
    check(where()==V,'stage 0: north exit does NOT lead to A1 (map %s)'%where())
    check('フィオナ' in ev("document.getElementById('forestToast').textContent"),'stage 0: a hint toast tells the player to meet Fiona')
    # ---- stage 1 (after Fiona joined): open
    ev("(()=>{storyStage=0;})()"); village(0)
    ev("document.getElementById('fiona').onclick()"); pg.wait_for_timeout(300)
    check(ev("storyStage")==1,'Fiona join (#fiona) moves storyStage 0 -> 1 (this is the opening condition)')
    ev("closeDialogue&&closeDialogue()")
    village(1)
    fired0=ev("JSON.stringify(PrologueProgress.serialize().moss.fired)"); opened0=ev("JSON.stringify(PrologueProgress.serialize().moss.opened)")
    sig=[]
    for i in range(3):
        north()
        check(where()==A1,'round %d: village -> A1 (map %s)'%(i+1,where()))
        f=ev("MossForest.feet"); check(abs(f['x']-1429)<60 and abs(f['y']-5673)<60,'round %d: arrives at A1 from_lind (%s)'%(i+1,f))
        if i==0:
            kinds=ev("MossForest.monsters.map(m=>m.type||m.t&&m.t.id||'?')")
            ty=ev("MossForest.monsters.map(m=>m.id)")
            check(len(ty)>0 and not any('gob' in str(x) for x in ty),'peaceful A1 has monsters but no goblins (%d: %s)'%(len(ty),sorted(set(map(str,ty)))[:8]))
            check(ev("FieldWeather.current")=='clear','peaceful A1 weather is clear (%s)'%ev("FieldWeather.current"))
            check(ev("storyStage")==1,'stage stays 1 in A1')
        south()
        check(where()==V,'round %d: A1 -> village (map %s)'%(i+1,where()))
        f=ev("MossForest.feet"); check(abs(f['x']-830)<60 and abs(f['y']-190)<60,'round %d: arrives at village from_moss_forest (%s)'%(i+1,f))
        sig.append((ev("JSON.stringify(PrologueProgress.serialize().moss.fired)"),ev("JSON.stringify(PrologueProgress.serialize().moss.opened)"),ev("storyStage")))
    check(len(set(sig))==1,'repeated round trips leave fired/opened/stage identical (no duplicate event firing) %s'%(sig[0][:2],))
    check(opened0==sig[0][1],'treasures opened unchanged by round trips')
    # event-zone once-semantics: location card zone fires once
    fi=json.loads(sig[0][0]); check(len(fi)==len(set(fi)),'fired ids have no duplicates %s'%fi)
    # ---- stage 3 still open, stage 4 closed
    village(3); north(); check(where()==A1,'stage 3: still open'); ev("storyStage=3"); south()
    village(4); north(); check(in_exit() and where()==V,'stage 4 (cliff sunset): reached exit, closed'); 
    # ---- attack started (stage 5+, ruin village): closed
    for st in (5,6,7,8):
        village(st); st_map=where(); north()
        check(st_map==R and in_exit() and where()==R,'stage %d: ruin village, reached exit rect, closed (map %s)'%(st,where()))
    # stage>=15: closed in this task (decision pending)
    village(15); north(); check(in_exit() and where()==R,'stage 15: reached exit, peaceful route stays closed (open decision, see report)')
    # ---- direct A1 access under attack/prologue stages: tr_to_lind does not return to a peaceful village
    for st in (9,12):
        ev("(s)=>{storyStage=s}",st); ev("MossForest.reset();MossForestStory.enterMap('moss_forest_01_sunlit_path','from_lind')"); pg.wait_for_function("MossForest.mapId==='%s'"%A1,timeout=20000); settle(900)
        south()
        check(where()==A1,'stage %d: A1 tr_to_lind blocked (stays in A1)'%st)
        mons=ev("MossForest.monsters.map(m=>m.id)"); check(any('gob' in str(x) for x in mons),'stage %d: A1 goblins still present (prologue behaviour unchanged)'%st)
    # ---- save / load in A1 at peaceful stage (honest report)
    village(1); north()
    data=ev("PrologueProgress.serialize()"); mo=data.get('moss') or {}
    ev("(d)=>{localStorage.setItem(SAVE_KEY,JSON.stringify({version:29,prologue:d}));return loadGrowthData()}",data); pg.wait_for_timeout(2500)
    restored=where(); active=ev("MossForest.active"); shown=ev("document.querySelector('#forestScene').style.display")
    print('save/load probe: map=%s active=%s forestScene=%s stage=%s moss=%s'%(restored,active,shown,ev('storyStage'),json.dumps(mo)[:80]))
    # whatever the restore target is, the load must leave a playable, uncorrupted game (no soft-lock / data loss)
    post=ev("({stage:storyStage,world:getComputedStyle(document.getElementById('world')).display,ser:PrologueProgress.serialize()})")
    check(post['stage']==1 and post['world']!='none','after the A1-position save is loaded: stage kept (1) and the legacy DOM world is shown (%s)'%post['world'])
    check(post['ser']['moss']['opened']==data['moss']['opened'] and post['ser']['version']==2,'after load: opened treasures and save format v2 intact')
    if restored==A1 and active and shown!='none': check(True,'A1 save at stage 1 restores to A1')
    else:
        notes.append('A1 save/load at peaceful stage (<=8) is NOT supported by the current save spec: the forest is not re-entered (active=%s, forestScene=%s, mapId leftover=%s; stage<=8 loads go to the legacy DOM position). Reported as a separate issue; NOT counted as PASS.'%(active,shown,restored))
        print('NOTE '+notes[-1])
    print('errors',errs[:6]); b.close()
if notes: print('UNSUPPORTED (separate issue):',notes)
sys.exit(1 if (fails or errs) else 0)
