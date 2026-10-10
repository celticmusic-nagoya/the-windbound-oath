# Mobile-emulation smoke test: touch tap-to-move in the forest at phone sizes (landscape + portrait).
import sys
from playwright.sync_api import sync_playwright
errs=[];fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    for name,vp in [('landscape',{'width':844,'height':390}),('portrait',{'width':390,'height':844})]:
        ctx=b.new_context(viewport=vp,device_scale_factor=2,is_mobile=True,has_touch=True)
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
        pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
        pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(900); pg.evaluate("closeDialogue()")
        f0=pg.evaluate("MossForest.feet"); w=pg.evaluate("[innerWidth,innerHeight]")
        pg.touchscreen.tap(w[0]*0.75,w[1]*0.45); pg.wait_for_timeout(1500)
        f1=pg.evaluate("MossForest.feet"); check(abs(f1['x']-f0['x'])+abs(f1['y']-f0['y'])>20,'%s: tap-to-move moves the player (%d,%d)->(%d,%d)'%(name,f0['x'],f0['y'],f1['x'],f1['y']))
        check(pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"),'%s: no horizontal page scroll'%name)
        pg.screenshot(path='/tmp/mob_%s.png'%name)
        ctx.close()
    print('errors',errs[:5]); b.close()
sys.exit(1 if (fails or errs) else 0)
