"""Fiona idle v3 - strict timeline + reduced-motion tests (Codex QA FIV3-01 / FIV3-02).
 1. controlled-clock probe of the REAL pose function against the approved spec (every boundary +-0.01 ms, plus a sweep);
 2. real-browser trace of every actual draw (clock, blink start, state, overlays actually drawn L/R, breath) vs the approved spec, per draw;
 3. reduced-motion toggled mid-animation (open/half/closed eye, inhale/exhale, rapid toggling, resume);
 4. negative controls: deliberately broken renderers/assets (skipped states 2/3, wrong duration, one eye off, wrong gap, wrong breath cycle, reduced-motion fix reverted)
    must be detected by exactly these checks.
The approved spec lives in tools/qa/fiona_v3_trace.py, independent of js/assets.js. No tolerance is widened: states are compared draw by draw at each draw's own clock value.
Env: FIONA_TRACE_SECONDS (default 14), FIONA_MUTANTS=0 to skip negative controls."""
import os,sys,time,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
import fiona_v3_trace as S
from playwright.sync_api import sync_playwright
SECS=float(os.getenv('FIONA_TRACE_SECONDS','14'));MUT=os.getenv('FIONA_MUTANTS','1')!='0'
fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail if detail!='' else '')
    if not ok:fails.append(name)
START={'raider':'startRaiderBattle()','normal':'document.body.classList.remove("soloRescue");startAttackBattle("attackGob1",100)'}
SEL={'raider':'#rbFiona','normal':'#bFiona2'}
ACT="BattleIdleMotion.status.actors.find(q=>q.actor==='fiona'&&q.context===%r)"
def begin(pg,name):
    pg.evaluate("document.body.classList.remove('dialogueOpen')")
    pg.evaluate(START[name]);pg.wait_for_timeout(1500)
    pg.wait_for_function("BattleIdleMotion.status.actors.some(q=>q.actor==='fiona'&&q.context===%r&&q.showing&&q.layer)"%name,timeout=30000)
    pg.evaluate("typeof closeDialogue==='function'&&closeDialogue()")
    pg.wait_for_function("!['battlePresentationBusy','dialogueOpen','actionCinematic'].some(c=>document.body.classList.contains(c))",timeout=30000);pg.wait_for_timeout(800)
def probe(pg,label):
    cases=S.probe_cases()
    # blink start 0, controlled clock t = ms/1000 (cases are (ms_since_start, expected)); the sweep entries use start k+0.5 s offsets via the same helper
    req=[[0.0,ms/1000] for ms,_ in cases]
    got=pg.evaluate("c=>c.map(([s,t])=>BattleIdleMotion.probeLayered('fiona',s,t).state)",req)
    bad=[(cases[i][0],cases[i][1],got[i]) for i in range(len(cases)) if got[i]!=cases[i][1]]
    check(not bad,label+': controlled clock - every approved boundary (+-0.01 ms) and sweep gives the approved state (%d cases)'%len(cases),bad[:3])
    br=pg.evaluate("[0,1,2,3.5].map(t=>{const r=BattleIdleMotion.probeLayered('fiona',-1e9,t);return [r.ph,r.wave]})")
    ok=all(abs(br[i][0]-S.spec_wave(t)[0])<1e-12 and abs(br[i][1]-S.spec_wave(t)[1])<1e-12 for i,t in enumerate([0,1,2,3.5]))
    check(ok,label+': controlled clock - breath is the approved 4 s cos cycle',br)
def trace(pg,name,secs,label):
    pg.evaluate("BattleIdleMotion.traceStart()");pg.wait_for_timeout(int(secs*1000));tr=pg.evaluate("BattleIdleMotion.traceStop()")
    f,m=S.analyze(tr,name)
    check(not f and m['draws']>50 and m['blinks']>=1,'%s %s: every real draw conforms to the approved spec (state, L/R overlays, breath, clock)'%(label,name),(f,m))
    return m
