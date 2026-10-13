# Aidan walk heading: straight up/down -> frontal/back art, diagonal -> 3/4 art (mirrored to the right), sideways -> side art. Needs http.server on 8765.
import sys
from playwright.sync_api import sync_playwright
fails=[];errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    r=pg.evaluate("""(()=>{const run=(dx,dy,n=10)=>{const h=AidanHeading.create();let r;for(let i=0;i<n;i++)r=h.step(dx,dy);return r.dir+(r.flip?'F':'')};
      return {down:run(0,2),up:run(0,-2),right:run(2,0),left:run(-2,0),dr:run(2,2),dl:run(-2,2),ur:run(2,-2),ul:run(-2,-2),steep:run(.5,2),shallow:run(2,.5)}})()""")
    check(r=={'down':'down','up':'up','right':'right','left':'left','dr':'dlF','dl':'dl','ur':'ulF','ul':'ul','steep':'down','shallow':'right'},'heading classes %s'%r)
    jit=pg.evaluate("""(()=>{const h=AidanHeading.create();const seq=[];for(let i=0;i<40;i++){const r=h.step(i%2?2.6:2.4,2.5);seq.push(r.dir)}return new Set(seq.slice(5)).size})()""")
    check(jit==1,'jitter around 45deg does not flicker between sets (%s)'%jit)
    pg.evaluate("devJump('forest')"); pg.wait_for_timeout(8000); pg.evaluate("closeDialogue()")
    pg.evaluate("MossForest.encounters(false)")
    def walk(keys):
        seen=set()
        for k in keys: pg.keyboard.down(k)
        for i in range(20):
            pg.wait_for_timeout(60)
            n=pg.evaluate("(()=>{const i=[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden);return i?i.dataset.src.split('/').pop().split('?')[0].split('_').slice(2,-1).join('_')+(i.style.transform.includes('scaleX')?'F':''):null})()")
            seen.add(n)
        for k in keys: pg.keyboard.up(k)
        pg.wait_for_timeout(700); return seen
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
