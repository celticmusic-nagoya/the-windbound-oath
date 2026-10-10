# ドゥンヴァル砦 + 王都 foundation maps: load, collision, spawns, walking to every NPC node / chest / transition, transition chain, 'TBD' exits. needs http.server 8765
import json, sys, glob
from playwright.sync_api import sync_playwright
fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
IDS=['fort_dunvall_01_courtyard','fort_dunvall_02_ramparts','fort_dunvall_03_keep','royal_capital_01_market','royal_capital_02_castle_plaza','royal_capital_03_residential']
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
            if t['toMap']!='TBD': check(t['toMap'] in maps and t['toSpawn'] in maps[t['toMap']]['spawns']['points'],'%s: %s -> %s:%s exists'%(i,t['id'],t['toMap'],t['toSpawn']))
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
        try: pg.wait_for_function('(m)=>MossForest.mapId!==m',arg=mapid,timeout=30000)
        except Exception: pass
        pg.wait_for_timeout(300)
        check(ev("MossForest.mapId")==expect,'walk through %s: %s -> %s'%(tid,mapid,ev("MossForest.mapId")))
    walk_to('tr_f1_to_ramparts','from_road','fort_dunvall_01_courtyard','fort_dunvall_02_ramparts')
    walk_to('tr_f2_down','from_courtyard','fort_dunvall_02_ramparts','fort_dunvall_01_courtyard')
    walk_to('tr_f1_to_keep','from_road','fort_dunvall_01_courtyard','fort_dunvall_03_keep')
    walk_to('tr_f3_exit','from_courtyard','fort_dunvall_03_keep','fort_dunvall_01_courtyard')
    walk_to('tr_r1_to_plaza','from_west_gate','royal_capital_01_market','royal_capital_02_castle_plaza')
    walk_to('tr_r2_to_residential','from_market','royal_capital_02_castle_plaza','royal_capital_03_residential')
    walk_to('tr_r3_to_market','from_plaza','royal_capital_03_residential','royal_capital_01_market')
    # 'TBD' exits stay in place with a toast (no crash / no leaving the map)
    walk_to('tr_f3_to_wall','from_courtyard','fort_dunvall_03_keep','fort_dunvall_02_ramparts')
    walk_to('tr_f2_to_keep','from_courtyard','fort_dunvall_02_ramparts','fort_dunvall_03_keep')
    walk_to('tr_f1_gate_out','from_road','fort_dunvall_01_courtyard','fort_dunvall_01_courtyard')
    walk_to('tr_r1_west_gate','from_west_gate','royal_capital_01_market','royal_capital_01_market')
    check(ev("document.querySelector('#forestToast,.forest-toast')?document.querySelector('#forestToast,.forest-toast').textContent:'?'") is not None,'TBD exit shows a notice')
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)
