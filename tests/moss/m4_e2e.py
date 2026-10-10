# M4 through-play via index.html. usage: m4_e2e.py   (needs python3 -m http.server 8765 in repo root; playwright)
import sys, json
from playwright.sync_api import sync_playwright
URL='http://localhost:8765/index.html'
errs=[]; fails=[]
def check(c,msg):
    print(('ok   ' if c else 'FAIL ')+msg)
    if not c: fails.append(msg)
GO="""async ([x,y,ms])=>{const sleep=t=>new Promise(r=>setTimeout(r,t));
  const m0=MossForest.mapId;if(!MossForest.goFeet(x,y))return {ok:false,why:'unreachable'};const t0=performance.now();
  while(MossForest.target&&performance.now()-t0<(ms||120000)&&MossForest.mapId===m0&&MossForest.active)await sleep(100);
  return {ok:true,why:MossForest.mapId===m0?MossForest.status.outcome:'changed',map:MossForest.mapId,active:MossForest.active};}"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1920,'height':1080})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    def dom(): return pg.evaluate("document.querySelectorAll('#forestScene *').length")
    def wait_map(mid,t=30000): pg.wait_for_function("(m)=>MossForest.mapId===m&&MossForest.active&&!MossForest.busy",arg=mid,timeout=t)
    def go(x,y,ms=120000): return pg.evaluate(GO,[x,y,ms])
    def paths(): return {q['id']:q['points'] for q in pg.evaluate("MossForest.map.terrain.paths")}
    def walk_path(pid,upto=None):
        pts=paths()[pid]; pg.evaluate("([x,y])=>MossForest.teleportFeet(x,y)",pts[0]); bad=[]
        for pt in (pts[1:upto] if upto else pts[1:]):
            r=go(*pt)
            if not r['ok'] or r['why'] not in ('arrived','changed','moving'): bad.append((pt,r['why']))
        return bad
    pg.goto(URL); pg.wait_for_timeout(1200)
    # ---- 1. entry (new game flow from DEV jump 'forest' = stage 9)
    pg.evaluate("devJump('forest')"); wait_map('moss_forest_01_sunlit_path')
    check(pg.evaluate("storyStage")==9,'stage 9 on entry'); check(pg.evaluate("MOSS_RT"),'new runtime active')
    pg.wait_for_timeout(600); check('近付くなって' in pg.evaluate("document.querySelector('#msg').textContent"),'Fiona stage-9 line (elder/Emma warning wording)')
    pg.evaluate("closeDialogue()")
    # ---- 2. A1 -> A2 -> A3 by walking (click-to-move) through the exits
    bad=walk_path('path_main'); check(not bad,'A1 path_main walked %s'%bad)
    r=go(7700,20); wait_map('moss_forest_02_mossy_ravine'); check(True,'A1 -> A2 transition')
    bad=walk_path('path_main'); check(not bad,'A2 path_main walked %s'%bad)
    r=go(1600,20); wait_map('moss_forest_03_ancient_grove'); check(True,'A2 -> A3 transition')
    # ---- 3. A3 closed seal
    check(pg.evaluate("MossForest.flags.moss_a3_seal_open")==False and pg.evaluate("MossForest.sealNodes")==1,'A3 seal closed + visual')
    pg.evaluate("closeDialogue()")
    bad=walk_path('path_main',upto=-1); check(not bad,'A3 path_main to the throat %s'%bad)
    r=go(3900,3250); pos=pg.evaluate("MossForest.feet"); check(pos['y']>3289,'closed seal blocks the route (fy=%d, %s)'%(pos['y'],r['why']))
    # ---- 4. three symbols via touch -> battle -> victory
    for i in range(3):
        sy=pg.evaluate("MossForest.map.story.prologue.symbols[%d]"%i)
        pg.evaluate("([x,y])=>MossForest.teleportFeet(x,y)",[sy['x']-260,sy['y']])
        pg.evaluate("closeDialogue()")
        go(sy['x'],sy['y'],60000)
        pg.wait_for_function("document.querySelector('#attackBattle').style.display==='block'",timeout=15000)
        check(pg.evaluate("MossForest.active")==False,'symbol %d: battle started, forest paused'%i)
        pg.wait_for_timeout(600); pg.evaluate("PrologueCombat.instantKill('normal')")
        pg.wait_for_function("getComputedStyle(document.querySelector('#battleResult')).display!=='none'",timeout=20000)
        pg.evaluate("document.querySelector('#resultContinue').click()")
        pg.wait_for_function("MossForest.active",timeout=15000)
        check(pg.evaluate("PrologueProgress.count()")==i+1,'symbol %d defeated (count %d)'%(i,i+1))
    pg.wait_for_timeout(1500)
    check(pg.evaluate("MossForest.flags.moss_a3_seal_open")==True,'3 symbols -> seal flag open'); check(pg.evaluate("MossForest.sealNodes")==0,'seal visual removed')
    check(pg.evaluate("storyStage")>=10,'stage >=10 after seal')
    # ---- 5. pass the seal, Lou intro, wind path, altar
    pg.evaluate("closeDialogue()"); pg.evaluate("([x,y])=>MossForest.teleportFeet(x,y)",[3900,3400])
    r=go(3900,3250); check(r['why']=='arrived','open seal: passes (3900,3250) (%s)'%r['why'])
    bad=walk_path('path_main_inner'); 
    pg.wait_for_function("document.querySelector('#louIntroScene').style.display==='block'",timeout=15000); check(True,'Lou intro auto-starts at the sanctuary')
    for i in range(10): pg.evaluate("document.querySelector('#louIntroScene').click()")
    pg.wait_for_function("MossForest.active",timeout=10000)
    check(pg.evaluate("louFound")==True and pg.evaluate("storyStage")==11,'Lou found, stage 11'); check(pg.evaluate("MossForest.flags.moss_a3_lou_found"),'lou_found flag in runtime')
    pg.evaluate("closeDialogue()")
    bad=walk_path('path_hidden_wind'); 
    pg.wait_for_function("document.querySelector('#altarScene').style.display==='block'",timeout=15000); check(True,'altar scene starts from the hidden wind path')
    check(pg.evaluate("MossForest.active")==False,'forest paused during altar scene')
    # ---- 6. node budget
    peak=pg.evaluate("MossForest.forest?MossForest.forest.cull.stats.peak:0"); check(peak<=800,'A3 peak live nodes %d <= 800'%peak)
    print('errors',errs[:6])
    b.close()
sys.exit(1 if (fails or errs) else 0)
