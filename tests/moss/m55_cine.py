# M5.5 cinematic camera: seal-open shake + sanctuary pan; camera scale untouched. needs http.server 8765
import sys, json
from playwright.sync_api import sync_playwright
URL='http://localhost:8765/index.html'; errs=[]; fails=[]
def check(c,msg):
    print(('ok   ' if c else 'FAIL ')+msg)
    if not c: fails.append(msg)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto(URL); pg.wait_for_timeout(1000)
    pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(600)
    pg.evaluate("PrologueProgress.seed(2,[]);MossForestStory.enterAt('moss_forest_03_ancient_grove',3900,3330,{opened:[],fired:[]})"); pg.wait_for_function("MossForest.active&&MossForest.mapId.includes('03')",timeout=20000); pg.wait_for_timeout(800); pg.evaluate("closeDialogue()")
    scale0=pg.evaluate("FieldCamera.scale")
    # seal opening: simulate the 3rd defeat flipping the flag
    pg.evaluate("window.__tf=[];(()=>{const w=document.querySelector('#forestWorld');const f=()=>{__tf.push(w.style.transform);requestAnimationFrame(f)};f()})()")
    pg.evaluate("PrologueProgress.seed(3,[]);MossForestStory.syncFlags()"); pg.wait_for_timeout(1300)
    tf=pg.evaluate("__tf"); shaken=[t for t in tf if t.startswith('translate(') and t.count('translate(')>=2]
    check(len(shaken)>10,'seal opening shakes the camera (%d shaken frames)'%len(shaken))
    pg.wait_for_timeout(300); pg.evaluate("__tf.length=0"); pg.wait_for_timeout(200)
    check(all(t.count('translate(')==1 for t in pg.evaluate("__tf")),'shake settles')
    # sanctuary pan
    pg.evaluate("MossForest.teleportFeet(4050,3280)"); pg.wait_for_timeout(100)
    pg.evaluate("MossForest.teleportFeet(4060,3200)"); pg.wait_for_timeout(400)
    check(pg.evaluate("MossForest.busy"),'pan locks input while it plays')
    f0=pg.evaluate("MossForest.feet"); pg.wait_for_timeout(1100)
    wt=pg.evaluate("document.querySelector('#forestWorld').style.transform")
    pg.wait_for_function("MossForest.busy===false",timeout=8000); pg.wait_for_timeout(300)
    f1=pg.evaluate("MossForest.feet"); check(abs(f1['x']-f0['x'])<1 and abs(f1['y']-f0['y'])<1,'player did not move during pan')
    check(pg.evaluate("MossForest.active"),'control returned after pan')
    check(pg.evaluate("FieldCamera.scale")==scale0,'camera scale unchanged (%s)'%scale0)
    # fires only once
    pg.evaluate("MossForest.teleportFeet(4500,3400)"); pg.wait_for_timeout(300); pg.evaluate("MossForest.teleportFeet(4060,3200)"); pg.wait_for_timeout(400)
    check(not pg.evaluate("MossForest.busy"),'pan is once-only')
    b.close()
check(not errs,'0 console errors %s'%errs[:2])
sys.exit(1 if fails else 0)
