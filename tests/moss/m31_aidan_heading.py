# Aidan walk heading: straight up/down -> frontal/back art, diagonal -> 3/4 art (mirrored to the right), sideways -> side art. Needs http.server on 8765.
import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
fails=[];errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with server(8822) as base, sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium')); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto(base+'/index.html'); pg.wait_for_function('window.AidanHeading && window.MossForest && MossForest.active && !MossForest.busy',timeout=30000)
    r=pg.evaluate("""(()=>{const run=(dx,dy,n=10)=>{const h=AidanHeading.create();let r;for(let i=0;i<n;i++)r=h.step(dx,dy);return r.dir+(r.flip?'F':'')};
      return {down:run(0,2),up:run(0,-2),right:run(2,0),left:run(-2,0),dr:run(2,2),dl:run(-2,2),ur:run(2,-2),ul:run(-2,-2),steep:run(.5,2),shallow:run(2,.5)}})()""")
    check(r=={'down':'down','up':'up','right':'right','left':'left','dr':'dlF','dl':'dl','ur':'ulF','ul':'ul','steep':'down','shallow':'right'},'heading classes %s'%r)
    jit=pg.evaluate("""(()=>{const h=AidanHeading.create();const seq=[];for(let i=0;i<40;i++){const r=h.step(i%2?2.6:2.4,2.5);seq.push(r.dir)}return new Set(seq.slice(5)).size})()""")
    check(jit==1,'jitter around 45deg does not flicker between sets (%s)'%jit)
    pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active && !MossForest.busy && MossForest.mapId==='moss_forest_01_sunlit_path'",timeout=30000); pg.wait_for_timeout(600); pg.evaluate("closeDialogue()"); pg.wait_for_function("[...document.querySelectorAll('.forest-aidan')].every(i=>i.complete&&i.naturalWidth>0)",timeout=30000)
    pg.evaluate("MossForest.encounters(false)")
    # Runtime spr.state is private. IDLE has no bob/mirror transform; require that
    # renderer condition AND unchanged feet/frame across >=160ms (runtime settles at110ms).
    # Never wait for the expected direction, which would conceal a wrong-heading failure.
    def idle():
        pg.evaluate("window.__headingIdle=null")
        pg.wait_for_function("""(()=>{const i=[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden),f=MossForest.feet,n=performance.now();if(!i)return false;
          const last=window.__headingIdle;if(!last||last.x!==f.x||last.y!==f.y||last.src!==i.dataset.src||i.style.transform){window.__headingIdle={x:f.x,y:f.y,src:i.dataset.src,since:n};return false}
          return n-last.since>=160 && !MossForest.target;})()""",timeout=10000,polling='raf')
    def walk(keys):
        idle(); origin=pg.evaluate('MossForest.feet');seen=set()
        try:
            for k in keys: pg.keyboard.down(k)
            pg.wait_for_function("""start=>{const f=MossForest.feet,i=[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden);return Math.hypot(f.x-start.x,f.y-start.y)>1 && i && !!i.style.transform} """,arg=origin,timeout=5000,polling='raf')
            for i in range(20):
                pg.wait_for_timeout(60)
                n=pg.evaluate("(()=>{const i=[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden);return i?i.dataset.src.split('/').pop().split('?')[0].split('_').slice(2,-1).join('_')+(i.style.transform.includes('scaleX')?'F':''):null})()")
                seen.add(n)
        finally:
            for k in keys: pg.keyboard.up(k)
        idle(); return seen
    s=walk(['ArrowDown']); check(s=={'down'},'straight down uses walk_down %s'%s)
    s=walk(['ArrowUp']); check(s=={'up'},'straight up uses walk_up %s'%s)
    s=walk(['ArrowRight','ArrowDown']); check('dlF' in s and 'down' not in s,'down-right uses mirrored 3/4 %s'%s)
    s=walk(['ArrowLeft','ArrowUp']); check('ul' in s and 'up' not in s,'up-left uses 3/4 back %s'%s)
    s=walk(['ArrowRight']); check(s<={'right'},'sideways uses walk_right %s'%s)
    pg.keyboard.down('ArrowLeft'); pg.keyboard.down('ArrowDown'); idx=[]
    for i in range(80):
        pg.wait_for_timeout(40); n=pg.evaluate("(()=>{const i=[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden);const m=i&&i.dataset.src.match(/walk_dl_(\\d+)/);return m?+m[1]:null})()")
        if n and (not idx or idx[-1]!=n): idx.append(n)
    pg.keyboard.up('ArrowLeft'); pg.keyboard.up('ArrowDown')
    check(len(set(idx))>=10 and max(idx)==12,'down-left diagonal cycles the 12-frame walk %s'%idx)
    check(not errs,'no console errors %s'%errs[:3])
    b.close()
print('FAILS %d'%len(fails)); sys.exit(1 if fails else 0)
