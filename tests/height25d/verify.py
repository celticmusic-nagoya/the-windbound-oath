"""Independent DEV height verification; no production-file mutations."""
import os,sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.qa.browser_support import server,ROOT
from playwright.sync_api import sync_playwright
OUT=Path(os.environ.get('OUT','/tmp/night-x2'));OUT.mkdir(parents=True,exist_ok=True)
checks=[];errors=[]
def ck(ok,name,data=None):
 checks.append(dict(name=name,pass_=bool(ok),data=data));print(('ok   ' if ok else 'FAIL ')+name,flush=True)
def fresh(b,base,view):
 p=b.new_page(viewport={'width':view[0],'height':view[1]});p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
 p.goto(base+'/index.html?dev=1');p.wait_for_function('window.MossForestStory && window.FieldHeight');p.wait_for_timeout(2200)
 p.evaluate('closeDialogue();devResetScreens();storyStage=15;MossForest.reset()');return p

def enter(p,x,y,l=0,map='dev_height_proto'):
 p.evaluate('async v=>{closeDialogue();await MossForest.enter({map:v.map,x:v.x-17,y:v.y-42,level:v.l});MossForest.encounters(false);FieldMonsters.setFrozen(true);MossForest.resume()}',dict(x=x,y=y,l=l,map=map));p.wait_for_timeout(150)
def st(p):return p.evaluate('({x:MossForest.feet.x,y:MossForest.feet.y,l:MossForest.level,z:+document.querySelector("#forestPlayer").style.zIndex,map:MossForest.mapId})')
def hold(p,key,ms):
 p.keyboard.down(key);p.wait_for_timeout(ms);p.keyboard.up(key);p.wait_for_timeout(100)
