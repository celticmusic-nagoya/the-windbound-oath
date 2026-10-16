"""BL-01 BattleLoading: 戦闘準備中… precedes the battle; assets prepared; min display; fallback never hangs; no duplicate requests; stale/cancel safe."""
import os,sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail)
    if not ok:fails.append(name)
INIT="""(()=>{window.__bl=[];window.__open=0;addEventListener('battle-opening',()=>{window.__open++});addEventListener('battle-loading',e=>__bl.push(Object.assign({t:Math.round(performance.now())},e.detail)));
 const d=HTMLImageElement.prototype.decode;window.__dc={};window.__dcField={};window.__rule=null;
 HTMLImageElement.prototype.decode=function(){const u=this.src.split('/').slice(-2).join('/').split('?')[0];
  if(/forest-loader/.test(new Error().stack||'')){__dcField[u]=(__dcField[u]||0)+1;return d.call(this)}   /* the field art loader retries its own failed decodes (documented in forest-loader.js); not a Loading decode */
  __dc[u]=(__dc[u]||0)+1;
  const r=window.__rule;if(r&&r.re.test(u)&&__dc[u]<=r.times)return Promise.reject(new DOMException('The source image cannot be decoded.','EncodingError'));return d.call(this)};
window.__ov=[];document.addEventListener('DOMContentLoaded',()=>new MutationObserver(()=>{const e=document.getElementById('battleLoading');const on=!!e&&e.classList.contains('isOn');const l=__ov[__ov.length-1];if(!l||l.on!==on)__ov.push({on,t:Math.round(performance.now()),mode:document.body.classList.contains('battleMode')})}).observe(document.documentElement,{attributes:true,subtree:true,attributeFilter:['class']}));
})()"""
def fresh(b,vp=(844,390),dpr=2):
    c=b.new_context(viewport={'width':vp[0],'height':vp[1]},device_scale_factor=dpr);c.add_init_script(INIT);pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append('pageerror:'+str(e)));pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None)
    reqs={};pg.on('request',lambda r:reqs.__setitem__(r.url,reqs.get(r.url,0)+1));pg.reqs=reqs
    return c,pg,errs
def boot(pg,base,wait=1500):
    pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat&&window.BattleLoading');pg.wait_for_timeout(wait);pg.evaluate('closeDialogue()')
MODE="document.body.classList.contains('raiderBattleMode')?'raider':document.body.classList.contains('normalBattleMode')?'normal':null"
ST="(()=>{const s=BattleLoading.status;return {state:s.state,fallback:s.fallback,failed:s.failed,units:s.units,shownMs:s.shownMs,reason:s.reason,last:s.last&&{state:s.last.state,shownMs:s.last.shownMs,failed:s.last.failed,units:s.last.units,fallback:s.last.fallback,reason:s.last.reason}}})()"
def run_to_end(pg,limit=9000):
    t=time.time()
    while time.time()-t<limit/1000:
        if not pg.evaluate('BattleLoading.active'):return True
        pg.wait_for_timeout(40)
    return False
def settle(pg,ms=2200):pg.wait_for_timeout(ms)
def started(pg,call,vp=None):
    pg.evaluate("window.__bl.length=0;window.__ov.length=0");pg.evaluate(call)
