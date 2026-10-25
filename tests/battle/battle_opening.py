"""Battle-start opening (Aidan 'draw' + Fiona 'ready'): once per battle start, both contexts, lock safety, return to rest, attack/skill unaffected."""
import os,sys,json,math
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
# ---- assets
for actor,state,pref,size in (('aidan','draw','aidan_draw_','aidan'),('fiona','ready','fiona_ready_','fiona')):
    d=ROOT/('img/battle/characters/%s/motion'%actor);ims=[Image.open(d/('%s%02d.png'%(pref,i))).convert('RGBA') for i in range(1,7)]
    check(len({i.size for i in ims})==1,'%s: 6 frames share one canvas'%actor,ims[0].size)
    bots=[];edge=[]
    for im in ims:
        a=np.array(im)[...,3];ys,xs=np.where(a>16);bots.append(int(ys.max()));edge.append(bool(xs.min()<=0 or ys.min()<=0 or xs.max()>=im.width-1 or ys.max()>=im.height-1))
    check(max(bots)-min(bots)<=3,'%s: foot line unified'%actor,bots);check(not any(edge),'%s: nothing touches the canvas edge'%actor)
man=json.load(open(ROOT/'img/battle/motion-manifest.json'))['motions']
check(man['aidan']['draw']['frames']==6 and sum(man['aidan']['draw']['ms'])==600,'manifest aidan draw 6f/600ms');check(man['fiona']['ready']['frames']==6 and sum(man['fiona']['ready']['ms'])<=900,'manifest fiona ready 6f/<=900ms',sum(man['fiona']['ready']['ms']))
check(man['aidan']['attack']['frames']==6 and man['aidan']['skill']['frames']==7,'attack/skill manifests untouched')
OPENING_MS=max(sum(man[a][state]['ms']) if isinstance(man[a][state]['ms'],list) else man[a][state]['frames']*man[a][state]['ms'] for a,state in [('aidan','draw'),('fiona','ready')])
START={'normal':"startAttackBattle('attackGob1',100)",'raider':"startRaiderBattle();PrologueCombat.spawn&&0"}
IMG={'normal':{'aidan':'#bAidan2 img','fiona':'#bFiona2 img'},'raider':{'aidan':'#rbAidan img','fiona':'#rbFiona img'}}
JS_TRACE="""([ctx,sel])=>{window.__traceCleanup?.();const cleanup=[];window.__traceCleanup=()=>{cleanup.forEach(f=>f());clearInterval(window.__iv)};window.__tr={ev:[],seq:{aidan:[],fiona:[]},busy:[],start:null,end:null,rest:null,frameReady:false,longTasks:[]};const t0=performance.now();
 const ready=()=>!(BattlePresentation.busy||(ctx==='normal'?attackBattleBusy:rbBusy)||BattleTargetSelector.active);
 const onOpening=e=>{__tr.start=performance.now();__tr.ev.push({t:__tr.start-t0,d:e.detail})};addEventListener('battle-opening',onOpening);cleanup.push(()=>removeEventListener('battle-opening',onOpening));
 const lockObserver=new MutationObserver(()=>{if(__tr.start!==null&&__tr.end===null&&!document.body.classList.contains('battlePresentationBusy')){
   __tr.end=performance.now();__tr.rest=[BattleActorState.get(ctx),BattleActorState.get(ctx,'fiona')];
   requestAnimationFrame(()=>{__tr.frameReady=ready()});
 }});lockObserver.observe(document.body,{attributes:true,attributeFilter:['class']});cleanup.push(()=>lockObserver.disconnect());
 try{const longObserver=new PerformanceObserver(list=>{for(const e of list.getEntries())__tr.longTasks.push({start:e.startTime,duration:e.duration})});longObserver.observe({type:'longtask',buffered:false});cleanup.push(()=>longObserver.disconnect())}catch(e){}
 for(const a of ['aidan','fiona']){const im=document.querySelector(sel[a]);const imageObserver=new MutationObserver(()=>{const f=+im.dataset.motionFrame;const s=__tr.seq[a];if(f&&s[s.length-1]?.f!==f)s.push({f,t:performance.now()-t0,src:im.getAttribute('src')})});imageObserver.observe(im,{attributes:true,attributeFilter:['src','data-motion-frame']});cleanup.push(()=>imageObserver.disconnect())}
 window.__t0=t0;window.__iv=setInterval(()=>__tr.busy.push([performance.now()-t0,BattlePresentation.busy,document.body.classList.contains('battlePresentationBusy')]),30);return 1}"""

