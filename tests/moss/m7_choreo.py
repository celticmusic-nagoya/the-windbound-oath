# FieldChoreo: two temporary rectangles approach over a fixed time (walk -> idle poses), blocked clamp, then a conversation continues;
# also MossForest.actor adapters + the 'approach' scene step in the cliff map. needs http.server 8765
import math
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    # ---- temporary rectangles
    ev("""window.mk=(x,y)=>{const d=document.createElement('div');d.style.cssText='position:fixed;width:20px;height:30px;background:#c33;left:0;top:0;z-index:9999';document.body.appendChild(d);
      const o={log:[],x,y,get:()=>({x:o.x,y:o.y}),set(a,b){o.x=a;o.y=b;d.style.transform=`translate(${a}px,${b}px)`},pose(s,dir){o.log.push(s+':'+dir)}};o.set(x,y);return o};
      window.A=mk(100,300);window.B=mk(700,300);""")
    r=ev("""(async()=>{const t0=performance.now();const ok=await FieldChoreo.approach(A,B,{ms:800,gap:60});return {ok,dt:performance.now()-t0,ax:A.x,bx:B.x,ay:A.y,by:B.y,la:A.log,lb:B.log}})()""")
    check(r['ok'] and 780<=r['dt']<=1000,'approach finishes in the requested time (%.0f ms)'%r['dt'])
    check(abs(abs(r['bx']-r['ax'])-60)<=2,'feet end %.1f px apart (gap 60)'%abs(r['bx']-r['ax']))
    check(abs((r['ax']-100)-(700-r['bx']))<=2,'share .5: both cover the same distance')
    check(r['la'][0]=='walk:right' and r['la'][-1]=='idle:right' and r['lb'][0]=='walk:left' and r['lb'][-1]=='idle:left','poses: walk while moving, idle facing each other on arrival %s'%r['la'])
    check(len(r['la'])==2,'pose only changes on state change (no per-frame spam)')
    # share=1: only a moves
    r=ev("""(async()=>{A.set(100,300);B.set(500,300);await FieldChoreo.approach(A,B,{ms:300,gap:50,share:1});return [A.x,B.x]})()""")
    check(abs(r[0]-450)<=2 and r[1]==500,'share 1: only the first actor moves')
    # moveTo with speed
    r=ev("""(async()=>{A.set(0,0);const t=performance.now();await FieldChoreo.moveTo(A,{x:200,y:0},{speed:400,face:'down'});return [performance.now()-t,A.log.slice(-1)[0]]})()""")
    check(450<=r[0]<=700 and r[1]=='idle:down','moveTo by speed (200px @400px/s ~500ms), ends facing the requested direction')
    # blocked clamp
    r=ev("""(async()=>{A.set(0,0);const ok=await FieldChoreo.moveTo(A,{x:400,y:0},{ms:400,blocked:(x)=>x>=150});return [ok,A.x]})()""")
    check(r[0]==False and 100<=r[1]<150,'blocked: stops at the last free point (x=%.0f) and reports false'%r[1])
    # cancel
    r=ev("""(async()=>{A.set(0,0);const pr=FieldChoreo.moveTo(A,{x:400,y:0},{ms:600});await new Promise(r=>setTimeout(r,150));FieldChoreo.cancelAll();return [await pr,A.x,A.log.slice(-1)[0]]})()""")
    check(r[0]==False and 0<r[1]<400 and r[2].startswith('idle'),'cancelAll stops the actors and returns them to idle')
    # approach, then conversation continues
    ev("PrologueProgress.seed(0);Quest.reset();FieldTalk.load(null)")
    r=ev("""(async()=>{A.set(100,300);B.set(700,300);await FieldChoreo.approach(A,B,{ms:500,gap:60});const done=new Promise(res=>addEventListener('field-talk-end',()=>res(true),{once:true}));
      const started=FieldTalk.talk('scene_cliff_sunset',{source:'scene'});return {started,active:FieldTalk.active,done:null}})()""")
    check(r['started'] and r['active'],'conversation starts right after the approach')
    n=0
    while ev("FieldTalk.active") and n<40: pg.click('#msg'); pg.wait_for_timeout(100); n+=1
    check(not ev("FieldTalk.active"),'conversation ran to its end (%d clicks)'%n)
    # ---- real game: cliff map, MossForest.actor adapters
    ev("storyStage=3;MossForest.reset()"); pg.evaluate("document.querySelector('#hillExit').click()"); pg.wait_for_timeout(1500)
    ev("MossForest.teleportFeet(2400,1500)"); pg.wait_for_timeout(300)
    d0=ev("(()=>{const a=MossForest.actor('aidan').get(),f=MossForest.actor('fiona').get();return Math.hypot(a.x-f.x,a.y-f.y)})()")
    r=ev("""(async()=>{const A=MossForest.actor('aidan'),F=MossForest.actor('fiona');F.set(F.get().x-60,F.get().y);
      const fa=F.get(),aa=A.get();const t=performance.now();
      const ok=await FieldChoreo.approach(A,F,{ms:900,gap:44,share:.3,blocked:MossForest.blocked});
      const a=A.get(),f=F.get();const pose=document.querySelector('#forestFiona').dataset.pose;
      return {ok,dt:performance.now()-t,d:Math.hypot(a.x-f.x,a.y-f.y),pose,dir:document.querySelector('#forestFiona').dataset.dir,moved:[a.x-aa.x,f.x-fa.x]}})()""")
    check(r['ok'] and 880<=r['dt']<=1100,'cliff: Aidan/Fiona approach in time (%.0f ms)'%r['dt'])
    check(abs(r['d']-44)<=2,'cliff: feet %.1f px apart (gap 44)'%r['d'])
    check(r['pose']=='idle','cliff: Fiona ends in idle pose (dir %s)'%r['dir'])
    pg.wait_for_timeout(600)
    f1=ev("MossForest.actor('fiona').get()")
    pg.wait_for_timeout(400); f2=ev("MossForest.actor('fiona').get()")
    check(abs(f1['x']-f2['x'])<.5,'fionaHold: Fiona stays where the scene put her (no follow easing)')
    ev("MossForest.actor('fiona').release()"); pg.wait_for_timeout(1500)
    ev("MossForest.goFeet(2400,1700)"); pg.wait_for_timeout(2500)
    a=ev("MossForest.actor('aidan').get()"); f=ev("MossForest.actor('fiona').get()")
    check(math.hypot(a['x']-f['x'],a['y']-f['y'])<90,'release(): Fiona follows Aidan again')
    # ---- 'approach' scene step end-to-end, with the talk afterwards (test scene only)
    ev("""window.__t={steps:[{lock:true},{approach:{a:'aidan',b:'fiona',ms:700,gap:46,share:.4}},{talk:'scene_cliff_sunset'},{follow:'fiona'},{release:{ms:10}}]}""")
    ev("MossForest.teleportFeet(2400,1500)"); pg.wait_for_timeout(300)
    ev("void FieldScene.play(__t)"); pg.wait_for_timeout(1100)
    check(ev("FieldTalk.active"),'scene step: approach completes, then the conversation opens')
    n=0
    while ev("FieldScene.running") and n<80:
        if ev("FieldTalk.active"): pg.click('#msg')
        pg.wait_for_timeout(120); n+=1
    check(not ev("FieldScene.running"),'scene finished')
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
import sys; sys.exit(1 if fails else 0)
