"""BB: delivered Aidan frames and actual four-direction rendering; images stay unchanged."""
import json,os,sys,subprocess
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.qa.browser_support import server
fails=[];warnings=[];metrics=[];errors=[]
def ck(c,m):
 print(('ok   ' if c else 'FAIL ')+m,flush=True)
 if not c:fails.append(m)
js="global.window={WINDBOUND_DEV:true};require(process.argv[1]);console.log(JSON.stringify(window.AidanFieldAssets.frames))"
frames=json.loads(subprocess.check_output(['node','-e',js,str(ROOT/'js/field/aidan-field-assets.js')],text=True))
paths={ROOT/v['path'].split('?')[0] for v in frames.values()};actual=set((ROOT/'img/field/characters/aidan').glob('*.png'))
ck(len(frames)==24 and paths==actual,'manifest contains exactly 24 files, no orphan PNGs')
for name,v in frames.items():
 p=ROOT/v['path'].split('?')[0]
 if not p.exists():ck(False,name+' exists');continue
 with Image.open(p) as im:
  ck(im.mode=='RGBA',name+' RGBA');box=im.getchannel('A').getbbox();ck(bool(box),name+' nonempty alpha')
  if not box:continue
  x0,y0,x1,y1=box;ck(abs(y1-v['anchor'][1])<=1,name+' actual feet matches registered anchor ±1px')
  ck(x0>0 and y0>0 and x1<im.width and y1<im.height,name+' no canvas clipping')
  ck(im.size==(v['width'],v['height']),name+' manifest dimensions')
  metrics.append({'name':name,'bbox':box,'height':y1-y0,'width':x1-x0,'anchor':v['anchor']})
heights=[v['height'] for v in metrics];ck(bool(heights) and max(heights)/min(heights)<=1.04,'body height differs by at most4% across idle/walk directions')
for d,n in [('up',6),('down',6),('left',4),('right',4)]:
 ck(sum(k.startswith('aidan_walk_'+d+'_') for k in frames)==n and 'aidan_idle_'+d in frames,d+' required frames')
 idle=next((v for v in metrics if v['name']=='aidan_idle_'+d),None)
 widths=[v['width'] for v in metrics if v['name'].startswith('aidan_walk_'+d+'_')]
 if d in ('up','down') and idle and widths:
  ratio=sum(widths)/len(widths)/idle['width'];warnings.append({'direction':d,'mean_walk_width_to_idle':round(ratio,3),'known_visual_issue':'delivered walk is three-quarter view; width proxy cannot classify face/body orientation'})
with server(8797) as base,sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE') or None);pg=b.new_page(viewport={'width':844,'height':390})
 pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
 pg.goto(base+'/index.html?dev=1');pg.wait_for_timeout(1800);pg.evaluate("closeDialogue();devJump('forest')");pg.wait_for_function("forestActive && MossForest.mapId==='moss_forest_01_sunlit_path'",timeout=15000);pg.wait_for_timeout(1500)
 pg.evaluate('MossForest.devFreezeMonsters(true);MossForest.encounters(false);closeDialogue()')
 # Find a clear crossing with room for actual movement in every direction.
 origin=pg.evaluate("()=>{for(let y=1000;y<5000;y+=120)for(let x=1000;x<5000;x+=120)if([[x,y],[x+200,y],[x-200,y],[x,y+200],[x,y-200]].every(([a,b])=>!MossForest.blocked(a,b)))return [x,y];return null}")
 ck(bool(origin),'clear four-direction test crossing')
 if origin:
  for d,dx,dy in [('up',0,-200),('down',0,200),('left',-200,0),('right',200,0)]:
   pg.evaluate('([x,y])=>MossForest.teleportFeet(x,y)',origin);pg.wait_for_timeout(200)
   ck(pg.evaluate('([x,y])=>MossForest.goFeet(x,y)',[origin[0]+dx,origin[1]+dy]),d+' actual goFeet accepted')
   try:pg.wait_for_function("d=>{const n=document.querySelector('.forest-aidan:not([hidden])');return n&&n.getAttribute('src').split('/').pop().startsWith('aidan_walk_'+d+'_')}",arg=d,timeout=1500);shown=True
   except Exception:shown=False
   ck(shown,d+' visible moving frame matches direction')
 b.close()
ck(not errors,'no console/page errors '+str(errors[:3]))
for w in warnings:print('WARN '+json.dumps(w,ensure_ascii=False))
print('METRICS '+json.dumps(metrics));print('FAILS',len(fails));sys.exit(bool(fails))