with server(8817) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    for ctxname,call,mode in (('normal',"startAttackBattle('northGob1',180)",'normal'),('raider',"startRaiderBattle()",'raider')):
        c,pg,errs=fresh(b);boot(pg,base)
        t0=pg.evaluate("performance.now()");started(pg,call);pg.wait_for_timeout(60)
        r=pg.evaluate("({ov:!!document.getElementById('battleLoading')?.classList.contains('isOn'),txt:document.querySelector('#battleLoading .blText')?.textContent,mode:%s,bm:document.body.classList.contains('battleMode'),st:BattleLoading.status.state,top:(()=>{const e=document.elementFromPoint(innerWidth/2,innerHeight/2);return e&&!!e.closest('#battleLoading')})()})"%MODE)
        check(r['ov'] and r['txt']=='戦闘準備中…' and r['st']=='preparing','%s: Loading shown at once with the text'%ctxname,r)
        check(r['mode'] is None and not r['bm'],'%s: battle scene NOT started while Loading'%ctxname)
        check(r['top'],'%s: overlay covers the screen (pointer input blocked)'%ctxname)
        pg.keyboard.press('Enter');pg.keyboard.press('Space');pg.keyboard.press('z')
        check(run_to_end(pg),'%s: Loading finishes'%ctxname)
        pg.wait_for_timeout(100)
        s=pg.evaluate(ST);ev=pg.evaluate('__bl');ov=pg.evaluate('__ov')
        ph=[e['phase'] for e in ev]
        check(ph==['start','ready'],'%s: events start->ready'%ctxname,ph)
        check(s['last']['state']=='ready' and not s['last']['fallback'] and not s['last']['failed'],'%s: ready with every unit prepared'%ctxname,s['last'])
        check(s['last']['units']['done']==s['last']['units']['total'] and s['last']['units']['total']>=6,'%s: progress = real finished/total'%ctxname,s['last']['units'])
        check(s['last']['shownMs']>=395,'%s: minimum display 400ms honoured'%ctxname,s['last']['shownMs'])
        on_=[o for o in ov if o['on']];off=[o for o in ov if not o['on']]
        check(bool(on_) and bool(off) and on_[0]['mode'] is False and off[0]['t']-on_[0]['t']>=395,'%s: overlay on while the field is still the scene; removed in the same task the battle appears (no gap frame)'%ctxname,ov)
        pg.wait_for_timeout(250)
        check(pg.evaluate(MODE)==mode,'%s: battle then starts'%ctxname,pg.evaluate(MODE))
        check(pg.evaluate("document.body.classList.contains('battleLoading')")==False,'%s: no leftover loading class'%ctxname)
        settle(pg,1800)
        o=pg.evaluate("({busy:BattlePresentation.busy,a:BattleActorState.get('%s'),f:BattleActorState.get('%s','fiona')})"%(mode,mode))
        check(not o['busy'] and o['a']=='idle' and o['f']=='idle','%s: opening (draw/ready) played out, COMMAND unlocked, back to idle'%ctxname,o)
        cv=pg.evaluate("[...document.querySelectorAll('canvas.battle-idle-canvas')].filter(c=>!c.hidden).length")
        check(cv>=2,'%s: idle canvases shown (first display not missing)'%ctxname,cv)
        check(not errs,'%s: no browser errors'%ctxname,errs[:3]);c.close()
    # duplicate requests: every battle asset URL requested once during Loading
    c,pg,errs=fresh(b);boot(pg,base);pg.reqs.clear();started(pg,"startRaiderBattle()");run_to_end(pg);settle(pg,1500)
    dup={u.split('/',3)[-1]:n for u,n in pg.reqs.items() if n>1 and u.endswith('.png')}
    check(not dup,'one network request per image URL (no duplicate request)',dup)
    dcs={u:n for u,n in pg.evaluate('__dc').items() if n>1}
    check(not dcs,'one decode per URL for the shared idle/motion/still assets',dcs);c.close()
    # cached: a second battle after the first
    c,pg,errs=fresh(b);boot(pg,base);started(pg,"startRaiderBattle()");run_to_end(pg);settle(pg,2600)
    pg.evaluate("BattleActorState.end('raider');BattleActorState.end('raider','fiona');BattleActorState.end('raider','lou');BattleActorState.end('raider','goblin_raider');BattleLoading.cancel();document.body.classList.remove('battleMode','raiderBattleMode');document.getElementById('raiderBattle').style.display='none'")
    pg.reqs.clear();started(pg,"startRaiderBattle()");run_to_end(pg);s=pg.evaluate(ST)
    check(s['last']['state']=='ready' and 395<=s['last']['shownMs']<=700,'cached second battle: Loading is the minimum only',s['last'])
    check(not [u for u in pg.reqs if u.endswith('.png')],'cached second battle: no image re-requested',[u for u in pg.reqs if u.endswith('.png')][:3]);c.close()
    # transient decode failure
    c,pg,errs=fresh(b);boot(pg,base);pg.evaluate("window.__rule={re:/idle\\/fiona_idle_0[1-3]|idle_v2\\/aidan_idle_0[1-2]/,times:1};window.__dc={}")
    started(pg,"startRaiderBattle()");run_to_end(pg);s=pg.evaluate(ST);settle(pg,2200)
    check(s['last']['state']=='ready' and not s['last']['failed'],'transient decode failure -> retried during Loading, ready',s['last'])
    cv=pg.evaluate("[...document.querySelectorAll('canvas.battle-idle-canvas')].filter(c=>!c.hidden).length");check(cv>=2,'transient decode failure: canvases shown after the battle starts',cv)
    check(not errs,'transient decode failure: no browser errors',errs[:3]);c.close()
    # permanent decode failure of one idle frame: bounded, fallback, battle still starts
    c,pg,errs=fresh(b);boot(pg,base);pg.evaluate("BattleLoading.setLimits({maxMs:5000});window.__rule={re:/idle\\/fiona_idle_04/,times:99};window.__dc={}")
    t=time.time();started(pg,"startRaiderBattle()");ok=run_to_end(pg,9000);el=time.time()-t;pg.wait_for_timeout(300)
    s=pg.evaluate(ST)
    check(ok and s['last']['state']=='failed' and s['last']['fallback'] and any('fiona_idle_04' in f for f in s['last']['failed']),'permanent decode failure -> fallback after bounded attempts',(round(el,2),s['last']))
    check(pg.evaluate(MODE)=='raider','permanent decode failure: battle still starts (no permanent stop)')
    check([e['phase'] for e in pg.evaluate('__bl')]==['start','fallback'],'permanent decode failure: events start->fallback',[e['phase'] for e in pg.evaluate('__bl')]);c.close()
    # 404 image
    c,pg,errs=fresh(b);boot(pg,base)
    pg.route('**/aidan_battle_idle.png',lambda r:r.fulfill(status=404,body='no'))
    started(pg,"startAttackBattle('northGob1',180)");ok=run_to_end(pg,9000);s=pg.evaluate(ST);pg.wait_for_timeout(300)
    check(ok and s['last']['state']=='failed' and any('aidan_battle_idle.png' in f for f in s['last']['failed']),'404 still -> fallback, battle starts',s['last'])
    check(pg.evaluate(MODE)=='normal','404: battle scene started');c.close()
    # timeout: assets that never arrive
    c,pg,errs=fresh(b);boot(pg,base);pg.evaluate("BattleLoading.setLimits({maxMs:1500})")
    pg.route('**/idle/fiona_idle_05.png',lambda r:None)
    t=time.time();started(pg,"startRaiderBattle()");ok=run_to_end(pg,6000);el=time.time()-t;s=pg.evaluate(ST);pg.wait_for_timeout(300)
    check(ok and 1.4<=el<=2.4 and s['last']['state']=='failed' and s['last']['reason']=='timeout','timeout -> fallback at the hard limit',(round(el,2),s['last']))
    check(pg.evaluate(MODE)=='raider','timeout: battle started anyway');c.close()
    # same battle requested twice while preparing: one run; different battle: old one cancelled
    c,pg,errs=fresh(b);boot(pg,base);started(pg,"startRaiderBattle();startRaiderBattle()");pg.wait_for_timeout(100)
    check(pg.evaluate('BattleLoading.status.runs')==1,'duplicate trigger while preparing is ignored',pg.evaluate('BattleLoading.status.runs'))
    run_to_end(pg);settle(pg,1500)
    if os.getenv('NEG')=='1':pg.evaluate("dispatchEvent(new CustomEvent('battle-opening',{detail:{}}))")     # negative control: a double battle start
    check(pg.evaluate("document.querySelectorAll('canvas.battle-idle-canvas').length")>=2 and pg.evaluate("window.__open")==1,'duplicate trigger: single battle start (exactly one opening)',pg.evaluate("window.__open"));
    check([e['phase'] for e in pg.evaluate('__bl')]==['start','ready'],'duplicate trigger: one start/ready',[e['phase'] for e in pg.evaluate('__bl')]);c.close()
    if os.getenv('NEG_STOP')=='1':print('FAILS',fails);sys.exit(1 if fails else 0)     # negative-control runs stop right after the checked condition
    c,pg,errs=fresh(b);boot(pg,base);started(pg,"startAttackBattle('northGob1',180)");pg.wait_for_timeout(120);pg.evaluate("startRaiderBattle()")
    run_to_end(pg);pg.wait_for_timeout(300);ph=[e['phase'] for e in pg.evaluate('__bl')]
    check(ph==['start','cancelled','start','ready'] and pg.evaluate(MODE)=='raider','superseded Loading is cancelled and never starts its battle',(ph,pg.evaluate(MODE)));c.close()
    # cancel (page transition) and another battle beginning underneath
    c,pg,errs=fresh(b);boot(pg,base);started(pg,"startRaiderBattle()");pg.wait_for_timeout(120);pg.evaluate("BattleLoading.cancel('test')");pg.wait_for_timeout(1500)
    check(pg.evaluate(MODE) is None and not pg.evaluate("document.body.classList.contains('battleLoading')") and pg.evaluate("getComputedStyle(document.getElementById('battleLoading')).display")=='none','cancel: overlay gone, battle not started')
    c.close()
    # no Loading leftover after a battle; Loading stays away from battle end
    c,pg,errs=fresh(b);boot(pg,base);started(pg,"startAttackBattle('northGob1',180)");run_to_end(pg);settle(pg,1500)
    check(not pg.evaluate("document.body.classList.contains('battleLoading')") and not pg.evaluate('BattleLoading.active'),'in battle: Loading not present');c.close()
    # viewports + rotation: the overlay covers the viewport in every size, also across a rotation
    for vp in ((360,640),(390,844),(412,915),(844,390),(915,412),(1280,720),(1920,1080)):
        for call,name in (("startAttackBattle('northGob1',180)",'normal'),("startRaiderBattle()",'raider')):
            c,pg,errs=fresh(b,vp);boot(pg,base,900);pg.evaluate("BattleLoading.setLimits({minMs:2600})");started(pg,call);pg.wait_for_timeout(450)
            g=pg.evaluate("(()=>{const r=document.getElementById('battleLoading').getBoundingClientRect();const k=document.querySelector('#battleLoading .blText').getBoundingClientRect();return {w:r.width,h:r.height,x:r.x,y:r.y,tx:k.x>=0&&k.right<=innerWidth,ty:k.y>=0&&k.bottom<=innerHeight,vw:innerWidth,vh:innerHeight}})()")
            check(g['w']==vp[0] and g['h']==vp[1] and g['x']==0 and g['y']==0 and g['tx'] and g['ty'],'%s %dx%d: overlay fills the viewport, text in view'%(name,*vp),g)
            out=os.getenv('BL_SHOTS')
            if out:os.makedirs(out,exist_ok=True);pg.screenshot(path='%s/loading_%s_%dx%d.png'%(out,name,*vp))
            if vp==(390,844):
                pg.set_viewport_size({'width':844,'height':390});pg.wait_for_timeout(120)
                g=pg.evaluate("(()=>{const r=document.getElementById('battleLoading').getBoundingClientRect();return [r.width,r.height,BattleLoading.status.state]})()")
                check(g[0]==844 and g[1]==390 and g[2]=='preparing','rotation while Loading: overlay keeps covering',g)
            run_to_end(pg);pg.wait_for_timeout(1900)
            if out:pg.screenshot(path='%s/battle_%s_%dx%d.png'%(out,name,*vp))
            check(not errs,'%s %dx%d: no browser errors'%(name,*vp),errs[:2]);c.close()
    b.close()
print('FAILS',fails)
sys.exit(1 if fails else 0)