def pix(pg,name):return pg.evaluate("n=>{const c=document.querySelector(n+' canvas.battle-idle-canvas');return c?c.toDataURL():null}",SEL[name])
def layer(pg,name):return pg.evaluate("n=>{const q=BattleIdleMotion.status.actors.find(q=>q.actor==='fiona'&&q.context===n);return {eye:q.layer.eye,ph:q.layer.phase,wave:q.layer.wave,showing:q.showing,rm:BattleIdleMotion.status.reducedMotion}}",name)
FREEZE="""([ctxn,cond])=>new Promise(res=>{const ok=eval('(L)=>'+cond);const f=()=>{const q=BattleIdleMotion.status.actors.find(q=>q.actor==='fiona'&&q.context===ctxn);
 if(q&&q.showing&&q.layer&&ok({eye:q.layer.eye,ph:q.layer.phase,wave:q.layer.wave})){document.body.classList.add('dialogueOpen');res({eye:q.layer.eye,ph:q.layer.phase,wave:q.layer.wave})}else requestAnimationFrame(f)};requestAnimationFrame(f)})"""
def reduced(pg,name,label):
    # cold reduced reference
    pg.emulate_media(reduced_motion='reduce');pg.wait_for_timeout(250);begin(pg,name);pg.wait_for_timeout(500)
    ref=pix(pg,name);l=layer(pg,name);check(l['eye']==0 and l['ph']==0 and l['wave']==0 and ref,'%s %s: cold start with reduced motion = rest pose'%(label,name),l)
    pg.emulate_media(reduced_motion='no-preference');pg.wait_for_timeout(300)
    scen=[('open+inhale','L.eye===0&&L.ph>0.15&&L.ph<0.45'),('open+exhale','L.eye===0&&L.ph>0.6&&L.ph<0.9'),('half-closed','L.eye===1||L.eye===2'),('closed','L.eye===3||L.eye===4')]
    for tag,cond in scen:
        pg.evaluate("document.body.classList.remove('dialogueOpen')");pg.wait_for_timeout(300)
        pre=pg.evaluate(FREEZE,[name,cond]);pg.wait_for_timeout(150);frozen=pix(pg,name)
        pg.emulate_media(reduced_motion='reduce');pg.wait_for_timeout(250);l=layer(pg,name);post=pix(pg,name)
        check(l['rm'] and l['eye']==0 and l['ph']==0 and l['wave']==0 and post==ref,'%s %s %s (eye %d, wave %.2f): reduced ON mid-animation -> MASTER rest pose, no residue (canvas == cold reduced)'%(label,name,tag,pre['eye'],pre['wave']),(l,post==ref,frozen==post))
        pg.evaluate("document.body.classList.remove('dialogueOpen')");pg.wait_for_timeout(400);l2=layer(pg,name);still=pix(pg,name)
        check(l2['eye']==0 and l2['ph']==0 and still==ref,'%s %s %s: stays still while reduced (no blink, no breath)'%(label,name,tag),l2)
        pg.emulate_media(reduced_motion='no-preference');pg.wait_for_timeout(700);l3=layer(pg,name);moved=pix(pg,name)
        check(not l3['rm'] and l3['ph']>0 and moved!=ref,'%s %s %s: reduced OFF -> breathing resumes from the rest pose'%(label,name,tag),l3)
    # live toggle without any pause (what the user does in OS settings)
    for i in range(3):
        pg.wait_for_timeout(1700+i*500);pg.emulate_media(reduced_motion='reduce');pg.wait_for_timeout(200);l=layer(pg,name)
        check(l['eye']==0 and l['ph']==0 and pix(pg,name)==ref,'%s %s live toggle %d: rest pose'%(label,name,i),l);pg.emulate_media(reduced_motion='no-preference');pg.wait_for_timeout(100)
    # rapid switching
    for i in range(8):
        pg.emulate_media(reduced_motion='reduce' if i%2==0 else 'no-preference');pg.wait_for_timeout(15+7*i)
    pg.emulate_media(reduced_motion='reduce');pg.wait_for_timeout(300);l=layer(pg,name)
    check(l['rm'] and l['eye']==0 and l['ph']==0 and pix(pg,name)==ref,'%s %s rapid switching ending ON: consistent rest pose'%(label,name),l)
    pg.emulate_media(reduced_motion='no-preference');pg.wait_for_timeout(900);l=layer(pg,name);a=pix(pg,name);pg.wait_for_timeout(500)
    check(not l['rm'] and l['ph']>0 and pix(pg,name)!=a,'%s %s after rapid switching ending OFF: running normally'%(label,name),l)
    # blink resumes after OFF
    pg.evaluate("BattleIdleMotion.traceStart()");pg.wait_for_timeout(8000);tr=pg.evaluate("BattleIdleMotion.traceStop()");f,m=S.analyze(tr,name)
    check(not f and m['blinks']>=1,'%s %s: blink resumes and conforms after reduced OFF'%(label,name),(f,m))
