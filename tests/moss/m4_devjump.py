# Every DEV jump entry must run without console errors; forest entries land in the right map/state.
import sys
from playwright.sync_api import sync_playwright
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    keys=['opening','training','sunset','attack','mother','fionaRescue','north','escape','forest','moss1','moss2','moss3','barrierBefore','barrierAfter','lou','altar','raider','aftermath','fort','prologueEnd']
    for k in keys:
        pg.evaluate("(k)=>devJump(k)",k); pg.wait_for_timeout(2500 if k in('forest','moss1','moss2','moss3','barrierBefore','barrierAfter','lou') else 700)
        st=pg.evaluate("({stage:storyStage,map:MossForest.mapId,act:MossForest.active,vis:document.querySelector('#forestScene').style.display,count:PrologueProgress.count(),seal:MossForest.flags.moss_a3_seal_open,bat:document.querySelector('#attackBattle').style.display,intro:document.querySelector('#louIntroScene').style.display})")
        print(k,st)
        pg.evaluate("document.querySelector('#attackBattle').style.display='none';document.body.classList.remove('battleMode','normalBattleMode')")
    print('errors',errs[:6]); b.close()
sys.exit(1 if errs else 0)
