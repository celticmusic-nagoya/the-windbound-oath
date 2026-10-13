"""2.5D test mode switch: default off; ?height25d=1 on (sticky); ?height25d=0 off; saves stay compatible both ways."""
import json,os,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.qa.browser_support import server
fails=[];errors=[]
def ck(c,m):
 print(('ok   ' if c else 'FAIL ')+m,flush=True)
 if not c:fails.append(m)
CLIFF="storyStage=3;closeDialogue();MossForestStory.enterCliff()"
def enter(pg):
 pg.evaluate('PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=15;closeDialogue();enterMossForest()');pg.wait_for_timeout(2000)
 pg.evaluate(CLIFF);pg.wait_for_function("MossForest.mapId==='cliff_moher_01_spiral_ascent'",timeout=15000);pg.wait_for_timeout(800)
with server(8797) as base, sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE') or None)
 def page(url,ctx):
  pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(base+url);pg.wait_for_timeout(1500);return pg
 # 1 default: off
 ctx=b.new_context(viewport={'width':844,'height':390});pg=page('/index.html?dev=1&legacyVillage=1',ctx);enter(pg)
 ck(pg.evaluate('!!MossForest.height')==False,'default: cliff has no height (normal mode)')
 ck(pg.locator('#height25dBadge').count()==0,'default: no badge')
 pos=pg.evaluate('({x:MossForest.feet.x,y:MossForest.feet.y})');snap_plain=pg.evaluate('MossForest.snapshot()');ck('level' not in snap_plain,'default: snapshot has no level')
 pg.close()
 # 2 on
 pg=page('/index.html?dev=1&legacyVillage=1&height25d=1',ctx);enter(pg)
 ck(pg.evaluate('!!MossForest.height'),'?height25d=1: height active on the cliff')
 ck(pg.locator('#height25dBadge').count()==1,'?height25d=1: badge shown')
 snap=pg.evaluate('MossForest.snapshot()');ck(snap.get('level')==0,'2.5D snapshot carries level 0')
 pg.close()
 # 3 sticky (same browser context, plain URL)
 pg=page('/index.html?dev=1&legacyVillage=1',ctx);enter(pg)
 ck(pg.evaluate('!!MossForest.height'),'sticky: plain URL keeps 2.5D on this browser')
 pg.close()
 # 4 off
 pg=page('/index.html?dev=1&legacyVillage=1&height25d=0',ctx);enter(pg)
 ck(pg.evaluate('!!MossForest.height')==False,'?height25d=0: off again')
 # 5 a save written with a level loads in normal mode without errors and ignores level
 res=pg.evaluate("(async()=>{try{restoreSnap={map:'cliff_moher_01_spiral_ascent',x:300,y:3700,level:1,opened:[],fired:[]};await MossForest.enter({map:'cliff_moher_01_spiral_ascent',x:300,y:3700,level:1});return MossForest.mapId+':'+MossForest.level}catch(e){return String(e)}})()")
 ck(res=='cliff_moher_01_spiral_ascent:0','normal mode: a saved level is ignored, player stands on the plain map (%s)'%res)
 pg.close();ctx.close()
 # 6 other maps unaffected with mode on: Rilde village / forest A1 load without a height
 ctx=b.new_context(viewport={'width':390,'height':844});pg=page('/index.html?dev=1&legacyVillage=1&height25d=1',ctx)
 pg.evaluate('PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=15;closeDialogue();enterMossForest()');pg.wait_for_timeout(2500)
 ck(pg.evaluate('!!MossForest.height')==False,'mode on: A1 (no spec) stays plain 2D on mobile viewport')
 pg.close();ctx.close();b.close()
ck(not errors,'no page errors '+str(errors[:3]))
print('FAILS',len(fails));sys.exit(bool(fails))
