"""Fiona idle v3 (approved 2026-10-21): MASTER-derived blink + 4 s breathing in the layered idle renderer.
Asset identity (SHA-256 of the approved files), MASTER untouched, overlays confined to the eyes, blink order/timing/gap, breath period,
attack hand-off, reduced motion, normal + raider battles. FIONA_LOOP_SECONDS=320 adds the long-loop soak (position drift = transform identity, errors, image failures)."""
import os,sys,hashlib,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail)
    if not ok:fails.append(name)
D=ROOT/'img/battle/characters/fiona/idle_v3'
SHA={'fiona_idle_master.png':'1a47fc29adf6fe2263110dc48f99e537a00daae2bf5c1b6fcd7fae7d23d076aa',
'eyes/overlay_L_s1.png':'eed876d6067865861b033fb91c86afc61b8de5db1c68632f5e61d9fa1a04053a','eyes/overlay_L_s2.png':'9cfa55ef07ddc34c3a5fdd872e16cb430a671fb27328bd80e8d00de3a3de5610',
'eyes/overlay_L_s3.png':'69ad1e3342153ae886f40b07c5b24caf3bc14ad064fad2b77c08fcb588861169','eyes/overlay_L_s4.png':'cf65ab2a1031aa74a5c22f03b591764d052c2c4a93ba3727eeb5cba52209e5c6',
'eyes/overlay_R_s1.png':'a84ebe45d3f87d2d8cb97af75a3ae39a5c958e2d098647a0d2cca2135daca202','eyes/overlay_R_s2.png':'75bbdc26027c4b18cea00a5f90111ded7276bcdfcc971e74c94704edfabcd3b3',
'eyes/overlay_R_s3.png':'59e9e4e25266fcfa949854b28590fdef58db0a5c5b6f98b5121ed400207ab7fc','eyes/overlay_R_s4.png':'f01e277f3e7033135edd0b0451336764427cc7558d08d7e8e5286ff6eb4c98d5'}
for f,h in SHA.items():check(hashlib.sha256((D/f).read_bytes()).hexdigest()==h,'asset identical to approved v3: '+f)
check(not (ROOT/'img/battle/characters/fiona/idle').exists(),'old 6-frame Fiona idle removed')
m=Image.open(D/'fiona_idle_master.png');check(m.size==(1024,1536) and m.mode=='RGBA','MASTER 1024x1536 RGBA',(m.size,m.mode))
BOX={'L':(458,251,512,296),'R':(511,223,577,269)}
for e,b in BOX.items():
    for i in range(1,5):
        o=Image.open(D/('eyes/overlay_%s_s%d.png'%(e,i)));check(o.size==(b[2]-b[0],b[3]-b[1]) and o.mode=='RGBA','overlay %s s%d matches its box'%(e,i),o.size)
