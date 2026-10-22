"""Fiona idle v3 - stall attribution probe (Codex FIV3 FAIL: ~7.9 s draw stop in a 320 s soak). MEASUREMENT ONLY: changes no game file, asserts nothing about the game.
Goal: when the idle renderer stops drawing, say WHICH layer stopped, using independent clocks on ONE time axis (epoch ms = performance.timeOrigin + performance.now()):
  W  dedicated Worker heartbeat (25 ms setInterval, records its own timestamps; NOT blocked by the page main thread)  -> process/host starvation shows here
  T  main-thread setTimeout(25 ms) chain                                                                               -> main thread blocked, or timers throttled
  R  main-thread requestAnimationFrame chain                                                                           -> frame production / compositor
  D  Fiona layered draws from BattleIdleMotion.traceStart() (the product's own draw log)                              -> the idle renderer itself
  L  longtask entries, hidden/body-class events, heap samples (performance.memory, 1 Hz; a drop = GC)
Host side (Python, 1 Hz): wall clock jumps, /proc/stat steal+iowait deltas, /proc/pressure/cpu, loadavg, CDP Performance.getMetrics (Task/Script/Layout/RecalcStyle duration, JSHeapUsedSize, Nodes).
Per stall (any of R/T/D/W gap > STALL_MS) the verdict names the layers that stopped together:
  W+T+R+D stalled          -> process-level freeze (host/CPU starvation/VM pause), not the page
  T+R+D stalled, W alive   -> main thread blocked (see longtask / GC / metrics in the window)
  R+D stalled, T,W alive   -> frame delivery stopped (rAF), main thread free
  D stalled only           -> the idle renderer did not draw although frames were delivered (paused()/eligible/exception)
Env: MODE=on|off|alt (on = Fiona idle drawing the whole time; off = BattleIdleMotion.stop() for the whole run; alt = ON/OFF phases of PHASE_S, CYCLES), SECONDS (320, for on/off), PHASE_S (40), CYCLES (2),
     STRESS=N (start N busy-loop processes for the run), THROTTLE (CDP CPU slow-down), CTX (raider|normal), RUNTIME (head|main as in fiona_v3_load_probe), OUT (json path), STALL_MS (400)."""
import os,sys,json,time,subprocess,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_support import server
import fiona_v3_trace as S
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
MODE=os.getenv('MODE','on');SECONDS=float(os.getenv('SECONDS','320'));PHASE=float(os.getenv('PHASE_S','40'));CYCLES=int(os.getenv('CYCLES','2'));CTXN=os.getenv('CTX','raider')
RUNTIME=os.getenv('RUNTIME','head');MAIN_REF=os.getenv('MAIN_REF','origin/main');STRESS=int(os.getenv('STRESS','0'));THR=float(os.getenv('THROTTLE','1'));STALL=float(os.getenv('STALL_MS','400'));VARIANT=os.getenv('VARIANT','none')
START={'raider':'startRaiderBattle()','normal':'startAttackBattle("attackGob2",100)'}[CTXN]
SEL={'raider':'#rbFiona img','normal':'#bFiona2 img'}[CTXN]
INSTALL="""()=>{const EP=()=>performance.timeOrigin+performance.now();const W=window.__sp={ep0:EP(),raf:[],tmr:[],lt:[],ev:[],heap:[],wk:null,phase:'init',drawErr:[]};
 const src='const a=[];setInterval(()=>a.push(performance.timeOrigin+performance.now()),25);onmessage=()=>{postMessage(a)}';
 const wk=new Worker(URL.createObjectURL(new Blob([src],{type:'text/javascript'})));W.worker=wk;wk.onmessage=e=>{W.wk=e.data};
 let lr=EP();const tick=()=>{const n=EP();W.raf.push([n,n-lr,W.phase]);lr=n;requestAnimationFrame(tick)};requestAnimationFrame(tick);
 let lt=EP();const tm=()=>{const n=EP();W.tmr.push([n,n-lt,W.phase]);lt=n;setTimeout(tm,25)};setTimeout(tm,25);
 try{new PerformanceObserver(l=>l.getEntries().forEach(e=>W.lt.push([performance.timeOrigin+e.startTime,e.duration,W.phase]))).observe({type:'longtask',buffered:false})}catch(e){}
 new MutationObserver(()=>W.ev.push([EP(),'class='+document.body.className])).observe(document.body,{attributes:true,attributeFilter:['class']});
 document.addEventListener('visibilitychange',()=>W.ev.push([EP(),'hidden='+document.hidden]));
 window.addEventListener('error',e=>W.drawErr.push([EP(),String(e.message)]));window.addEventListener('unhandledrejection',e=>W.drawErr.push([EP(),'rej '+String(e.reason)]));
 setInterval(()=>{const m=performance.memory;if(m)W.heap.push([EP(),m.usedJSHeapSize])},1000);
 BattleIdleMotion.traceStart();}"""
