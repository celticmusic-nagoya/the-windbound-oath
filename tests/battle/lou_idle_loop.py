# Lou raider-battle floating idle: 6 frames load, loop 1->6->1 at ~6 FPS, canvas is single, stops with the battle. Needs http.server on 8765.
import sys
from playwright.sync_api import sync_playwright
fails=[];errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
VP={'pc':(1280,720),'portrait':(390,844),'landscape':(844,390)}
with sync_playwright() as p:
    b=p.chromium.launch()
    for name,(w,h) in VP.items():
        pg=b.new_page(viewport={'width':w,'height':h})
        pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
        pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(800)
        a=pg.evaluate("BATTLE_IDLE_ASSETS.lou"); check(a['frames'].__len__()==6 and a['fps']==6,'%s: 6 frames @6fps'%name)
        ld=pg.evaluate("Promise.all(BATTLE_IDLE_ASSETS.lou.frames.map(f=>new Promise(r=>{const i=new Image();i.onload=()=>r([i.naturalWidth,i.naturalHeight]);i.onerror=()=>r(null);i.src=f.path})))")
        check(all(x==[442,724] for x in ld),'%s: all frames load at 442x724'%name)
        pg.evaluate("devJump('raider')"); pg.wait_for_timeout(9000)
        st=pg.evaluate("BattleIdleMotion.status.actors.find(a=>a.actor==='lou')")
        check(bool(st and st['showing']),'%s: Lou idle showing %s'%(name,st))
        check(pg.evaluate("document.querySelectorAll('#rbLou canvas').length")==1,'%s: exactly one canvas'%name)
        seq=[]
        for i in range(30):
            pg.wait_for_timeout(55); f=pg.evaluate("document.querySelector('#rbLou canvas')?.dataset.frame")
            if f is not None and (not seq or seq[-1]!=f): seq.append(f)
        steps=[(int(seq[i+1])-int(seq[i]))%6 for i in range(len(seq)-1)]
        check(len(seq)>=6 and all(s==1 for s in steps),'%s: frames advance 1->2->..->6->1 %s'%(name,seq))
        # battle end stops the loop
        pg.evaluate("document.body.classList.remove('raiderBattleMode','battleMode')"); pg.wait_for_timeout(500)
        ev=pg.evaluate("BattleIdleMotion.status.actors.find(a=>a.actor==='lou')")
        check(not ev['showing'] and not ev['scheduled'] if 'scheduled' in ev else not ev['showing'],'%s: idle stops when the battle mode ends'%name)
        check(not pg.evaluate("BattleIdleMotion.status.scheduled"),'%s: no animation frame left scheduled'%name)
        pg.close()
    check(not errs,'no console errors %s'%errs[:3])
    b.close()
print('FAILS %d'%len(fails)); sys.exit(1 if fails else 0)