with server(8842) as base,sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium'))
 for view in [(1280,720),(390,844),(844,390)]:
  p=fresh(b,base,view);tag=f'{view[0]}x{view[1]}'
  enter(p,1800,520);hold(p,'ArrowUp',1500);s=st(p);ck(s['l']==0 and s['y']>=429,tag+' cliff front blocks direct climb',s)
  enter(p,1800,380,1);hold(p,'ArrowDown',1500);s=st(p);ck(s['l']==1 and s['y']<=421,tag+' cliff edge prevents ordinary fall',s)
  enter(p,1960,580);hold(p,'ArrowUp',1700);s=st(p);ck(s['l']==1 and s['y']<430,tag+' stairs reach level1',s)
  enter(p,1560,270);hold(p,'ArrowRight',1600);s=st(p);ck(s['l']==1 and s['x']>1760,tag+' slope reaches level1',s)
  enter(p,1560,900,0);low=st(p);floor=p.evaluate('+document.querySelector("[data-piece=deck_floor]").style.zIndex');alpha=p.evaluate('getComputedStyle(document.querySelector("[data-piece=deck_floor]")).opacity')
  enter(p,1560,900,1);up=st(p);ck(low['l']==0 and up['l']==1 and low['x']==up['x'] and low['y']==up['y'],tag+' bridge same XY supports two levels',dict(low=low,up=up))
  ck(low['z']<floor<up['z'] and float(alpha)<.6,tag+' bridge z-order and underside fade',dict(floor=floor,opacity=alpha))
  enter(p,2100,395,1);s=st(p);canopy=p.evaluate('+document.querySelector("[data-piece=tree_canopy]").style.zIndex');ck(s['z']<canopy,tag+' foreground canopy occludes upper actor',dict(actor=s,canopy=canopy))
  p.screenshot(path=str(OUT/(tag+'-foreground.png')))
  enter(p,1560,900,0);snap=p.evaluate('MossForest.snapshot()');enter(p,300,1250)
  p.evaluate('async s=>{await MossForest.enter(s)}',snap);p.wait_for_timeout(150);s=st(p);ck(s['l']==0 and abs(s['x']-1560)<2 and abs(s['y']-900)<2,tag+' runtime snapshot restore retains ambiguous level0',s)
  # Real story-load path intentionally rejects DEV map; preserve failure as finding.
  p.evaluate('storyStage=9;renderSystemTab("save");saveGrowthData();document.querySelector("#systemMenu").style.display="none"');saved=p.evaluate('JSON.parse(localStorage.getItem(SAVE_KEY))');ck(saved['version']==30 and saved['prologue']['moss']['level']==0,tag+' real save writes v30 + level0');p.evaluate('loadGrowthData()');p.wait_for_timeout(900);s=st(p);ck(s['map']=='dev_height_proto' and s['l']==0,tag+' actual save/load restores DEV map/level',s)
  p.close()
 # Level2 fixture: append to DEV data only in intercepted response, never change JSON on disk.
 p=fresh(b,base,(1280,720));m=json.loads((ROOT/'data/maps/dev_height_proto.json').read_text());m['height']['levels']['2']={'walk':[[1750,120,500,300]]};m['height']['connectors']=[{'id':'test_stairs_0_2','rect':[1900,420,120,120],'axis':'y','fromEnd':'max','from':0,'to':2,'zone':.22}]
 p.route('**/data/maps/dev_height_proto.json*',lambda r:r.fulfill(json=m))
 enter(p,1960,580);hold(p,'ArrowUp',1700);s=st(p);ck(s['l']==2 and s['y']<430,'fixture stairs reaches level2',s)
 snap=p.evaluate('MossForest.snapshot()');enter(p,300,1250);p.evaluate('async s=>await MossForest.enter(s)',snap);p.wait_for_timeout(150);s=st(p);ck(s['l']==2,'fixture runtime snapshot retains level2',s)
 enter(p,1800,380,2);hold(p,'ArrowDown',1500);s=st(p);ck(s['l']==2 and s['y']<=421,'fixture level2 cliff prevents fall',s);p.close()
 # Three existing maps: original hooks/transition path (no overridden transition hooks).
 p=fresh(b,base,(1280,720));p.evaluate('window.__heightCalls=0;window.__originalHeight=FieldHeight;window.FieldHeight={...FieldHeight,create(...a){__heightCalls++;return __originalHeight.create(...a)}}')
 for mid,x,y,key,ms,target in [('rilde_in_aidan',480,570,'ArrowDown',650,'rilde_village_01_ruin'),('rilde_in_barn',500,550,'ArrowDown',650,'rilde_village_01_ruin'),('moss_forest_01_sunlit_path',7700,180,'ArrowUp',1800,'moss_forest_02_mossy_ravine')]:
  enter(p,x,y,0,mid);before=st(p);ck(p.evaluate('MossForest.height===null && MossForest.level===0'),'plain '+mid+' no height')
  hold(p,key,ms);p.wait_for_timeout(1500);after=st(p);ck(after['map']==target,'plain '+mid+' keyboard movement / original transition',dict(before=before,after=after))
 ck(p.evaluate('__heightCalls')==0,'three plain maps never instantiate FieldHeight')
 # Old save without level: original fromSave with real A1 coordinate + opened state.
 p.evaluate('async()=>await MossForestStory.fromSave({moss:{map:"moss_forest_01_sunlit_path",x:2003,y:5001.6,opened:["tr_a1_hollow"],fired:[]}},{storyStage:9,louFound:false,count:0})');p.wait_for_timeout(300)
 ck(p.evaluate('MossForest.mapId==="moss_forest_01_sunlit_path" && MossForest.level===0 && MossForest.opened.includes("tr_a1_hollow")'),'old height-free save reads map/level default/chest')
 p.close();b.close()
ck(not errors,'no console/page errors',errors)
result={'source_head':os.environ.get('QA_SOURCE_HEAD'),'checks':checks,'errors':errors,'fixture_level2':True,'hardware':'cloud Chromium, not Android'}
(OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
n=sum(not c['pass_'] for c in checks);print('FAILS',n);sys.exit(bool(n or errors))