js=(ROOT/'js/assets.js').read_text()
check('cycle:4, amp:0.35' in js and '[[1,30],[2,30],[3,35],[4,70],[3,35],[2,30],[1,30]]' in js and 'minGap:3000, maxGap:6000' in js,'assets.js: 4 s breath, 35% strength, blink sequence and 3-6 s gap as approved')
LOOP=float(os.getenv('FIONA_LOOP_SECONDS','0'))
JS_FRAME="""async()=>{const mp=await (async()=>{const i=new Image();i.src='img/battle/characters/fiona/idle_v3/fiona_idle_master.png';await i.decode();const c=document.createElement('canvas');c.width=1024;c.height=1536;const x=c.getContext('2d');x.drawImage(i,0,0);return x.getImageData(0,0,1024,1536).data})();
 const BOX={L:[458,251,512,296],R:[511,223,577,269]},out={},prev={};
 for(let s=0;s<=4;s++){const c=BattleIdleMotion.layeredFrame('fiona',s);const d=c.getContext('2d').getImageData(0,0,1024,1536).data;let outside=0,changed=0,alphaMax=0,vsPrev=0;
  for(let y=0;y<1536;y++)for(let x=0;x<1024;x++){const k=(y*1024+x)*4;const da=Math.abs(d[k+3]-mp[k+3]);if(da>alphaMax)alphaMax=da;
   const rgb=Math.max(Math.abs(d[k]-mp[k]),Math.abs(d[k+1]-mp[k+1]),Math.abs(d[k+2]-mp[k+2]));const exact=rgb===0&&da===0;
   let inb=false;for(const b of Object.values(BOX))if(x>=b[0]&&x<b[2]&&y>=b[1]&&y<b[3])inb=true;
   if(!inb&&!exact)outside++;if(inb&&rgb>8)changed++;if(s>0&&prev.d){const k2=k;if(Math.max(Math.abs(d[k2]-prev.d[k2]),Math.abs(d[k2+1]-prev.d[k2+1]),Math.abs(d[k2+2]-prev.d[k2+2]))>8)vsPrev++}}
  prev.d=d;out[s]={outside,changed,alphaMax,vsPrev}}return out}"""
JS_OBS="""async(ms)=>{const rec=[];let t0=performance.now(),last=null,lastPh=null,wraps=[];await new Promise(res=>{const tick=t=>{const a=BattleIdleMotion.status.actors.find(q=>q.actor==='fiona'&&q.showing);if(a&&a.layer){const L=a.layer;if(last!==L.eye){rec.push([Math.round(t-t0),L.eye]);last=L.eye}
 if(lastPh!==null&&L.phase<lastPh-0.5)wraps.push(Math.round(t-t0));lastPh=L.phase}
 if(t-t0<ms)requestAnimationFrame(tick);else res()};requestAnimationFrame(tick)});return {rec,wraps}}"""
def blinks(rec):
    out=[];i=0
    while i<len(rec):
        if rec[i][1]==1:
            seq=[rec[i][1]];j=i+1
            while j<len(rec) and rec[j][1]!=0:seq.append(rec[j][1]);j+=1
            if j<len(rec):out.append((rec[i][0],rec[j][0],seq))
            i=j
        else:i+=1
    return out
