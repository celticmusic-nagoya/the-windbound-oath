# M4 save serialize/load/migration checks via index.html. usage: m4_save.py (needs http.server 8765)
import sys, json
from playwright.sync_api import sync_playwright
URL='http://localhost:8765/index.html'; errs=[]; fails=[]
A1,A2,A3='moss_forest_01_sunlit_path','moss_forest_02_mossy_ravine','moss_forest_03_ancient_grove'
def check(c,msg):
    print(('ok   ' if c else 'FAIL ')+msg)
    if not c: fails.append(msg)
V1=dict(version=1,defeated=[],corruptionCount=0,barrierOpen=False,louFound=False,storyStage=9,attackStep=2,northPhase=3,forestStoneSeen=False,
        forestChests={'fChest1':False,'fChest2':False,'fChest3':False},position={'px':420,'py':1160,'fpx':900,'fpy':700},currentObjective='森の奥を調べる',subQuests={})
def v1(**kw):
    d=json.loads(json.dumps(V1)); d.update(kw); d['corruptionCount']=len(d['defeated']); d['barrierOpen']=len(d['defeated'])==3; return d
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto(URL); pg.wait_for_timeout(1000)
    def load(data,wrap=True):
        pg.evaluate("(d)=>{localStorage.setItem(SAVE_KEY,JSON.stringify({version:29,prologue:d}));return loadGrowthData()}",data)
        pg.wait_for_function("MossForest.busy===false",timeout=20000); pg.wait_for_timeout(700)
        return pg.evaluate("({ok:true,map:MossForest.mapId,feet:MossForest.feet,active:MossForest.active,opened:MossForest.opened,count:PrologueProgress.count(),stage:storyStage,flags:MossForest.flags,dom:document.querySelectorAll('#forestScene *').length})")
    ids=['moss_corruption_01','moss_corruption_02','moss_corruption_03']
    # --- v2 round trip
    pg.evaluate("devJump('barrierAfter')"); pg.wait_for_function("MossForest.active",timeout=20000)
    pg.evaluate("MossForest.teleportFeet(4300,3000)"); pg.wait_for_timeout(200)
    data=pg.evaluate("PrologueProgress.serialize()")
    check(data['version']==2 and data['moss']['map']==A3,'serialize v2 holds moss map/pos (%s)'%json.dumps(data['moss'])[:90])
    check('forestChests' not in data and 'fpx' not in json.dumps(data['position']),'v2 no longer stores legacy forest fields')
    r=load(json.loads(json.dumps(data)))
    check(r['map']==A3 and abs(r['feet']['x']-4300)<2 and abs(r['feet']['y']-3000)<2,'v2 restores exact map+position %s'%r['feet'])
    check(r['count']==3 and r['flags']['moss_a3_seal_open'],'v2 restores 3 defeats + open seal')
    # --- v1 migrations
    r=load(v1()); check(r['map']==A1 and r['active'],'v1 stage9 / 0 defeats -> A1 cliff-fall spawn')
    r=load(v1(defeated=ids[:1],forestChests={'fChest1':True,'fChest2':False,'fChest3':True}))
    check(r['map']==A3 and r['count']==1,'v1 stage9 / 1 defeat -> A3 entrance'); check(set(r['opened'])=={'tr_a1_hollow','tr_a3_shrine'},'v1 chests mapped to new treasure ids %s'%r['opened'])
    r=load(v1(defeated=ids,storyStage=10)); check(r['map']==A3 and r['flags']['moss_a3_seal_open'] and r['feet']['y']>3289,'v1 seal opened -> A3 south of seal, flag open')
    r=load(v1(defeated=ids,storyStage=11,louFound=True)); check(r['map']==A3 and r['flags']['moss_a3_lou_found'] and r['feet']['y']<3000,'v1 Lou found -> sanctuary spot, lou_found flag')
    # --- hostile / inconsistent v2
    bad=pg.evaluate("PrologueProgress.serialize()"); bad['moss']={'map':'evil','x':'NaN','y':None,'opened':[1,'tr_a1_hollow'],'fired':'x'}; bad['storyStage']=9
    r=load(bad); check(r['map']==A1 or r['map']==A3,'junk moss block falls back safely (%s)'%r['map']); check(r['opened']==['tr_a1_hollow'],'junk opened list sanitized %s'%r['opened'])
    bad=v1(defeated=ids[:1]); bad['version']=2; bad['moss']={'map':A3,'x':4300,'y':3000,'opened':[],'fired':[]}
    r=load(bad); check(r['map']==A3 and r['feet']['y']>3289,'seal closed but saved inside sanctuary -> moved to entrance (fy=%d)'%r['feet']['y'])
    bad=v1(defeated=ids); bad['version']=2; bad['moss']={'map':A3,'x':99999,'y':100,'opened':[],'fired':[]}   # outside the world
    r=load(bad); check(r['map']==A3 and (r['feet']['y']>6000),'unreachable/odd saved position falls back to spawn (feet %s)'%r['feet'])
    # --- village save (stage 3) loads without touching the forest
    r2=pg.evaluate("(d)=>{localStorage.setItem(SAVE_KEY,JSON.stringify({version:29,prologue:d}));return loadGrowthData()}",v1(storyStage=3)); pg.wait_for_timeout(500)
    check(r2==True and pg.evaluate("document.querySelector('#forestScene').style.display")=='none','village-stage v1 save loads, forest hidden')
    # --- version rejection
    check(pg.evaluate("PrologueProgress.load({version:99})")==False,'unknown version rejected')
    print('errors',errs[:6]); b.close()
sys.exit(1 if (fails or errs) else 0)
