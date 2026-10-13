"""Valid bridge-level contact fixtures; records hooks/once, never changes repository maps/runtime."""
import json, os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.qa.browser_support import server, ROOT
from playwright.sync_api import sync_playwright
fails=[]; errors=[]; checks=[]
def ck(ok,msg):
    print(('ok   ' if ok else 'FAIL ')+msg,flush=True);checks.append({'check':msg,'pass':bool(ok)})
    if not ok:fails.append(msg)
def fixture(kind,level=0):
    m=json.loads((ROOT/'data/maps/dev_height_proto.json').read_text())
    m.update(eventZones=[],transitions=[],treasurePoints=[],monsters=[],walkers=[],story={})
    m['spawns']['points']['test']={'x':1560,'y':1050,'level':1-level};m['spawns']['default']='test'
    shape={'shape':'rect','x':1540,'y':880,'w':40,'h':40}
    obj={'id':'test_'+kind,'level':level}
    if kind in ('npc','rest','ambience','trigger'):
        obj.update(type={'npc':'interact','ambience':'ambienceShift'}.get(kind,kind),shape=shape,once=True);m['eventZones']=[obj]
    elif kind in ('chest','herb'):
        obj.update(x=1560,y=900,kind=kind,hint='test',loot=[]);m['treasurePoints']=[obj]
    elif kind=='story':
        obj.update(x=1560,y=900,field='fixture_battle',touchRadius=40);m['story']={'prologue':{'symbols':[obj]}}
    elif kind=='moving':
        obj.update(x=1560,y=900,type='moss_slime',tune={'speed':0,'wanderSpeed':0,'engageDelay':.8});m['monsters']=[obj]
    elif kind=='exit':
        obj.update(enabled=True,rect=shape,toMap='dev_height_proto',toSpawn='test');m['transitions']=[obj]
    return m

def fresh(browser,base,kind,level=0,viewport=None):
    page=browser.new_page(viewport=viewport or {'width':844,'height':390})
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    m=fixture(kind,level)
    page.route('**/data/maps/dev_height_proto.json*',lambda r:r.fulfill(json=m))
    page.goto(base+'/index.html?dev=1');page.wait_for_function('window.MossForestStory');page.wait_for_timeout(2500)
    page.evaluate("""closeDialogue();devResetScreens();storyStage=15;window.__calls={event:0,treasure:0,story:0,moving:0,exit:0};
    MossForest.configure({hooks:{onEvent:()=>__calls.event++,onTreasure:()=>__calls.treasure++,onSymbol:()=>__calls.story++,onMonster:()=>{__calls.moving++;return true},onTransition:()=>{__calls.exit++;return true},isCleared:()=>false}})""")
    page.evaluate("async()=>{MossForest.reset();await MossForest.enter({map:'dev_height_proto',spawn:'test'});MossForest.encounters(false);FieldMonsters.setFrozen(true)}")
    page.wait_for_function("MossForest.mapId==='dev_height_proto' && !!MossForest.height")
    return page

def pose(page,level,x=1560,y=900):
    valid=page.evaluate('v=>!MossForest.height.blockedAtLevel(v.x-17,v.y-42,v.l)',{'x':x,'y':y,'l':level})
    assert valid,f'fixture is not valid walk: {x},{y},level{level}'
    page.evaluate('v=>{MossForest.resume();MossForest.teleportFeet(v.x,v.y);MossForest.height.setLevel(v.l);MossForest.height.commit(v.x-17,v.y-42)}',{'x':x,'y':y,'l':level});page.wait_for_timeout(120)

def tap(page,y=900):
    pt=page.evaluate('y=>FieldCamera.worldToScreen(document.querySelector("#forestWorld"),1560,y)',y)
    page.mouse.click(pt['x'],pt['y']);page.wait_for_timeout(200)

def count(page,kind):
    if kind in ('rest','ambience'):return int(page.evaluate('k=>MossForest.zones[k]!==null',kind))
    return page.evaluate('k=>__calls[k]',{'npc':'event','trigger':'event','chest':'treasure','herb':'treasure','story':'story','moving':'moving','exit':'exit'}[kind])
with server() as base, sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium'))
    for kind in ('npc','chest','herb','trigger','story','moving','exit','rest','ambience'):
        pg=fresh(b,base,kind)
        pose(pg,1)
        if kind in ('npc','chest','herb'):tap(pg,882 if kind!='npc' else 900)
        if kind=='moving':pg.evaluate('FieldMonsters.setFrozen(false)');pg.wait_for_timeout(1300)
        ck(count(pg,kind)==0,kind+': other level no hook/reward/zone')
        pg.evaluate('FieldMonsters.setFrozen(true)')
        pose(pg,0,y=1050)
        if kind in ('story','exit'):
            assert pg.evaluate('MossForest.goFeet(1560,900)')
            pg.wait_for_timeout(2300)
        else:pose(pg,0)
        if kind in ('npc','chest','herb'):tap(pg,882 if kind!='npc' else 900);tap(pg,882 if kind!='npc' else 900)
        elif kind=='moving':pg.evaluate('FieldMonsters.setFrozen(false)');pg.wait_for_timeout(1300)
        ck(count(pg,kind)==1,kind+': own level exactly one hook/reward/zone')
        if kind in ('chest','herb'):ck(pg.evaluate('MossForest.opened.length')==1,kind+': one claimed id')
        if kind in ('npc','trigger'):ck(pg.evaluate('MossForest.snapshot().fired.length')==1,kind+': once consumed exactly once')
        pg.close()
    # Ground outside the overpass -> select ground NPC under bridge.
    pg=fresh(b,base,'npc');pose(pg,0,x=1400)
    tap(pg);goal=pg.evaluate('MossForest.target')
    ck(goal is not None and goal.get('level')==0,'ground NPC tap retains target level0 (outside bridge)')
    pg.close()
    # Change levels while an engagement is delayed.
    pg=fresh(b,base,'moving');pose(pg,0,y=1050);pose(pg,0)
    pg.evaluate('FieldMonsters.setFrozen(false)')
    try:
        pg.wait_for_function('FieldMonsters.list[0].state==="engage"',timeout=2000)
        pose(pg,1);pg.wait_for_timeout(1300)
        ck(count(pg,'moving')==0,'engagement delay + level change cancels battle hook')
    except Exception as e:ck(False,'delayed engagement fixture reachable: '+str(e).splitlines()[0])
    pg.close()
    for width,height in ((390,844),(844,390)):
        pg=fresh(b,base,'chest',1,{'width':width,'height':height});pose(pg,1)
        # Expected visual lift at upper-level object feet. Runtime currently draws static treasures without it.
        lift=pg.evaluate('MossForest.height.lift(1543,858,1)')
        tap(pg,900-lift-18)
        ck(count(pg,'chest')==1,f'{width}x{height}: upper object tap at lifted visual location')
        pg.screenshot(path=f'/tmp/m24-upper-{width}.png');pg.close()
    b.close()
ck(not errors,'no console/page errors '+str(errors[:2]))
print('SKIP: rest/ambience external effects have no hooks; active zone ids checked instead')
if os.environ.get('OUT'):
    out=Path(os.environ['OUT']);out.mkdir(parents=True,exist_ok=True);(out/'m24.json').write_text(json.dumps({'checks':checks,'errors':errors},indent=2))
print('FAILS',len(fails));sys.exit(1 if fails or errors else 0)
