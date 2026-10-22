"""ally_motion_p3 intermittent FAIL - readiness-order probe (Codex FIV3: Lou/Fiona heal image 'not ready' at the +250 ms mid sample). MEASUREMENT ONLY: game files untouched, nothing asserted about the game.
For each action it records, on the PAGE clock, the order of: action call -> <img src> attribute set -> resource request/response (Resource Timing; was it already fetched by BattleMotion's preload?)
-> the img 'load' event -> img.decode() settled -> first requestAnimationFrame after load, and the exact state of the +250 ms sample the test takes (img.complete, naturalWidth, src).
Trials use the test's own preamble (fresh page, startRaiderBattle, opening presentation finished, +1.5 s) so the numbers are for the same timing the test has.
Env: TRIALS (8), VP (pc|portrait|landscape), THROTTLE (CDP CPU factor), STRESS (busy-loop processes), ACTIONS ("fiona:heal,lou:heal"), OUT."""
import os,sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_support import server
from playwright.sync_api import sync_playwright
TRIALS=int(os.getenv('TRIALS','8'));VPN=os.getenv('VP','pc');THR=float(os.getenv('THROTTLE','1'));STRESS=int(os.getenv('STRESS','0'))
ACTS=[tuple(x.split(':')) for x in os.getenv('ACTIONS','fiona:heal,lou:heal').split(',')]
VP={'pc':(1280,720),'portrait':(390,844),'landscape':(844,390)}[VPN]
PROBE="""async(a)=>{const [actor,state]=a;const sel={aidan:'#rbAidan',fiona:'#rbFiona',lou:'#rbLou'}[actor];const e=document.querySelector(sel);const img=e&&e.querySelector('img');if(!img)return {err:'no img'};
 const T0=performance.now(),rel=()=>Math.round((performance.now()-T0)*10)/10;const out={actor,state,t:{},srcs:[],loads:[]};
 const mo=new MutationObserver(ms=>ms.forEach(m=>{if(m.attributeName==='src'){out.srcs.push([rel(),img.getAttribute('src').split('/').slice(-2).join('/')])}}));mo.observe(img,{attributes:true,attributeFilter:['src']});
 const onload=()=>{out.loads.push([rel(),img.src.split('/').slice(-2).join('/'),img.naturalWidth]);requestAnimationFrame(()=>out.t.raf_after_load=out.t.raf_after_load||rel())};img.addEventListener('load',onload);
 const ok=BattleActorState.action(actor,state,{battle:'raider'});out.ok=ok;out.t.action_returned=rel();
 await new Promise(r=>setTimeout(r,250));
 out.mid={t:rel(),complete:img.complete,nw:img.naturalWidth,src:img.src.split('/').slice(-2).join('/'),okTest:img.complete&&img.naturalWidth>0};
 // resource timing for what the img is showing now (was it fetched earlier by the preload, and had it finished before the action?)
 const nm=img.currentSrc||img.src;const re=performance.getEntriesByName(nm);out.resource=re.length?{count:re.length,startedBeforeAction:Math.round(re[0].startTime-T0),endedBeforeAction:Math.round(re[0].responseEnd-T0),initiator:re[0].initiatorType}:null;
 try{const t=performance.now();await img.decode();out.decode_ms=Math.round((performance.now()-t)*10)/10}catch(x){out.decode_err=String(x)}
 await new Promise(r=>setTimeout(r,1700));out.end={complete:img.complete,nw:img.naturalWidth,state:BattleActorState.get('raider',actor)};mo.disconnect();img.removeEventListener('load',onload);return out}"""
def main():
    stress=[subprocess.Popen([sys.executable,'-c','while True:pass']) for _ in range(STRESS)];rows=[]
    try:
        with server(8833) as base,sync_playwright() as p:
            b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
            for k in range(TRIALS):
                ctx=b.new_context(viewport={'width':VP[0],'height':VP[1]});pg=ctx.new_page()
                pg.goto(base+'/index.html?dev=1',timeout=90000);pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat',timeout=60000);pg.wait_for_timeout(1500);pg.evaluate("closeDialogue()")
                if THR>1:ctx.new_cdp_session(pg).send('Emulation.setCPUThrottlingRate',{'rate':THR})
                pg.evaluate("PrologueProgress.seed(0);startRaiderBattle()");pg.wait_for_timeout(300)
                pg.wait_for_function("!document.body.classList.contains('battlePresentationBusy')&&!document.body.classList.contains('dialogueOpen')&&!document.body.classList.contains('actionCinematic')",timeout=30000);pg.wait_for_timeout(1500)
                for a in ACTS:
                    if a[0]=='lou' and not pg.evaluate("!!document.querySelector('#rbLou img')&&getComputedStyle(document.querySelector('#rbLou')).visibility!=='hidden'"):rows.append({'trial':k,'actor':a[0],'state':a[1],'skipped':'lou not in party'});continue
                    r=pg.evaluate(PROBE,list(a));r['trial']=k;rows.append(r)
                ctx.close()
            b.close()
    finally:
        [s.kill() for s in stress]
    summ={}
    for r in rows:
        if 'mid' not in r:continue
        s=summ.setdefault('%s:%s'%(r['actor'],r['state']),{'n':0,'mid_not_ready':0,'not_ready_resource_not_yet_fetched':0,'not_ready_fetched_but_pending':0,'src_to_load_ms':[],'decode_ms':[]})
        s['n']+=1;ready=r['mid']['okTest']
        if not ready:
            s['mid_not_ready']+=1
            if r['resource'] is None or r['resource']['endedBeforeAction']>0:s['not_ready_resource_not_yet_fetched']+=1
            else:s['not_ready_fetched_but_pending']+=1
        if r['srcs'] and r['loads']:s['src_to_load_ms'].append(round(r['loads'][-1][0]-r['srcs'][0][0],1))
        if 'decode_ms' in r:s['decode_ms'].append(r['decode_ms'])
    res={'viewport':VPN,'throttle':THR,'stress':STRESS,'trials':TRIALS,'summary':summ,'rows':rows}
    if os.getenv('OUT'):Path(os.getenv('OUT')).write_text(json.dumps(res,indent=1))
    print(json.dumps({k:v for k,v in res.items() if k!='rows'},indent=1))
main()
