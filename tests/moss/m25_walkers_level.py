"""Walker pause/home-plane contract, with valid bridge feet and a no-height control."""
import json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.qa.browser_support import ROOT,server
from playwright.sync_api import sync_playwright
checks=[];errors=[]
def ck(ok,m):
 print(('ok   ' if ok else 'FAIL ')+m,flush=True);checks.append({'check':m,'pass':bool(ok)})
with server(8795) as base,sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium'))
 for raised in (True,False):
  m=json.loads((ROOT/'data/maps/dev_height_proto.json').read_text())
  if not raised:m.pop('height',None)
  m.update(eventZones=[],transitions=[],treasurePoints=[],monsters=[],story={})
  m['walkers']=[{'id':f'w{lv}','look':'townsman','x':1560,'y':900,'level':lv,'path':[[0,60]],'speed':20,'rest':[0,0]} for lv in (0,1)]
  m['eventZones']=[{'id':f'home{lv}','type':'interact','level':lv,'once':True,'shape':{'shape':'circle','cx':1560,'cy':900,'r':20}} for lv in (0,1)]
  m['spawns']['points']['test']={'x':1560,'y':1050,'level':0};m['spawns']['default']='test'
  pg=b.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('console',lambda v:errors.append(v.text) if v.type=='error' else None)
  pg.route('**/data/maps/dev_height_proto.json*',lambda r:r.fulfill(json=m))
  pg.goto(base+'/index.html?dev=1');pg.wait_for_timeout(2500)
  pg.evaluate("closeDialogue();devResetScreens();window.__homes=[];MossForest.configure({hooks:{onEvent:z=>__homes.push({id:z.id,level:z.level})}})")
  pg.evaluate("async()=>{MossForest.reset();await Promise.race([MossForest.enter({map:'dev_height_proto',spawn:'test'}),new Promise((_,r)=>setTimeout(()=>r(Error('fixture enter timeout')),15000))]);MossForest.encounters(false)}")
  ck(pg.evaluate('FieldWalkers.list.length')==2,f'height={raised}: two real walkers mounted')
  for lv in (0,1):
   pg.evaluate("v=>{const h=MossForest.height;if(h?h.blockedAtLevel(1543,858,v):MossForest.blocked(1560,900))throw Error('invalid fixture feet');MossForest.teleportFeet(1560,900);if(h){h.setLevel(v);h.commit(1543,858)}MossForest.restoreState({fired:[]});__homes=[]}",lv)
   pg.wait_for_timeout(150)
   rows=pg.evaluate("()=>{for(const r of FieldWalkers.list){r.x=r.home[0];r.y=r.home[1];r.i=1;r.wait=0;r.clock=0}FieldWalkers.update(.2);return FieldWalkers.list.map(r=>({id:r.id,level:r.lv??r.level??null,moved:Math.hypot(r.x-r.home[0],r.y-r.home[1])>.1,state:r.state,home:r.home}))}")
   for row in rows:
    wl=int(row['id'][1:]);should_pause=not raised or wl==lv
    ck(row['moved']!=should_pause,f'height={raised} player={lv} walker={wl}: '+('same plane pauses' if should_pause else 'other plane continues'))
    if raised:ck(row['level']==wl,f'height={raised} walker={wl}: declared level retained')
   pt=pg.evaluate('FieldCamera.worldToScreen(document.querySelector("#forestWorld"),1560,900)');pg.mouse.click(pt['x'],pt['y']);pg.wait_for_timeout(150)
   calls=pg.evaluate('__homes');expected=lv if raised else 0
   ck(calls==[{'id':f'home{expected}','level':expected}],f'height={raised} player={lv}: home-zone hook only on eligible plane, once')
   selected=next(r for r in rows if r['id']==f'w{expected}')
   ck((not raised or selected['level']==expected) and selected['home']==[1560,900],f'height={raised}: selected home matches walker plane and original home')
  pg.evaluate("()=>{const h=MossForest.height;if(h){if(h.blockedAtLevel(1543,1008,0))throw Error('invalid far feet');h.setLevel(0)}MossForest.teleportFeet(1560,1050);if(h)h.commit(1543,1008);for(const r of FieldWalkers.list){r.x=r.home[0];r.y=r.home[1];r.i=1;r.wait=0}FieldWalkers.update(.2)}")
  ck(pg.evaluate('FieldWalkers.list.every(r=>r.state==="walk")'),f'height={raised}: both walk away from player (positive control)')
  pg.close()
 b.close()
ck(not errors,'console/page errors0 '+str(errors[:2]))
if os.environ.get('OUT'):
 out=Path(os.environ['OUT']);out.mkdir(parents=True,exist_ok=True);(out/'m25.json').write_text(json.dumps({'checks':checks,'errors':errors},indent=2))
n=sum(not c['pass'] for c in checks);print('FAILS',n);sys.exit(1 if n or errors else 0)
