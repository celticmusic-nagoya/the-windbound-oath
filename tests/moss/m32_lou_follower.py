# Lou follows on forest maps once she has joined (PartyManager.support.joined); hidden before; idle loop animates. Needs http.server on 8765.
import sys
from playwright.sync_api import sync_playwright
fails=[];errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1000,'height':640})
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(800)
    pg.evaluate("devJump('map:dev_monster_arena')"); pg.wait_for_timeout(2500)
    vis=lambda: pg.evaluate("(()=>{const e=document.querySelector('#forestLou');return e?getComputedStyle(e).display:'none'})()")
    pg.evaluate("PartyManager.support.joined=false"); pg.wait_for_timeout(400)
    check(vis()=="none","hidden before joining")
    pg.evaluate("PartyManager.support.joined=true"); pg.wait_for_timeout(600)
    check(vis()=='block','visible after joining')
    seq=[]
    for i in range(25):
        pg.wait_for_timeout(60); f=pg.evaluate("[...document.querySelectorAll('#forestLou img')].findIndex(i=>!i.hidden)")
        if not seq or seq[-1]!=f: seq.append(f)
    check(len(set(seq))>=5,'idle frames cycle %s'%seq)
    pg.keyboard.down('ArrowRight'); pg.wait_for_timeout(1200); pg.keyboard.up('ArrowRight'); pg.wait_for_timeout(800)
    d=pg.evaluate("(()=>{const l=document.querySelector('#forestLou').getBoundingClientRect(),f=document.querySelector('#forestFiona').getBoundingClientRect();return [l.x,f.x,l.width,l.height]})()")
    check(d[0]<d[1]+60,'Lou trails near Fiona %s'%d)
    pg.screenshot(path='/tmp/aw/lou_field.png')
    check(not errs,'no errors %s'%errs[:2]); b.close()
print('FAILS %d'%len(fails)); sys.exit(1 if fails else 0)
