# ドゥンヴァル砦 + 王都 foundation maps: load, collision, spawns, walking to every NPC node / chest / transition, transition chain, 'TBD' exits. needs http.server 8765
import json, sys, glob, time
from playwright.sync_api import sync_playwright, TimeoutError
fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
IDS=['fort_dunvall_01_courtyard','fort_dunvall_02_ramparts','fort_dunvall_03_keep','royal_capital_01_market','royal_capital_02_castle_plaza','royal_capital_03_residential','royal_capital_00_gate','royal_in_guild','royal_in_inn','road_dunvall_capital_01','fort_in_tavern']
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=15")
    maps={i:json.load(open('data/maps/%s.json'%i,encoding='utf-8')) for i in IDS}
    # static structure
    for i,m in maps.items():
        ids=[t['id'] for t in m['transitions']]
        check(m['schemaVersion']==2 and m['id']==i and len(set(ids))==len(ids) and m['spawns']['default'] in m['spawns']['points'],'%s: schema/id/spawns'%i)
        for t in m['transitions']:
            if t['toMap'] not in ('TBD','lind_village'): check(t['toMap'] in maps and t['toSpawn'] in maps[t['toMap']]['spawns']['points'],'%s: %s -> %s:%s exists'%(i,t['id'],t['toMap'],t['toSpawn']))
        back=[t for t in m['transitions'] if t['toMap'] in maps]
        check(all(any(u['toMap']==i for u in maps[t['toMap']]['transitions']) for t in back),'%s: every link has a way back'%i)
    # runtime: load each, check collision + walk to every node
    ev("enterWorldMap('fort')"); pg.wait_for_timeout(1500)
    for i,m in maps.items():
        ev("(id)=>MossForest.enter({map:id,spawn:null})",i) if False else None
        ev("(a)=>MossForest.enter({map:a[0],spawn:a[1]})",[i,m['spawns']['default']]); pg.wait_for_timeout(1200)
        check(ev("MossForest.mapId")==i and ev("forestActive"),'%s: loads in the runtime'%i)
        sp=m['spawns']['points'][m['spawns']['default']]
        check(not ev("([x,y])=>MossForest.blocked(x,y)",[sp['x'],sp['y']]),'%s: default spawn is free'%i)
        check(ev("MossForest.blocked(10,10)"),'%s: world edge is blocked'%i)
        w=[r for r in m['collision']['blockers'] if r['tag'] not in ('void',)]
        if w:
            x,y,ww,hh=w[0]['rects'][0]; check(ev("([x,y])=>MossForest.blocked(x,y)",[x+ww/2,y+hh/2]),'%s: wall centre is blocked (%s)'%(i,w[0]['tag']))
        pg.screenshot(path='/tmp/claude-0/map_%s.png'%i)
        bad=[]
        for z in [z for z in m['eventZones'] if z['type']=='interact' and 'shape' in z and z['shape'].get('cx')]+[{'id':t['id'],'shape':{'cx':t['x'],'cy':t['y']}} for t in m['treasurePoints']]:
            sh=z['shape']; ok=ev("([x,y])=>{const a=MossForest.goFeet(x,y+40);return a}",[sh['cx'],sh['cy']])
            if not ok: bad.append(z['id'])
        check(not bad,'%s: a walking route exists to every NPC slot and chest %s'%(i,bad))
    # transition chain by walking
    def walk_to(tid, frm, mapid, expect):
        ev("(a)=>MossForest.enter({map:a[0],spawn:a[1]})",[mapid,frm]); pg.wait_for_timeout(1000)
        t=[t for t in maps[mapid]['transitions'] if t['id']==tid][0]['rect']
        cx,cy=t['x']+t['w']/2,t['y']+t['h']/2
        ev("([x,y])=>MossForest.goFeet(x,y)",[cx,cy]); 
        # The road crosses >5,000 px. Under load the existing frame-time cap
        # slows traversal (the valid gate took 51 s at ~10 fps), so 30 s is not
        # a reliable deadline. Still require the actual transition and ready
        # field; never teleport, bypass the gate, or suppress encounters.
        started=time.monotonic()
        wait_ms=90000 if expect!=mapid else 30000
        try:
            pg.wait_for_function('(m)=>MossForest.mapId!==m && MossForest.active && !MossForest.busy',arg=mapid,timeout=wait_ms)
        except TimeoutError:
            if expect!=mapid:
                check(False,'transition readiness deadline: '+tid)
                print('transition timeout',tid,ev("({map:MossForest.mapId,feet:MossForest.feet,active:MossForest.active,busy:MossForest.busy,target:MossForest.target,nav:FieldNavigation.status,battle:document.body.classList.contains('normalBattleMode'),liam:PartyManager.members.liam.joined,pass:FieldTalk.flag('capital_gate_passed')})"))
        pg.wait_for_timeout(300)
        print('walk seconds',tid,round(time.monotonic()-started,2))
        check(ev("MossForest.mapId")==expect,'walk through %s: %s -> %s'%(tid,mapid,ev("MossForest.mapId")))
    walk_to('tr_f1_to_ramparts','from_road','fort_dunvall_01_courtyard','fort_dunvall_02_ramparts')
    walk_to('tr_f2_down','from_courtyard','fort_dunvall_02_ramparts','fort_dunvall_01_courtyard')
    walk_to('tr_f1_to_keep','from_road','fort_dunvall_01_courtyard','fort_dunvall_03_keep')
    walk_to('tr_f3_exit','from_courtyard','fort_dunvall_03_keep','fort_dunvall_01_courtyard')
    walk_to('tr_g_to_market','from_road','royal_capital_00_gate','royal_capital_01_market')
    walk_to('tr_g_to_guild','from_road','royal_capital_00_gate','royal_in_guild')
    walk_to('tr_gi_exit','from_gate','royal_in_guild','royal_capital_00_gate')
    walk_to('tr_g_to_inn','from_road','royal_capital_00_gate','royal_in_inn')
    walk_to('tr_ii_exit','from_gate','royal_in_inn','royal_capital_00_gate')
    walk_to('tr_r1_to_plaza','from_gate','royal_capital_01_market','royal_capital_02_castle_plaza')
    walk_to('tr_r2_to_residential','from_market','royal_capital_02_castle_plaza','royal_capital_03_residential')
    walk_to('tr_r3_to_market','from_plaza','royal_capital_03_residential','royal_capital_01_market')
    walk_to('tr_r1_to_residential','from_gate','royal_capital_01_market','royal_capital_03_residential')
    walk_to('tr_r2_to_market','from_residential','royal_capital_02_castle_plaza','royal_capital_01_market')
    walk_to('tr_r1_to_gate','from_plaza','royal_capital_01_market','royal_capital_00_gate')
    # 'TBD' exits stay in place with a toast (no crash / no leaving the map)
    walk_to('tr_f3_to_wall','from_courtyard','fort_dunvall_03_keep','fort_dunvall_02_ramparts')
    walk_to('tr_f2_to_keep','from_courtyard','fort_dunvall_02_ramparts','fort_dunvall_03_keep')
    walk_to('tr_f1_to_capital','from_road','fort_dunvall_01_courtyard','road_dunvall_capital_01')
    ev("PartyManager.members.liam.joined=true;FieldTalk.setFlag('capital_gate_passed',true)")   # the road gate only opens for Liam's party (tests/moss/m14_capital_gate.py)
    walk_to('tr_rd_to_capital','from_fort','road_dunvall_capital_01','royal_capital_00_gate')
    walk_to('tr_g_to_road','from_road','royal_capital_00_gate','road_dunvall_capital_01')
    walk_to('tr_rd_to_fort','from_capital','road_dunvall_capital_01','fort_dunvall_01_courtyard')
    walk_to('tr_f1_to_tavern','from_road','fort_dunvall_01_courtyard','fort_in_tavern')
    walk_to('tr_in_tavern_exit','from_courtyard','fort_in_tavern','fort_dunvall_01_courtyard')
    # castle gate is still unbuilt ('TBD'): stays in place with a notice
    walk_to('tr_r2_castle_gate','from_market','royal_capital_02_castle_plaza','royal_capital_02_castle_plaza')
    # south gate -> back to the village (story hook hides the forest scene)
    ev("(a)=>MossForest.enter({map:a[0],spawn:a[1]})",['fort_dunvall_01_courtyard','from_keep']); pg.wait_for_timeout(1000)
    t=[t for t in maps['fort_dunvall_01_courtyard']['transitions'] if t['id']=='tr_f1_to_village'][0]['rect']
    ev("([x,y])=>MossForest.goFeet(x,y)",[t['x']+t['w']/2,t['y']+t['h']/2]); pg.wait_for_timeout(9000)
    check(ev("MossForest.mapId").startswith('rilde_village_01_'),'south gate returns to the (Moss) Rilde village')
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)
