"""Trace Lou idle through altar completion, commands and real enemy turn."""
import json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path('docs/qa/lou-idle-real-flow-20261013');OUT.mkdir(parents=True,exist_ok=True)
rows=[];runs=[];errors=[]
def check(ok,name,detail=None):
    rows.append(dict(name=name,ok=bool(ok),detail=detail));print(('ok   ' if ok else 'FAIL ')+name,detail or '')
with server(8813) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    for reduced in ['no-preference','reduce']:
        ctx=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,reduced_motion=reduced)
        pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(base+'/index.html');pg.wait_for_function('window.BattleIdleMotion');pg.wait_for_timeout(1400)
        # Starting at altar is permitted. NEVER devJump('raider'): the altar's original last click starts battle.
        pg.evaluate("closeDialogue();devJump('altar');window.qaPhase='altar';window.qaTimeline=[];window.qaTrace=setInterval(()=>qaTimeline.push({ms:performance.now(),phase:qaPhase,classes:document.body.className,hidden:document.hidden,state:InputManager.state(),idle:BattleIdleMotion.status,canvas:document.querySelector('#rbLou canvas')?.dataset.frame,hp:[rbHP,rbFHP],round:rbRound}),250)")
        n=pg.evaluate('altarLines.length')
        for _ in range(n):pg.locator('#altarScene').click();pg.wait_for_timeout(35)
        pg.wait_for_function("document.body.classList.contains('raiderBattleMode')",timeout=30000);pg.evaluate("qaPhase='initial-idle'")
        pg.wait_for_function("BattleIdleMotion.status.actors.some(a=>a.actor==='lou' && a.showing)",timeout=20000);pg.wait_for_timeout(3000)
        check(pg.evaluate('oathBound && storyStage===12'),'altar contract then original battle start / '+reduced)
        seq=pg.evaluate("qaTimeline.filter(x=>x.phase==='initial-idle').map(x=>x.canvas)")
        check(len(set(x for x in seq if x is not None))>=5,'initial Lou loop advances / '+reduced,seq)
        pg.evaluate("qaPhase='aidan-command';setRaiderCommandDrawer(true)");pg.locator('#rbGuard').tap();pg.wait_for_function("rbActor==='fiona'");pg.wait_for_timeout(750)
        pg.evaluate("qaPhase='enemy-turn';setRaiderCommandDrawer(true)");pg.locator('#rbGuard').tap();pg.wait_for_function('rbBusy',timeout=10000)
        pg.wait_for_function('!rbBusy && !BattlePresentation.busy',timeout=30000);pg.evaluate("qaPhase='post-hit-idle'");pg.wait_for_timeout(3000)
        check(pg.evaluate('rbRound>=2 && (rbHP<120 || rbFHP<105)'),'actual enemy turn damages heroes / '+reduced,pg.evaluate('[rbHP,rbFHP,rbRound]'))
        seq=pg.evaluate("qaTimeline.filter(x=>x.phase==='post-hit-idle').map(x=>x.canvas)")
        check(len(set(x for x in seq if x is not None))>=5,'Lou resumes after turn / '+reduced,seq)
        pg.screenshot(path=str(OUT/(reduced+'.png')));timeline=pg.evaluate('clearInterval(qaTrace);qaTimeline');runs.append(dict(reducedMotion=reduced,timeline=timeline));ctx.close()
    check(not errors,'page errors',errors);b.close()
(OUT/'results.json').write_text(json.dumps(dict(base='31a5f5e',rows=rows,runs=runs,errors=errors,intervalMs=250,device='Cloud Chromium mobile emulation, not Android'),ensure_ascii=False,indent=2))
n=sum(not r['ok'] for r in rows);print('FAILS',n);sys.exit(bool(n))
