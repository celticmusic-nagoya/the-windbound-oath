# Keyboard: story scenes advance one line per press (held key does not skip), battle result screen continues with Enter, inside-room walking. Needs http.server on 8765.
import sys
from playwright.sync_api import sync_playwright
fails=[];errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200); pg.evaluate("closeDialogue()")
    st=lambda: pg.evaluate("InputManager.state()")
    # indoor room walking
    pg.evaluate("document.querySelector('#forestScene').style.display='none';document.querySelector('#inside').style.display='block';ipx=400;ipy=400")
    pg.keyboard.down('ArrowRight'); pg.wait_for_timeout(500); pg.keyboard.up('ArrowRight')
    check(pg.evaluate("ipx")>410,'indoor room: arrow keys walk (ipx %s)'%pg.evaluate("ipx"))
    pg.evaluate("document.querySelector('#inside').style.display='none';document.querySelector('#forestScene').style.display='block'")
    # altar scene
    pg.evaluate("document.querySelector('#forestScene').style.display='none';startAltarScene()"); pg.wait_for_timeout(600)
    check(st()=='SCENE','altar scene is the SCENE state (%s)'%st())
    txt=lambda: pg.evaluate("document.querySelector('#altarText').textContent")
    t0=txt(); pg.keyboard.press('Enter'); pg.wait_for_timeout(250); t1=txt()
    check(t1!=t0,'Enter advances the scene')
    pg.keyboard.down('Enter')
    for _ in range(6): pg.keyboard.down('Enter')
    pg.keyboard.up('Enter'); pg.wait_for_timeout(300)
    A=pg.evaluate("altarLines"); i1=A.index(t1) if t1 in A else -1; i2=A.index(txt()) if txt() in A else -1
    check(i1>=0 and i2==i1+1,'a held Enter advances exactly one line (%s -> %s)'%(i1,i2))
    pg.keyboard.press('Space'); pg.wait_for_timeout(250); i3=A.index(txt()) if txt() in A else -1
    check(i3==i2+1,'Space also advances')
    pg.evaluate("document.querySelector('#altarScene').style.display='none'")
    # battle result
    pg.evaluate("document.querySelector('#forestScene').style.display='block'")
    pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(600); pg.evaluate("closeDialogue()")
    pg.evaluate("startAttackBattle('forestBat1',112)"); pg.wait_for_timeout(3500)
    pg.evaluate("document.querySelector('#nDevKill').click()")
    for _ in range(60):
        pg.wait_for_timeout(250)
        if st()=='RESULT': break
    check(st()=='RESULT','victory shows the result screen (%s)'%st())
    pg.keyboard.press('Enter'); pg.wait_for_timeout(1500)
    check(st() in ('FIELD','DIALOGUE') and not pg.evaluate("document.body.classList.contains('battleMode')"),'Enter leaves the result screen back to the field (%s)'%st())
    check(not errs,'no errors %s'%errs[:3]); b.close()
print('FAILS %d'%len(fails)); sys.exit(1 if fails else 0)
