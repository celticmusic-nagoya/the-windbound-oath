# Walking speed must not depend on the frame rate. Compares normal vs uncapped (high-Hz) frame pacing in forest and village.
import sys
from playwright.sync_api import sync_playwright
fails=[]
def run(args):
    out={}
    with sync_playwright() as p:
        b=p.chromium.launch(args=args); pg=b.new_page(viewport={'width':1280,'height':720}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
        # village: click-to-move 3 s along the open road
        pg.evaluate("devJump('training')"); pg.wait_for_timeout(500)
        out['fps_v']=pg.evaluate("new Promise(r=>{let n=0;const t0=performance.now();const f=()=>{n++;performance.now()-t0<1000?requestAnimationFrame(f):r(n)};requestAnimationFrame(f)})")
        pg.evaluate("""(()=>{for(let y=200;y<1800;y+=20)for(let x=600;x<2400;x+=20){let ok=true;for(let d=0;d<=340&&ok;d+=10)if(blockedWorld(x-d,y))ok=false;if(ok){px=x;py=y;target=null;return}}})()"""); pg.wait_for_timeout(200)
        x0=pg.evaluate("px"); pg.evaluate("target=FieldNavigation.destination(px-300,py,blockedWorld)"); pg.wait_for_timeout(1000)
        out['village']=abs(pg.evaluate("px")-x0)
        # forest
        pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(800); pg.evaluate("closeDialogue()")
        f0=pg.evaluate("MossForest.feet"); pg.evaluate("MossForest.goFeet(%d,%d)"%(f0['x']+2000,f0['y']-200)); pg.wait_for_timeout(2000)
        f1=pg.evaluate("MossForest.feet"); out['forest']=((f1['x']-f0['x'])**2+(f1['y']-f0['y'])**2)**.5/2
        out['fps_f']=pg.evaluate("new Promise(r=>{let n=0;const t0=performance.now();const f=()=>{n++;performance.now()-t0<1000?requestAnimationFrame(f):r(n)};requestAnimationFrame(f)})")
        b.close()
    return out
a=run([]); b=run(['--disable-frame-rate-limit','--disable-gpu-vsync'])
print('default ',a); print('uncapped',b)
vr=b['village']/max(a['village'],1); print('village ratio %.2f'%vr)
assert 0.85<=vr<=1.15 and a['village']>200, 'village speed'
ratio=b['forest']/a['forest']; print('forest speed ratio uncapped/default = %.2f (fps %s vs %s)'%(ratio,b['fps_f'],a['fps_f']))
ok=0.85<=ratio<=1.15 and abs(a['forest']-300)<45
print('ok   ' if ok else 'FAIL ','forest px/s %.0f (default) vs %.0f (uncapped)'%(a['forest'],b['forest']))
sys.exit(0 if ok else 1)
