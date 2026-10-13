"""CC: immutable delivered boar assets, real rush poses and battle KO timeline."""
import json,os,sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.qa.browser_support import server
fails=[];errors=[];metrics=[]
def ck(c,m):
 print(('ok   'if c else 'FAIL ')+m,flush=True)
 if not c:fails.append(m)
for group,size,feet in [('battle',(480,400),390),('field',(240,160),154)]:
 files=sorted((ROOT/('img/battle/enemies/leafy_boar' if group=='battle' else 'img/field/monsters/leafy_boar')).rglob('*.png'))
 ck(len(files)==(23 if group=='battle' else 11),group+' expected delivered file count '+str(len(files)))
 for f in files:
  with Image.open(f) as im:
   ck(im.mode=='RGBA' and im.size==size,str(f.relative_to(ROOT))+' RGBA dimensions')
   box=im.getchannel('A').getbbox();ck(bool(box),f.name+' nonempty')
   if box:
    cx=(box[0]+box[2])/2;ck(abs(cx-size[0]/2)<=1,f.name+' alpha bbox centered ±1px');ck(abs(box[3]-feet)<=1,f.name+' feet row '+str(box[3]))
    metrics.append({'file':str(f.relative_to(ROOT)),'bbox':box,'bbox_center_x':cx,'canvas_center_x':size[0]/2,'alpha_mean':sum(im.getchannel('A').getdata())/(im.width*im.height)})
manifest=json.loads((ROOT/'img/battle/motion-manifest.json').read_text());ko=manifest['motions']['leafy_boar']['ko'];ck(ko['frames']==6,'KO manifest has six frames')
with server(8798) as base,sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE') or None);pg=b.new_page(viewport={'width':844,'height':390})
 pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('console',lambda m:errors.append(m.text)if m.type=='error'else None)
 pg.goto(base+'/index.html?dev=1');pg.wait_for_timeout(2300);pg.evaluate('closeDialogue();PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=9;enterMossForest()');pg.wait_for_timeout(2400)
 poses=pg.evaluate('FieldMonsters.MONSTER_TYPES.leafy_boar.art.poses');ck(poses=={'alert':[4],'engage':[4],'windup':[5,6],'rush':[7,8,9],'recover':[10]},'field pose indexes match declared1-based5/6-7/8-10/11')
 pg.evaluate("MossForest.enter({map:'road_dunvall_capital_01',spawn:'from_fort'})");pg.wait_for_timeout(1800)
 pg.evaluate("MossForest.map.monsters=[{id:'cc_boar',type:'leafy_boar',x:2400,y:1300}];MossForest.enter({map:'road_dunvall_capital_01',spawn:'from_fort'})");pg.wait_for_timeout(1600)
 pg.evaluate("window.__rush=[];window.__ccLoop=true;(function tick(){for(const m of MossForest.monsters)if(m.state==='rush')__rush.push(m.el.dataset.src);if(__ccLoop)requestAnimationFrame(tick)})();MossForest.teleportFeet(2400,1500)")
 pg.wait_for_timeout(700);pg.evaluate('MossForest.teleportFeet(2700,1700)');pg.wait_for_timeout(2000)
 rush=pg.evaluate('[...new Set(__rush)]');ck(bool(rush) and all(any(('leafy_boar_%02d.png'%n)in x for n in (8,9,10))for x in rush),'actual rush uses frames8-10 '+str(rush))
 pg.evaluate('window.__ccLoop=false;FieldMonsters.removeAll();startAttackBattle("leafyBoar1",147)');pg.wait_for_timeout(1700)
 pg.evaluate("window.__ko=[];window.__koLoop=true;window.__koStart=performance.now();(function tick(){const n=document.querySelector('#bGob img');__ko.push({ms:performance.now()-__koStart,src:n?.getAttribute('src'),visible:!!n&&n.getBoundingClientRect().width>0&&getComputedStyle(n).visibility!=='hidden',battle:document.body.classList.contains('normalBattleMode'),result:getComputedStyle(document.querySelector('#battleResult')).display!=='none'});if(__koLoop)requestAnimationFrame(tick)})();PrologueCombat.instantKill('normal')")
 pg.wait_for_timeout(3000);timeline=pg.evaluate('__ko');seen={int(x['src'].split('_ko_')[1].split('.')[0])for x in timeline if x['src'] and '_ko_'in x['src']};ck(seen==set(range(1,7)),'real battle plays KO frames1-6 '+str(sorted(seen)))
 for _ in range(8):
  if pg.evaluate("getComputedStyle(document.querySelector('#battleResult')).display==='none'"):break
  pg.evaluate("(document.querySelector('#battleResult button')||document.querySelector('#battleResult')).click()");pg.wait_for_timeout(500)
 pg.wait_for_timeout(1300);pg.evaluate('window.__koLoop=false');after=pg.evaluate("(()=>{const n=document.querySelector('#bGob img');return {src:n.getAttribute('src'),visible:n.getBoundingClientRect().width>0,battle:document.body.classList.contains('normalBattleMode'),forest:forestActive}})()")
 print('KO_TIMELINE '+json.dumps(timeline));print('POST_BATTLE '+json.dumps(after));ck(not after['visible'],'faded terminal art not visible after battle result closes')
 b.close()
ck(not errors,'no console/page errors '+str(errors[:3]));print('METRICS '+json.dumps(metrics));print('FAILS',len(fails));sys.exit(bool(fails))