def lock_verdict(trace, expected, retry_used=False):
    # No polling samples enter the decision. Missing evidence never becomes PASS.
    start,end=trace.get('start'),trace.get('end')
    if type(start) not in (int,float) or type(end) not in (int,float) or not math.isfinite(start) or not math.isfinite(end) or end<start:
        return 'FAIL','missing/invalid direct timestamps'
    duration=end-start
    if duration<expected-2:
        return 'FAIL',f'early release {duration:.2f} < {expected-2:.2f}ms'
    if trace.get('rest')!=['idle','idle'] or trace.get('frameReady') is not True:
        return 'FAIL','not at rest / not accepting by the first frame after release'
    if duration>expected+600:
        evidence=any(t.get('duration',0)>=50 and t.get('start',end)+t.get('duration',0)>start and t.get('start',end)<end for t in trace.get('longTasks',[]))
        return ('RETRY' if evidence and not retry_used else 'FAIL'),f'late release {duration:.2f}ms; long-task evidence={evidence}'
    return 'PASS',f'direct lock {duration:.2f}ms (T={expected})'

if '--self-test' in sys.argv:
    # Classifier controls are unit evidence, distinct from the browser fault injections below.
    expected=OPENING_MS
    def sample(duration,**kw):return dict(start=100,end=100+duration,rest=['idle','idle'],frameReady=True,longTasks=[],**kw)
    cases=[('normal',sample(880),False,'PASS'),('lower inclusive',sample(878),False,'PASS'),('early 600',sample(600),False,'FAIL'),('late 5000',sample(5000),False,'FAIL'),('300ms workload within budget',sample(1180),False,'PASS'),('missing',{},False,'FAIL'),('no release',dict(start=0,end=None),False,'FAIL'),('NaN timestamp',dict(start=0,end=float('nan')),False,'FAIL')]
    slow=sample(1500);slow['longTasks']=[{'start':200,'duration':300}]
    cases.extend([('evidenced late retry',slow,False,'RETRY'),('late retry exhausted',slow,True,'FAIL')])
    for field,value in [('rest',['draw','idle']),('frameReady',False)]:
        row=sample(880);row[field]=value;cases.append((field,row,False,'FAIL'))
    for name,row,retry,want in cases:
        got=lock_verdict(row,expected,retry)[0];assert got==want,(name,got,want);print('PASS classifier',name)
    print('classifier unit checks only; browser controls NOT_RUN');sys.exit(0)

