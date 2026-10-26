# Walking speed must not depend on frame rate. Forest velocity uses the delivered simulation time: FieldMovement intentionally caps a stalled frame to 50ms. Raw wall time/distances remain diagnostic evidence.
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
        # Measure before arrival: reaching a 300 px destination after 1 s would
        # also pass if an uncapped browser moved much too quickly.
        x0=pg.evaluate("px"); pg.evaluate("target=FieldNavigation.destination(px-300,py,blockedWorld)"); pg.wait_for_timeout(500)
        out['village']=abs(pg.evaluate("px")-x0)
        # forest
        pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active&&!MossForest.busy",timeout=60000); pg.wait_for_timeout(800); pg.evaluate("closeDialogue()")
        # Observe the actual public clock consumed by the runtime, without setting or mocking it.
        pg.evaluate("""()=>{window.qaHz={};qaHz.start=()=>{qaHz.sample={scale:0,frames:0,maxGap:0,start:performance.now()};let last=performance.now();const tick=t=>{qaHz.sample.scale+=FieldMovement.frameScale;qaHz.sample.frames++;qaHz.sample.maxGap=Math.max(qaHz.sample.maxGap,t-last);last=t;qaHz.raf=requestAnimationFrame(tick)};qaHz.raf=requestAnimationFrame(tick)};qaHz.stop=()=>{cancelAnimationFrame(qaHz.raf);return {...qaHz.sample,end:performance.now()}};}""")
        f0=pg.evaluate("MossForest.feet"); pg.evaluate("MossForest.goFeet(%d,%d);qaHz.start()"%(f0['x']+2000,f0['y']-200)); pg.wait_for_timeout(2000)
        clock=pg.evaluate("()=>({...qaHz.stop(),feet:MossForest.feet})"); f1=clock['feet']; distance=((f1['x']-f0['x'])**2+(f1['y']-f0['y'])**2)**.5
        assert clock['frames']>0 and clock['scale']>0,'No actual forest clock samples'
        out['forest_wall_px_s']=distance/((clock['end']-clock['start'])/1000);out['forest_clock']=clock;out['forest']=distance/(clock['scale']/60)
        # Held keyboard uses the same dt-normalised runtime as pointer movement.
        corridor=pg.evaluate("""(()=>{
          const map=MossForest.map,zones=[...map.eventZones,...map.transitions];
          for(let y=600;y<map.world.height-600;y+=40)for(let x=600;x<map.world.width-1000;x+=40){
            let clear=true;
            for(let d=0;d<=380&&clear;d+=5){
              if(MossForest.blocked(x+d,y))clear=false;
              for(const zone of zones){const r=zone.shape||zone.rect;
                if(r&&x+d>=r.x-100&&x+d<=r.x+r.w+100&&y>=r.y-100&&y<=r.y+r.h+100)clear=false;
              }
            }
            if(clear)return [x,y];
          }
          return null;
        })()""")
        assert corridor, 'No clear keyboard test corridor'
        pg.evaluate("([x,y])=>{MossForest.teleportFeet(x,y);closeDialogue()}",corridor)
        k0=pg.evaluate("MossForest.feet")
        pg.evaluate("""()=>{window.qaHzDown=e=>{if(e.key==='ArrowRight')qaHz.start()};window.qaHzUp=e=>{if(e.key==='ArrowRight')qaHz.keyClock=qaHz.stop()};addEventListener('keydown',qaHzDown,true);addEventListener('keyup',qaHzUp,true)}""")
        pg.keyboard.down('ArrowRight'); pg.wait_for_timeout(1000); pg.keyboard.up('ArrowRight')
        k1=pg.evaluate("MossForest.feet")
        clock=pg.evaluate("()=>{removeEventListener('keydown',qaHzDown,true);removeEventListener('keyup',qaHzUp,true);return qaHz.keyClock}")
        distance=((k1['x']-k0['x'])**2+(k1['y']-k0['y'])**2)**.5
        assert clock and clock['frames']>0 and clock['scale']>0,'No actual keyboard clock samples'
        out['keyboard_raw_distance']=distance;out['keyboard_wall_px_s']=distance/((clock['end']-clock['start'])/1000);out['keyboard_clock']=clock;out['keyboard']=distance/(clock['scale']/60)
        out['fps_f']=pg.evaluate("new Promise(r=>{let n=0;const t0=performance.now();const f=()=>{n++;performance.now()-t0<1000?requestAnimationFrame(f):r(n)};requestAnimationFrame(f)})")
        assert not errs, 'JavaScript exceptions: %s' % errs
        b.close()
    return out
a=run([]); b=run(['--disable-frame-rate-limit','--disable-gpu-vsync'])
print('default ',a); print('uncapped',b)
vr=b['village']/max(a['village'],1); print('village ratio %.2f'%vr)
assert 0.85<=vr<=1.15 and abs(a['village']-150)<30, 'village speed'
ratio=b['forest']/a['forest']; print('forest speed ratio uncapped/default = %.2f (fps %s vs %s)'%(ratio,b['fps_f'],a['fps_f']))
kr=b['keyboard']/max(a['keyboard'],1)
print('keyboard simulated-time velocity ratio %.2f, px/s %s / %s'%(kr,a['keyboard'],b['keyboard']))
ok=0.85<=ratio<=1.15 and abs(a['forest']-300)<45 and 0.85<=kr<=1.15 and a['keyboard']>200
print('ok   ' if ok else 'FAIL ','forest px/s %.0f (default) vs %.0f (uncapped)'%(a['forest'],b['forest']))
sys.exit(0 if ok else 1)
