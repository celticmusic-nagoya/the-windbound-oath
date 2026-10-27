"""Baseline for the common Loading design (BL-01 battle start / ML-01 map move). MEASUREMENT ONLY - no game file is changed.
Per run (fresh browser context, so the HTTP/decoded cache is cold) it measures, on the page clock:
  map move  : MossForestStory.enterMap(A1) then A1 -> A2 -> A3 -> A2 (the last is a re-visit): wall time of each enterMap() promise, and the same minus the two fixed fades; image/JSON requests and bytes started during it
  battle    : startAttackBattle() synchronous cost, and the requests / bytes it caused in the next 4 s (first battle = cold, second = warm)
Env: STRESS (busy-loop procs), THROTTLE (CDP CPU rate), OUT."""
import os,sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_support import server
from playwright.sync_api import sync_playwright
STRESS=int(os.getenv('STRESS','0'));THR=float(os.getenv('THROTTLE','1'))
HOOK="""()=>{window.__res=[];new PerformanceObserver(l=>l.getEntries().forEach(e=>window.__res.push([e.name.split('/').slice(-3).join('/'),e.initiatorType,Math.round(e.startTime),Math.round(e.responseEnd),e.encodedBodySize||0]))).observe({type:'resource',buffered:false});
 window.__m=async(id,sp)=>{const n0=window.__res.length,t=performance.now();let err=null;try{await MossForestStory.enterMap(id,sp)}catch(e){err=String(e)}const dt=performance.now()-t;const r=window.__res.slice(n0);return {id,ms:Math.round(dt),req:r.length,kb:Math.round(r.reduce((a,x)=>a+x[4],0)/1024),err}}}"""
def main():
    stress=[subprocess.Popen([sys.executable,'-c','while True:pass']) for _ in range(STRESS)];out={'stress':STRESS,'throttle':THR}
    try:
        with server(8851) as base,sync_playwright() as p:
            b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
            ctx=b.new_context(viewport={'width':1280,'height':720});pg=ctx.new_page();pg.goto(base+'/index.html?dev=1',timeout=90000)
            pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.MossForestStory',timeout=60000);pg.wait_for_timeout(1500);pg.evaluate("closeDialogue()")
            if THR>1:ctx.new_cdp_session(pg).send('Emulation.setCPUThrottlingRate',{'rate':THR})
            pg.evaluate(HOOK);ids=pg.evaluate("MossForestStory.MAP_IDS")
            out['maps']=[]
            for k,(m,sp) in enumerate(((ids['a1'],'from_lind'),(ids['a2'],None),(ids['a3'],None),(ids['a2'],None))):
                try:
                    pg.evaluate("document.body.classList.remove('dialogueOpen')")
                    r=pg.evaluate("([m,s])=>window.__m(m,s||undefined)",[m,sp]);r['step']=k;out['maps'].append(r);pg.wait_for_timeout(800)
                except Exception as e:out['maps'].append({'step':k,'err':repr(e)[:200]})
            out['fade_ms_note']='enter() waits setFade out+in (default 0.35 s each +20 ms) except on the first map; subtract ~740 ms for steps 1-3'
            out['battle']=[]
            for k in range(2):
                try:
                    pg.evaluate("window.__b0=window.__res.length");t=pg.evaluate("(()=>{const t=performance.now();startAttackBattle('attackGob1',100);return performance.now()-t})()");pg.wait_for_timeout(4000)
                    r=pg.evaluate("window.__res.slice(window.__b0)");out['battle'].append({'run':k,'sync_ms':round(t,1),'req_4s':len(r),'kb_4s':round(sum(x[4] for x in r)/1024),'last_end_ms':max([x[3] for x in r] or [0])-min([x[2] for x in r] or [0]),'files':[x[0] for x in r][:8]})
                    pg.evaluate("try{PrologueCombat.cancel&&PrologueCombat.cancel()}catch(e){};location.reload()") if False else None
                    break
                except Exception as e:out['battle'].append({'run':k,'err':repr(e)[:200]});break
            b.close()
    finally:[s.kill() for s in stress]
    if os.getenv('OUT'):Path(os.getenv('OUT')).write_text(json.dumps(out,indent=1))
    print(json.dumps(out)[:1800])
main()