def suite(pg,label,do_reduced=True,full=True):
    probe(pg,label)
    for name in ('raider','normal'):
        begin(pg,name);trace(pg,name,SECS if full else 9,label)
        if do_reduced:reduced(pg,name,label)
def newpage(b,base,patch=None):
    ctx=b.new_context(viewport={'width':1280,'height':720});pg=ctx.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    if patch:
        def h(route):
            url=route.request.url.split('?')[0].split('/')[-1]
            if url in patch:
                r=route.fetch();t=r.text()
                for a,c in patch[url]:
                    assert a in t,'mutant anchor missing: '+a
                    t=t.replace(a,c)
                route.fulfill(response=r,body=t)
            else:route.continue_()
        pg.route(re.compile(r'/js/[^/?]+\.js(\?.*)?$'),h)
    pg.goto(base+'/index.html',wait_until='domcontentloaded',timeout=120000);pg.wait_for_function('window.BattleIdleMotion&&window.BattleActorState',timeout=120000);pg.wait_for_timeout(1500);pg.evaluate("closeDialogue()");pg.wait_for_timeout(300)
    return ctx,pg,errs
SEQ_OK='[[1,30],[2,30],[3,35],[4,70],[3,35],[2,30],[1,30]]'
MUTANTS=[
 ('skip states 2/3 (renderer)',{'battle-idle-motion.js':[('if(ms<d){state=st;break;}','if(ms<d){state=(st===2||st===3)?1:st;break;}')]},'blink'),
 ('skip states 2/3 (assets, same total time)',{'assets.js':[(SEQ_OK,'[[1,30],[1,30],[1,35],[4,70],[1,35],[1,30],[1,30]]')]},'blink'),
 ('wrong duration of state 4 (70->40 ms)',{'assets.js':[(SEQ_OK,'[[1,30],[2,30],[3,35],[4,40],[3,35],[2,30],[1,30]]')]},'blink'),
 ('one eye off (R uses the previous state)',{'battle-idle-motion.js':[('const si=state-1;','const si=id===\'R\'?Math.max(0,state-2):state-1;')]},'blink'),
 ('blink gap 1-2 s',{'assets.js':[('minGap:3000, maxGap:6000','minGap:1000, maxGap:2000')]},'blink'),
 ('breath cycle 3 s',{'assets.js':[('cycle:4, amp:0.35','cycle:3, amp:0.35')]},'blink'),
 ('reduced-motion fix reverted (FIV3-01)',{'battle-idle-motion.js':[('(r.frame!==0||(r.assets.layered&&!r.stillDone))','r.frame!==0')]},'reduced'),
]
with server(8818) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    if os.getenv('FIONA_ONLY_MUT')!='1':
        ctx,pg,errs=newpage(b,base);suite(pg,'real');check(not errs,'real: no page errors',errs[:3]);ctx.close()
    if MUT:
        for label,patch,kind in MUTANTS:
            if os.getenv('FIONA_MUT_FILTER') and os.getenv('FIONA_MUT_FILTER') not in label:continue
            before=len(fails);ctx2,pg2,e2=newpage(b,base,patch);keep=list(fails)
            try:
                if kind=='blink':
                    probe(pg2,'MUTANT');begin(pg2,'raider');trace(pg2,'raider',9,'MUTANT')
                else:
                    begin(pg2,'raider');reduced_only=reduced(pg2,'raider','MUTANT')
            except Exception as ex:print('mutant run stopped by',type(ex).__name__,str(ex)[:120],'page errors:',e2[:3])
            new=fails[len(keep):];del fails[len(keep):]   # failures inside a mutant run are the EXPECTED outcome, not a failure of this suite
            check(len(new)>0,'negative control detected: '+label,[n[:90] for n in new[:2]]);ctx2.close()
    b.close()
print('FAILS',fails);sys.exit(1 if fails else 0)
