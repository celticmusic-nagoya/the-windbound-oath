"""BattleMotion run.done + BattleActorState two-condition rest (duration elapsed AND motion complete).
Normal completion / stop / replace settle exactly once; stale runs never touch a newer state; KO / victory / battle end / new battle are not overridden."""
import os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail)
    if not ok:fails.append(name)
with server(8816) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    pg=b.new_page(viewport={'width':1280,'height':720});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.goto(base+'/index.html');pg.wait_for_function('window.BattleMotion&&BattleMotion.loaded&&window.BattleActorState');pg.wait_for_timeout(1500);pg.evaluate("closeDialogue()")
    # ---- BattleMotion level (scratch <img>, no battle needed)
    r=pg.evaluate("""async()=>{
      const mk=()=>{const i=document.createElement('img');document.body.append(i);return i};const out={};
      const tot=BattleMotion.info('aidan','attack').totalMs;out.tot=tot;
      let i1=mk();let t=performance.now();let run=BattleMotion.start(i1,'aidan','attack');out.hasDone=run&&typeof run.done.then==='function';
      out.beforeFinished=run.finished;const res=await run.done;out.normal={res,dt:Math.round(performance.now()-t),finished:run.finished,frame:i1.dataset.motionFrame};
      out.again=await run.done;BattleMotion.stop(i1);out.afterStop=(await run.done)===res;   // already settled: stop must not change the result
      i1.remove();
      let i2=mk();run=BattleMotion.start(i2,'aidan','attack');await new Promise(r=>setTimeout(r,150));t=performance.now();BattleMotion.stop(i2);const sres=await run.done;out.stop={res:sres,dt:Math.round(performance.now()-t),finished:run.finished};
      const f=i2.dataset.motionFrame;await new Promise(r=>setTimeout(r,tot));out.stopFrozen=i2.dataset.motionFrame===f;BattleMotion.stop(i2);out.stop2=(await run.done)===sres;i2.remove();
      let i3=mk();const ra=BattleMotion.start(i3,'aidan','attack');await new Promise(r=>setTimeout(r,120));const rb=BattleMotion.start(i3,'aidan','skill');const a=await ra.done;out.replaced={a,bFinishedAtReplace:rb.finished};const bres=await rb.done;out.replaced.b=bres;i3.remove();
      let i4=mk();out.none=BattleMotion.start(i4,'aidan','idle')===null||BattleMotion.start(i4,'aidan','no_such_state')===null;i4.remove();
      // hold:'last' keeps the final frame after done
      let i5=mk();const r5=BattleMotion.start(i5,'aidan','draw');await r5.done;out.holdLast={frame:i5.dataset.motionFrame,n:BattleMotion.info('aidan','draw').frames};await new Promise(r=>setTimeout(r,300));out.holdLast.later=i5.dataset.motionFrame;i5.remove();
      return out}""")
    n=r['tot']
    check(r['hasDone'] and r['beforeFinished'] is False,'start() returns run with done Promise, not finished yet')
    check(r['normal']['res']=={'completed':True,'reason':'complete','frames':6,'ms':r['normal']['res']['ms']} and r['normal']['finished'] is True,'normal completion -> {completed:true, reason:complete}',r['normal'])
    check(n<=r['normal']['dt']<=n+150,'completion arrives after the last frame\'s display time (total %d)'%n,r['normal']['dt'])
    check(r['normal']['frame']=='6','last frame still on screen at completion')
    check(r['again']==r['normal']['res'] and r['afterStop'],'result is stable: no second notification, late stop() changes nothing')
    check(r['stop']['res']['completed'] is False and r['stop']['res']['reason']=='stopped' and r['stop']['dt']<30 and r['stop']['finished'],'stop() settles immediately as stopped',r['stop'])
    check(r['stopFrozen'] and r['stop2'],'stopped run plays no more frames and stays settled once')
    check(r['replaced']['a']['reason']=='replaced' and not r['replaced']['a']['completed'] and r['replaced']['bFinishedAtReplace'] is False and r['replaced']['b']['completed'],'newer start() settles the older run as replaced, newer one completes normally',r['replaced'])
    check(r['none'],'no motion installed -> null (stills as before)')
    check(r['holdLast']['frame']==str(r['holdLast']['n']) and r['holdLast']['later']==r['holdLast']['frame'],'hold:last keeps the final frame after completion',r['holdLast'])
    # ---- BattleActorState level
    SET="""async([ctx,actor,state,dur])=>{window.__ev=[];const t=performance.now();BattleActorState.set(actor,state,{battle:ctx,duration:dur});
      const iv=setInterval(()=>{const s=BattleActorState.get(ctx,actor);if(s!==(__ev.at(-1)||[])[1])__ev.push([Math.round(performance.now()-t),s])},10);window.__stop=()=>clearInterval(iv);return t}"""
    def run_state(ctx,actor,state,dur,wait):
        pg.evaluate("BattleActorState.begin(%r,%r)"%(ctx,actor) if actor!='aidan' else "BattleActorState.begin(%r)"%ctx)
        pg.evaluate(SET,[ctx,actor,state,dur]);pg.wait_for_timeout(wait);return pg.evaluate("(__stop(),__ev)")
    def rest_at(ev,rest='idle'):
        for t,s in ev:
            if s==rest and t>0:return t
    total=pg.evaluate("BattleMotion.info('aidan','attack').totalMs")
    ev=run_state('normal','aidan','attack',100,total+500);t=rest_at(ev)
    check(t is not None and total<=t<=total+120,'duration 100 < motion %d: rest waits for motion completion'%total,ev)
    ev=run_state('normal','aidan','attack',total+400,total+900);t=rest_at(ev)
    check(t is not None and total+400<=t<=total+400+120,'duration %d > motion: rest at the requested duration'%(total+400),ev)
    ev=run_state('normal','aidan','damage',300,900);t=rest_at(ev)
    check(t is not None and 300<=t<=420,'still-image state (damage, no frames): unchanged timing',ev)
    for actor,ctx,state in (('aidan','normal','skill'),('aidan','raider','attack'),('fiona','normal','ready'),('fiona','raider','attack')):
        info=pg.evaluate("BattleMotion.has(%r,%r)&&BattleMotion.info(%r,%r)"%(actor,state,actor,state))
        ev=run_state(ctx,actor,state,200,(info['totalMs'] if info else 600)+500);t=rest_at(ev)
        check(t is not None and (not info or info['totalMs']<=t<=info['totalMs']+150),'%s/%s %s -> idle after completion'%(ctx,actor,state),(info and info['totalMs'],t))
    # interruption: older run's completion must not return the newer pose to rest
    pg.evaluate("BattleActorState.begin('normal')");
    r=pg.evaluate("""async()=>{BattleActorState.set('aidan','attack',{battle:'normal',duration:100});const old=BattleActorState.motion('normal');await new Promise(r=>setTimeout(r,60));
      BattleActorState.set('aidan','skill',{battle:'normal',duration:3000});const o=await old.done;const s0=BattleActorState.get('normal');await new Promise(r=>setTimeout(r,700));return {o,s0,s1:BattleActorState.get('normal')}}""")
    check(r['o']['reason']=='replaced' and r['s0']=='skill' and r['s1']=='skill','interrupted run settles; its completion does not rest the newer pose',r)
    # KO during a pose: no rest after completion
    r=pg.evaluate("""async()=>{BattleActorState.begin('normal');const hp=aahp;BattleActorState.set('aidan','attack',{battle:'normal',duration:100});await new Promise(r=>setTimeout(r,80));aahp=0;BattleActorState.sync('normal');
      await new Promise(r=>setTimeout(r,1200));const s=BattleActorState.get('normal');aahp=hp;BattleActorState.recover('normal');return s}""")
    check(r=='ko','KO during a pose: stays ko after motion completion',r)
    # victory is not overwritten
    r=pg.evaluate("""async()=>{BattleActorState.begin('normal');BattleActorState.set('aidan','attack',{battle:'normal',duration:100});await new Promise(r=>setTimeout(r,60));
      const ok=BattleActorState.set('aidan','victory',{battle:'normal'});const s0=BattleActorState.get('normal');await new Promise(r=>setTimeout(r,1200));return {ok,s0,s1:BattleActorState.get('normal')}}""")
    check(r['s1']=='victory' and r['s0']=='victory','victory is not overwritten by the older pose\'s completion',r)
    # battle end / restart: stale completion has no effect on a new battle
    r=pg.evaluate("""async()=>{BattleActorState.begin('normal');BattleActorState.set('aidan','attack',{battle:'normal',duration:100});const old=BattleActorState.motion('normal');await new Promise(r=>setTimeout(r,60));
      BattleActorState.end('normal');BattleActorState.begin('normal');BattleActorState.set('aidan','skill',{battle:'normal',duration:5000});const sk=BattleActorState.get('normal');
      const o=await old.done;await new Promise(r=>setTimeout(r,300));return {sk,o:o.reason,after:BattleActorState.get('normal')}}""")
    check(r['after']=='skill' and r['o']=='replaced','stale run completion after battle end/restart leaves the new battle alone',r)
    r=pg.evaluate("""async()=>{BattleActorState.begin('normal');BattleActorState.set('aidan','attack',{battle:'normal',duration:100});BattleActorState.end('normal');await new Promise(r=>setTimeout(r,1000));return BattleActorState.get('normal')}""")
    check(r=='attack','battle end: no late rest paint from the old timer/promise (state untouched)',r)
    # one timer only
    r=pg.evaluate("""async()=>{BattleActorState.begin('normal');let n=0;const o=BattleActorState.set;BattleActorState.set('aidan','attack',{battle:'normal',duration:100,next:'damage',nextDuration:100});await new Promise(r=>setTimeout(r,1500));return BattleActorState.get('normal')}""")
    check(r=='idle','next-chained pose also returns to idle exactly once',r)
    check(not errs,'no console/page errors',errs)
    b.close()
print('FAILS',fails);sys.exit(1 if fails else 0)