with server(8817) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    ctx=b.new_context(viewport={'width':1280,'height':720});pg=ctx.new_page();errs=[];bad=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('response',lambda r:bad.append(r.url) if r.status>=400 else None);pg.on('requestfailed',lambda r:bad.append(r.url) if 'ABORTED' not in str(r.failure) else None)   # aborted = request superseded by a scene switch
    pg.goto(base+'/index.html');pg.wait_for_function('window.BattleIdleMotion&&window.BattleActorState');pg.wait_for_timeout(1500);pg.evaluate("closeDialogue()");pg.wait_for_timeout(300)
    for name,start in (('raider','startRaiderBattle()'),('normal','document.body.classList.remove("soloRescue");startAttackBattle("attackGob1",100)')):
        pg.evaluate(start);pg.wait_for_timeout(1500);pg.wait_for_function("BattleIdleMotion.status.actors.some(q=>q.actor==='fiona'&&q.context===%r&&q.showing&&q.layer)"%name,timeout=20000);pg.evaluate("typeof closeDialogue==='function'&&closeDialogue()");pg.wait_for_function("!['battlePresentationBusy','dialogueOpen','actionCinematic'].some(c=>document.body.classList.contains(c))",timeout=20000);pg.wait_for_timeout(800)
        a=pg.evaluate("BattleIdleMotion.status.actors.find(q=>q.actor==='fiona'&&q.context===%r)"%name)
        check(a['showing'] and a['layer'] is not None,name+': Fiona v3 layered idle is running',a)
        if name=='raider':
            fr=pg.evaluate(JS_FRAME)
            check(fr['0']['outside']==0 and fr['0']['changed']==0 and fr['0']['alphaMax']==0,'open eyes (state 0) composite == MASTER pixel-exact',fr['0'])
            for s in '1234':check(fr[s]['outside']==0 and fr[s]['alphaMax']<=3 and fr[s]['changed']>200 and fr[s]['vsPrev']>50,'blink state %s: only the eye regions change (outside==0, alpha within 3 LSB of canvas premultiply rounding), differs from the previous state'%s,fr[s])
        obs=pg.evaluate(JS_OBS,14000);bl=blinks(obs['rec'])
        check(len(bl)>=1,name+': at least one blink in 14 s',[(x[0],x[1]) for x in bl])
        ok_order=lambda q:q[0]<=2 and q[-1]<=2 and 4 in q and q[:q.index(4)+1]==sorted(q[:q.index(4)+1]) and q[q.index(4):]==sorted(q[q.index(4):],reverse=True)   # rAF sampling may skip a 30 ms state
        check(all(ok_order(x[2]) for x in bl),name+': frame order open>1..4>..1>open (up then down)',[x[2] for x in bl])
        check(all(200<=x[1]-x[0]<=420 for x in bl),name+': blink duration ~260 ms',[x[1]-x[0] for x in bl])
        st=[x[0] for x in bl];gaps=[st[i+1]-st[i] for i in range(len(st)-1)]
        check(all(2900<=g<=6100 for g in gaps),name+': blink gap 3-6 s, never consecutive',gaps)
        w=obs['wraps'];per=[w[i+1]-w[i] for i in range(len(w)-1)]
        check(len(per)>=2 and all(3900<=x<=4150 for x in per),name+': breathing period 4 s',per)
        # hand-off: an attack hides the idle canvas, idle resumes from the rest pose
        pg.evaluate("BattleActorState.set('fiona','attack',{battle:%r,duration:500})"%name);pg.wait_for_timeout(120)
        mid=pg.evaluate("BattleIdleMotion.status.actors.find(q=>q.actor==='fiona'&&q.context===%r).showing"%name);pg.wait_for_timeout(1500)
        back=pg.evaluate("(()=>{const a=BattleIdleMotion.status.actors.find(q=>q.actor==='fiona'&&q.context===%r);return [a.showing,a.layer]})()"%name)
        check(mid is False and back[0] is True,name+': attack hides idle, idle resumes',(mid,back))
    # long loop soak (raider battle): errors / failed images / blink stream
    if LOOP>0:
        pg.evaluate("startRaiderBattle()");pg.wait_for_timeout(2500);obs=pg.evaluate(JS_OBS,int(LOOP*1000));bl=blinks(obs['rec'])
        check(len(bl)>=int(LOOP/6)-1 and all(4 in x[2] and x[2][0]<=2 and x[2][-1]<=2 for x in bl),'soak %ds: blinks keep the approved order (%d blinks)'%(LOOP,len(bl)))
        per=[obs['wraps'][i+1]-obs['wraps'][i] for i in range(len(obs['wraps'])-1)];check(max(per)<=4150 and min(per)>=3900,'soak: breath period stable',(min(per),max(per)))
    check(not errs,'no page errors',errs[:3]);check(not bad,'no image/asset load failures',bad[:3])
    # reduced motion: rest pose only (open eyes, no breathing)
    c2=b.new_context(viewport={'width':1280,'height':720},reduced_motion='reduce');p2=c2.new_page();p2.goto(base+'/index.html');p2.wait_for_function('window.BattleIdleMotion&&window.BattleActorState');p2.wait_for_timeout(1500);p2.evaluate("closeDialogue()");p2.evaluate("startRaiderBattle()");p2.wait_for_timeout(2500)
    o=p2.evaluate(JS_OBS,5000);check(all(e==0 for _,e in o['rec']) and not o['wraps'],'reduced motion: open eyes, no blink, no breathing',o['rec'][:3])
    b.close()
print('FAILS',fails);sys.exit(1 if fails else 0)
