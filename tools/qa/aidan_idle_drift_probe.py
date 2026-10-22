"""Aidan idle drift probe - MEASUREMENT ONLY, no game file changed.
CORRECTION to the first reading: Aidan's 6-frame battle idle is NOT the BattleMotion setTimeout chain. It is BattleIdleMotion ('frames' profile): a requestAnimationFrame loop that advances when `now - r.started >= hold`
and then sets `r.started = now` (js/battle-idle-motion.js tick()). The overshoot of every frame (up to one rAF interval, or the whole delay when rAF stalls) is therefore added to the loop and never caught up:
a frame lasts hold + overshoot, so the cycle is longer than nominal, and a stall of N ms stretches the frame on screen by N ms (no skip, no catch-up).
Records, on the page clock (rAF timestamps, the same way tests/battle/battle_idle6.py samples), when each frame of the Aidan idle becomes visible, for DUR seconds, and reports:
  nominal cycle (220,180,220,160,110,260 = 1150 ms) vs the measured frame-1 -> frame-1 period, cumulative drift over the run,
  per-frame lateness (dwell - nominal) mean/p95/max, and `frames_lateness_ge_next_frame_ms` = frames shown so late that a wall-clock scheduler would have jumped over the next frame.
Env: DUR (60 s; not SECONDS - bash owns that name), STRESS (busy-loop processes), THROTTLE (CDP CPU rate), CTX (raider|normal), OUT."""
import os,sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_support import server
from playwright.sync_api import sync_playwright
SEC=int(os.getenv('DUR','60'));STRESS=int(os.getenv('STRESS','0'));THR=float(os.getenv('THROTTLE','1'));CTX=os.getenv('CTX','raider')
SEL={'raider':'#rbAidan','normal':'#bAidan2'}[CTX];START={'raider':'PrologueProgress.seed(0);startRaiderBattle()','normal':'startAttackBattle("attackGob1",100)'}[CTX]
JS="""async([ctx,ms])=>{const rec=[];const t0=performance.now();let last=-1;
 await new Promise(res=>{const tick=t=>{for(const a of BattleIdleMotion.status.actors)if(a.context===ctx&&a.actor==='aidan'&&a.showing&&a.frame!==last){last=a.frame;rec.push([t-t0,a.frame+1])}
  if(t-t0<ms)requestAnimationFrame(tick);else res()};requestAnimationFrame(tick)});return rec}"""
NOM=[220,180,220,160,110,260]
def main():
    stress=[subprocess.Popen([sys.executable,'-c','while True:pass']) for _ in range(STRESS)]
    try:
        with server(8841) as base,sync_playwright() as p:
            b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
            ctx=b.new_context(viewport={'width':1280,'height':720});pg=ctx.new_page();pg.goto(base+'/index.html?dev=1',timeout=90000)
            pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat',timeout=60000);pg.wait_for_timeout(1500);pg.evaluate("closeDialogue()")
            if THR>1:ctx.new_cdp_session(pg).send('Emulation.setCPUThrottlingRate',{'rate':THR})
            pg.evaluate(START);pg.wait_for_timeout(300)
            pg.wait_for_function("!document.body.classList.contains('battlePresentationBusy')&&!document.body.classList.contains('dialogueOpen')&&!document.body.classList.contains('actionCinematic')",timeout=60000);pg.wait_for_timeout(1500)
            rec=pg.evaluate(JS,[CTX,SEC*1000]);b.close()
    finally:[s.kill() for s in stress]
    late=[];skip=0;ones=[]
    for i in range(1,len(rec)-1):
        f=rec[i][1];dwell=rec[i+1][0]-rec[i][0];nom=NOM[f-1];l=dwell-nom;late.append(l)
        if l>=NOM[f%6]:skip+=1
        if f==1:ones.append(rec[i][0])
    cyc=[ones[k+1]-ones[k] for k in range(len(ones)-1)]
    late_s=sorted(late)
    res={'ctx':CTX,'stress':STRESS,'throttle':THR,'seconds':SEC,'frames_seen':len(rec),'cycles':len(cyc),'nominal_cycle_ms':sum(NOM),
      'cycle_mean_ms':round(sum(cyc)/len(cyc),1) if cyc else None,'cycle_max_ms':round(max(cyc),1) if cyc else None,
      'cum_drift_ms':round((ones[-1]-ones[0])-len(cyc)*sum(NOM),1) if len(ones)>1 else None,
      'late_mean_ms':round(sum(late)/len(late),1) if late else None,'late_p95_ms':round(late_s[int(.95*len(late_s))],1) if late else None,'late_max_ms':round(max(late),1) if late else None,
      'frames_lateness_ge_next_frame_ms':skip}
    if os.getenv('OUT'):Path(os.getenv('OUT')).write_text(json.dumps({'summary':res,'rec':rec},indent=0))
    print(json.dumps(res))
main()