with server(8815) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    repeats=int(os.environ.get('OPENING_REPEATS','1'))
    if repeats<1:raise ValueError('OPENING_REPEATS must be positive')
    for vp in [(1280,720),(390,844),(844,390)]*repeats:
      for ctx in ('normal','raider'):
        pg=b.new_page(viewport={'width':vp[0],'height':vp[1]});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat');pg.wait_for_timeout(1800);pg.evaluate("closeDialogue()")
        pg.evaluate(JS_TRACE,[ctx,IMG[ctx]]);pg.evaluate("PrologueProgress&&PrologueProgress.seed&&PrologueProgress.seed(0)");pg.evaluate(START[ctx]);pg.wait_for_timeout(450)
        mid=pg.evaluate("[BattlePresentation.busy,BattleActorState.get(%r),BattleActorState.get(%r,'fiona')]"%(ctx,ctx))
        check(mid[0] is True and mid[1]=='draw' and mid[2]=='ready','%s %s: opening running, input locked at 450ms'%(vp,ctx),mid)
        pg.wait_for_timeout(1100);r=pg.evaluate("clearInterval(__iv)||({trace:__tr,ev:__tr.ev,seq:__tr.seq,busy:__tr.busy,a:BattleActorState.get(%r),f:BattleActorState.get(%r,'fiona'),again:BattleOpening.play(%r),busyNow:BattlePresentation.busy,srcF:document.querySelector(%r).getAttribute('src')})"%(ctx,ctx,ctx,IMG[ctx]['fiona']))
        check(len(r['ev'])==1 and set(r['ev'][0]['d']['actors'])=={'aidan','fiona'},'%s %s: exactly one opening event, both actors'%(vp,ctx),r['ev'])
        sa=[s['f'] for s in r['seq']['aidan']];sf=[s['f'] for s in r['seq']['fiona']]
        check(sa==[1,2,3,4,5,6] and sf==[1,2,3,4,5,6],'%s %s: both play frames 1..6 once, in order'%(vp,ctx),(sa,sf))
        lastA=r['seq']['aidan'][-1]['t']-r['seq']['aidan'][0]['t'];lastF=r['seq']['fiona'][-1]['t']-r['seq']['fiona'][0]['t']
        check(430<=lastA<=560 and 640<=lastF<=800,'%s %s: frame timing (aidan last frame ~480ms, fiona ~760ms)'%(vp,ctx),(lastA,lastF))
        expected=OPENING_MS
        verdict,detail=lock_verdict(r['trace'],expected)
        if verdict=='RETRY':
            # One fresh battle only for an evidenced long task, never for early release or missing data.
            pg.evaluate(JS_TRACE,[ctx,IMG[ctx]]);pg.evaluate(START[ctx]);pg.wait_for_timeout(expected+1600)
            retry_trace=pg.evaluate('clearInterval(__iv)||__tr');verdict,detail=lock_verdict(retry_trace,expected,True)
        check(verdict=='PASS' and not r['busyNow'],'%s %s: directly measured input lock'%(vp,ctx),detail)
        check(r['a']=='idle' and r['f']=='idle' and r['again'] is False and r['srcF'].split('/')[-1].startswith('fiona_battle_idle'),'%s %s: both back at rest (Aidan idle, Fiona still), no double play'%(vp,ctx),(r['a'],r['f'],r['again'],r['srcF']))
        idle=pg.evaluate("BattleIdleMotion.status.actors.some(a=>a.actor==='aidan'&&a.context===%r&&a.state==='idle')"%ctx);check(idle,'%s %s: Aidan idle motion resumes'%(vp,ctx))
        # attack / skill must not trigger an opening
        pg.evaluate("window.__n=0;addEventListener('battle-opening',()=>__n++);BattleActorState.set('aidan','attack',{battle:%r,duration:820});BattleActorState.set('fiona','skill',{battle:%r,duration:700})"%(ctx,ctx));pg.wait_for_timeout(1000)
        check(pg.evaluate("__n")==0,'%s %s: attack/skill never replay the opening'%(vp,ctx))
        check(not errs,'%s %s: no console errors'%(vp,ctx),errs[:2]);pg.close()
    # Measurement controls: actual game page, temporary hold override/workload, no source writes.
    expected=OPENING_MS
    for name,duration,workload,wanted in [('early600',600,0,'FAIL'),('late5000',5000,0,'FAIL'),('workload300',None,300,'PASS')]:
        pg=b.new_page(viewport={'width':1280,'height':720});pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat');pg.wait_for_timeout(1800);pg.evaluate('closeDialogue()')
        pg.evaluate(JS_TRACE,['normal',IMG['normal']])
        if duration is not None:
            pg.evaluate("ms=>{const original=BattlePresentation;window.BattlePresentation={...original,get busy(){return original.busy},hold:(_ms,token)=>original.hold(ms,token)}}",duration)
        pg.evaluate(START['normal']+";"+("{const until=performance.now()+300;while(performance.now()<until){}}" if workload else ''))
        pg.wait_for_timeout((duration or expected)+1700)
        trace=pg.evaluate('clearInterval(__iv)||__tr');verdict,detail=lock_verdict(trace,expected,True)
        reason_ok=detail.startswith('early release') if name=='early600' else detail.startswith('late release') if name=='late5000' else verdict=='PASS'
        check(verdict==wanted and reason_ok,'measurement control '+name,(verdict,detail));pg.close()
    # ---- interruption: cancelling mid-opening releases the lock at once; a restart opens once more
    pg=b.new_page(viewport={'width':1280,'height':720});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded');pg.wait_for_timeout(1800);pg.evaluate("closeDialogue();startRaiderBattle()");pg.wait_for_timeout(250)
    pg.evaluate("PrologueCombat.cancel()");pg.wait_for_timeout(60)
    check(pg.evaluate("BattlePresentation.busy")is False and not pg.evaluate("document.body.classList.contains('battlePresentationBusy')"),'interrupt: cancel releases the input lock at once')
    pg.wait_for_timeout(1200);check(pg.evaluate("[BattleActorState.get('raider'),BattleActorState.get('raider','fiona')]")==['idle','idle'],'interrupt: actors still return to rest')
    pg.evaluate("startRaiderBattle()");pg.wait_for_timeout(400);check(pg.evaluate("BattlePresentation.busy")is True,'restart: a new battle start opens again (lock on)');pg.wait_for_timeout(1100)
    check(pg.evaluate("BattlePresentation.busy")is False,'restart: lock released after the opening');check(not errs,'interrupt/restart: no console errors',errs[:2]);pg.close()
    # ---- image load failure: Fiona frames blocked -> opening still ends, lock released, rest pose back
    ctxf=b.new_context(viewport={'width':1280,'height':720});ctxf.route('**/fiona_ready_0*.png',lambda r:r.abort());pg=ctxf.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded');pg.wait_for_timeout(1800);pg.evaluate("closeDialogue();startRaiderBattle()");pg.wait_for_timeout(1500)
    check(pg.evaluate("BattlePresentation.busy")is False and pg.evaluate("[BattleActorState.get('raider'),BattleActorState.get('raider','fiona')]")==['idle','idle'],'load failure: lock released and both at rest');check(not errs,'load failure: no uncaught errors',errs[:2]);pg.close()
    # ---- battle exit during the opening does not leave the lock
    pg=b.new_page(viewport={'width':1280,'height':720});pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded');pg.wait_for_timeout(1800);pg.evaluate("closeDialogue();startRaiderBattle()");pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#raiderBattle').style.display='none';document.body.classList.remove('battleMode','raiderBattleMode');PrologueCombat.cancel()");pg.wait_for_timeout(100)
    check(pg.evaluate("BattlePresentation.busy")is False,'battle exit mid-opening: no lock left');pg.close()
    b.close()
print('FAILS %d'%len(fails));sys.exit(1 if fails else 0)
