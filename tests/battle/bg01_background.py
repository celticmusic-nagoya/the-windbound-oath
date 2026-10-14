"""BG-01 battle background: assignment by enemy id, layer geometry/z-order, no-bg fallback, load-failure fallback, boss untouched."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail)
    if not ok:fails.append(name)
check((ROOT/'img/battle/backgrounds/bg_BG-01_main.png').read_bytes()==(ROOT/'docs/art/delivered/bg01_20261014/bg_BG-01_main_original.png').read_bytes(),'implemented image == untouched original')
STATE="""()=>{const r=document.getElementById('attackBattle'),l=document.getElementById('battleBg'),s=document.querySelector('#attackBattle>.v2BattleStage');const sb=s.getBoundingClientRect(),lb=l.getBoundingClientRect();
 return {bg:r.dataset.bg||null,disp:getComputedStyle(l).display,img:l.style.backgroundImage,z:getComputedStyle(l).zIndex,first:s.firstElementChild===l,covers:lb.left<=sb.left+1&&lb.right>=sb.right-1&&lb.top<=sb.top+1&&lb.bottom>=sb.bottom-1,
 stageBg:getComputedStyle(s).backgroundImage,ptr:getComputedStyle(l).pointerEvents}}"""
def start(pg,call):
    pg.evaluate("BattleBackground.clear();document.getElementById('attackBattle').style.display='none';document.body.classList.remove('battleMode','normalBattleMode')");pg.evaluate(call);pg.wait_for_timeout(600)
with server(8817) as base,sync_playwright() as p:
    b=p.chromium.launch()
    for n,w,h in (('pc',1280,720),('land',844,390),('port',390,844)):
        pg=b.new_page(viewport={'width':w,'height':h});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.InputManager&&window.BattleBackground');pg.wait_for_timeout(1200);pg.evaluate('closeDialogue()')
        for eid in ('attackGob1','attackGob2','northGob1','northGob2'):
            start(pg,"startAttackBattle('%s',100)"%eid);s=pg.evaluate(STATE)
            check(s['bg']=='BG-01' and s['disp']=='block' and 'bg_BG-01_main.png' in s['img'],'%s %s: BG-01 applied'%(n,eid))
        check(s['z']=='0' and s['first'] and s['covers'] and s['ptr']=='none' and s['stageBg']=='none','%s: layer is first child, z0, covers stage, no pointer events, stage gradient off'%n,s)
        for eid in ('mossSlime1','forestBat1','fieldGob1'):
            start(pg,"startAttackBattle('%s',100)"%eid);s=pg.evaluate(STATE)
            check(s['bg'] is None and s['disp']=='none' and s['stageBg']!='none','%s %s: no BG-01, existing stage gradient kept'%(n,eid))
        pg.evaluate("document.getElementById('attackBattle').style.display='none';document.body.classList.remove('battleMode','normalBattleMode')")
        pg.evaluate('startRaiderBattle()');pg.wait_for_timeout(800)
        check(pg.evaluate("document.getElementById('attackBattle').dataset.bg||null") is None and pg.evaluate("getComputedStyle(document.getElementById('raiderBattle')).display")=='block','%s: boss battle has no BG-01'%n)
        check(not errs,'%s: no page errors'%n,errs);pg.close()
    # load failure -> fallback
    pg=b.new_page(viewport={'width':1280,'height':720});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/bg_BG-01_main.png',lambda r:r.abort())
    pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.InputManager&&window.BattleBackground');pg.wait_for_timeout(1200);pg.evaluate('closeDialogue()')
    pg.evaluate("startAttackBattle('northGob1',100)");pg.wait_for_timeout(1500);s=pg.evaluate(STATE)
    check(s['bg'] is None and s['disp']=='none' and s['stageBg']!='none','image load failure: falls back to existing stage gradient',s)
    check(pg.evaluate("getComputedStyle(document.getElementById('bAidan2')).display")!='none' and pg.evaluate("document.getElementById('attackBattle').style.display")=='block','image load failure: battle still runs')
    check(not errs,'image load failure: no uncaught errors',errs);pg.close()
print('FAILS',fails) if fails else print('ALL OK');sys.exit(1 if fails else 0)