def read_stat():
    try:
        c=open('/proc/stat').readline().split()[1:];v=list(map(int,c));return {'total':sum(v),'steal':v[7] if len(v)>7 else 0,'iowait':v[4]}
    except Exception:return None
def pressure():
    try:return open('/proc/pressure/cpu').read().split('\n')[0]
    except Exception:return None
def git_show(path):return subprocess.run(['git','show','%s:%s'%(MAIN_REF,path)],cwd=ROOT,capture_output=True,check=True).stdout
def gaps(rows,key=1):return [(r[0]-r[1],r[0],r[1],r[2] if len(r)>2 else '') for r in rows if r[key]>STALL]   # (start_ep, end_ep, gap_ms, phase)
def merge_events(ev):   # stalls from different layers that overlap in time are one incident
    ev=sorted(ev,key=lambda e:e[0]);out=[]
    for s,e,g,src,ph in ev:
        if out and s<=out[-1]['end']+200:
            o=out[-1];o['end']=max(o['end'],e);o['start']=min(o['start'],s);o['layers'].add(src);o['phases'].add(ph)
        else:out.append({'start':s,'end':e,'layers':{src},'phases':{ph}})
    return out
def main():
    stress=[subprocess.Popen([sys.executable,'-c','while True:pass']) for _ in range(STRESS)]
    host=[];stop=threading.Event()
    def hostloop():
        prev=read_stat();pw=time.time()
        while not stop.wait(1.0):
            now=time.time();cur=read_stat();row={'wall':now,'dt':round(now-pw,3),'load1':os.getloadavg()[0],'psi':pressure()}
            if prev and cur:
                dt=max(cur['total']-prev['total'],1);row['steal_pct']=round(100*(cur['steal']-prev['steal'])/dt,2);row['iowait_pct']=round(100*(cur['iowait']-prev['iowait'])/dt,2)
            prev=cur;pw=now;host.append(row)
    th=threading.Thread(target=hostloop,daemon=True);th.start()
    cdp_rows=[];phases=[]
    try:
        with server(8819) as base,sync_playwright() as p:
            b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None),args=['--enable-precise-memory-info'])
            ctx=b.new_context(viewport={'width':1280,'height':720});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
            if RUNTIME=='main':
                def serve(route):
                    u=route.request.url;path=u.split(base+'/',1)[1].split('?')[0]
                    try:route.fulfill(status=200,body=git_show(path),content_type='application/javascript' if path.endswith('.js') else 'image/png')
                    except Exception:route.continue_()
                for pat in ('**/js/assets.js*','**/js/battle-idle-motion.js*','**/img/battle/characters/fiona/idle/*.png'):ctx.route(pat,serve)
            pg.goto(base+'/index.html',timeout=90000);pg.wait_for_function('window.BattleIdleMotion&&window.BattleActorState',timeout=60000);pg.wait_for_timeout(1500);pg.evaluate("closeDialogue()");pg.wait_for_timeout(300)
            pg.evaluate(START);pg.wait_for_timeout(2500)
            pg.wait_for_function("BattleIdleMotion.status.actors.some(q=>q.actor==='fiona'&&q.context===%r&&q.showing)"%CTXN,timeout=30000)
            pg.evaluate("typeof closeDialogue==='function'&&closeDialogue()");pg.wait_for_function("!['battlePresentationBusy','dialogueOpen','actionCinematic'].some(c=>document.body.classList.contains(c))",timeout=30000);pg.wait_for_timeout(800)
            cdp=ctx.new_cdp_session(pg);cdp.send('Performance.enable')
            if THR>1:cdp.send('Emulation.setCPUThrottlingRate',{'rate':THR})
            pg.evaluate(INSTALL)
            if VARIANT=='low_quality':pg.evaluate("""()=>{const o=Object.getOwnPropertyDescriptor(CanvasRenderingContext2D.prototype,'imageSmoothingQuality');Object.defineProperty(CanvasRenderingContext2D.prototype,'imageSmoothingQuality',{configurable:true,get:o.get,set(v){o.set.call(this,'low')}})}""")   # in-page A/B only, never committed to the game
            def sample():
                m={x['name']:x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
                cdp_rows.append({'wall':time.time(),**{k:round(m[k],4) for k in ('TaskDuration','ScriptDuration','LayoutDuration','RecalcStyleDuration','JSHeapUsedSize','Nodes','JSEventListeners') if k in m}})
            def run(seconds,tag,on):
                pg.evaluate("n=>{__sp.phase=n}",tag)
                pg.evaluate("a=>{const s=a[0],on=a[1];if(on)BattleIdleMotion.begin(s,'fiona');else BattleIdleMotion.stop(s)}",[SEL,on]);pg.wait_for_timeout(600)
                st=pg.evaluate("BattleIdleMotion.status.actors.find(q=>q.actor==='fiona'&&q.context===%r).showing"%CTXN)
                phases.append({'tag':tag,'on':on,'showing_at_start':st,'wall0':time.time(),'seconds':seconds})
                end=time.time()+seconds
                while time.time()<end:
                    sample();pg.wait_for_timeout(2000)
            if MODE=='alt':
                for c in range(CYCLES):
                    run(PHASE,'ON%d'%c,True);run(PHASE,'OFF%d'%c,False)
            else:run(SECONDS,MODE.upper(),MODE=='on')
            sample();pg.evaluate("__sp.worker.postMessage(0)");pg.wait_for_function("__sp.wk!==null",timeout=60000)
            d=pg.evaluate("({raf:__sp.raf,tmr:__sp.tmr,lt:__sp.lt,ev:__sp.ev,heap:__sp.heap,wk:__sp.wk,err:__sp.drawErr,tr:BattleIdleMotion.traceStop(),ep0:__sp.ep0,to:performance.timeOrigin,hidden:document.hidden})")
            b.close()
    finally:
        stop.set();[s.kill() for s in stress]
    wk=d['wk'];wg=[(wk[i-1],wk[i],wk[i]-wk[i-1],'') for i in range(1,len(wk)) if wk[i]-wk[i-1]>STALL]
    draws=[x for x in d['tr'] if x['ctx']==CTXN and not x['still']];dg=[(draws[i-1]['now']+0,draws[i]['now'],draws[i]['now']-draws[i-1]['now'],'') for i in range(1,len(draws)) if draws[i]['now']-draws[i-1]['now']>STALL]
    # trace 'now' is the rAF timestamp (performance.now, page clock): move it to the epoch axis with the page's time origin
    # (ep0 was taken with performance.timeOrigin+performance.now() when the probe was installed)
    ev_all=[]
    for s,e,g,ph in gaps(d['raf']):ev_all.append((s,e,g,'R',ph))
    for s,e,g,ph in gaps(d['tmr']):ev_all.append((s,e,g,'T',ph))
    for s,e,g,_ in wg:ev_all.append((s,e,g,'W',''))
    anchor=d['to']   # draw 'now' is performance.now(); epoch = performance.timeOrigin + now (same axis as the other layers)
    off_iv=[]   # epoch intervals of the OFF phases (idle drawing stopped on purpose): a draw hole that overlaps one is not an incident
    for ph in sorted({r[2] for r in d['raf'] if r[2].startswith('OFF')}):
        xs=[r[0] for r in d['raf'] if r[2]==ph];off_iv.append((min(xs)-700,max(xs)+700))
    for s,e,g,_ in dg:
        if any(s+anchor<=b_ and e+anchor>=a_ for a_,b_ in off_iv):continue   # OFF phase: the idle draw loop is stopped on purpose
        ev_all.append((s+anchor,e+anchor,g,'D',''))
    inc=merge_events(ev_all);out=[]
    for i in inc:
        L=sorted(i['layers']);w0,w1=i['start']-300,i['end']+300
        lts=[x for x in d['lt'] if w0<=x[0]<=w1];evs=[x for x in d['ev'] if w0<=x[0]<=w1]
        hp=[x for x in d['heap'] if w0-2000<=x[0]<=w1+2000];drop=[hp[k][1]-hp[k-1][1] for k in range(1,len(hp)) if hp[k][1]<hp[k-1][1]]
        cs=[h for h in host if w0/1000-2<=h['wall']<=w1/1000+2]
        verdict=S.classify_incident(L)
        out.append({'start_s':round((i['start']-d['ep0'])/1000,2),'dur_ms':round(i['end']-i['start']),'stalled_layers':''.join(L),'phases':sorted(x for x in i['phases'] if x),'verdict':verdict,'longtasks_in_window':[[round((x[0]-d['ep0'])/1000,2),round(x[1])] for x in lts][:8],
          'events_in_window':[[round((x[0]-d['ep0'])/1000,2),x[1]] for x in evs][:6],'heap_drops_bytes_in_window':drop[:5],'host_in_window':[{k:h.get(k) for k in ('dt','load1','steal_pct','iowait_pct','psi')} for h in cs][:6]})
    def rng(rows,k=1):
        v=[r[k] for r in rows];return {'n':len(v),'max_ms':round(max(v),1) if v else None,'over100':sum(1 for x in v if x>100)}
    byph={}
    for ph in sorted({r[2] for r in d['raf']}):
        byph[ph]={'raf':rng([r for r in d['raf'] if r[2]==ph]),'timer25':rng([r for r in d['tmr'] if r[2]==ph]),'longtasks':sum(1 for x in d['lt'] if x[2]==ph),'longest_task_ms':round(max([x[1] for x in d['lt'] if x[2]==ph] or [0]))}
    res={'mode':MODE,'seconds':SECONDS,'stress':STRESS,'throttle':THR,'variant':VARIANT,'runtime':RUNTIME,'ctx':CTXN,'stall_threshold_ms':STALL,'nproc':os.cpu_count(),'errors':errs[:3]+[str(x) for x in d['err'][:3]],'phases':phases and [{k:v for k,v in q.items() if k!='wall0'} for q in phases],
         'overall':{'worker_beat':rng([[0,wk[i]-wk[i-1]] for i in range(1,len(wk))]),'raf':rng(d['raf']),'timer25':rng(d['tmr']),'draws':len(draws),'draw_gap_max_ms':round(max([draws[i]['now']-draws[i-1]['now'] for i in range(1,len(draws))] or [0]),1),'longtasks':len(d['lt']),'longest_task_ms':round(max([x[1] for x in d['lt']] or [0]))},
         'by_phase':byph,'host':{'max_wall_gap_s':max([h['dt'] for h in host] or [0]),'max_steal_pct':max([h.get('steal_pct',0) for h in host] or [0]),'max_iowait_pct':max([h.get('iowait_pct',0) for h in host] or [0]),'max_load1':max([h['load1'] for h in host] or [0])},
         'incidents':out}
    if os.getenv('OUT'):Path(os.getenv('OUT')).write_text(json.dumps({'summary':res,'host':host,'cdp':cdp_rows,'raw_longtasks':d['lt'],'raw_events':d['ev'][:200]},indent=1))
    print(json.dumps(res,indent=1))
main()
