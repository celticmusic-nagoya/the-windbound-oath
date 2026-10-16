"""BL-01 input freeze + safety, with Loading ENABLED (real battle-start path): touch/mouse/keyboard/gamepad frozen while preparing and normal afterwards,
timeout fallback keeps COMMAND usable, stale/cancelled/late work never starts a battle, test-only bypass cannot be enabled by accident."""
import os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail)
    if not ok:fails.append(name)
INIT="""(()=>{window.__bl=[];addEventListener('battle-loading',e=>__bl.push(Object.assign({t:Math.round(performance.now())},e.detail)));window.__open=0;addEventListener('battle-opening',()=>__open++);
 window.__kd=0;const add=EventTarget.prototype.addEventListener;
 EventTarget.prototype.addEventListener=function(t,f,o){if(t==='keydown'&&(this===window||this===document)&&typeof f==='function'&&f.name!=='swallowKey'){const g=function(){__kd++;return f.apply(this,arguments)};return add.call(this,t,g,o)}return add.call(this,t,f,o)};
 window.__fail=null;const dec=HTMLImageElement.prototype.decode;HTMLImageElement.prototype.decode=function(){if(window.__fail&&window.__fail.test(this.src))return Promise.reject(new DOMException('x','EncodingError'));return dec.call(this)};
 window.__pads=[{id:'fake',index:0,connected:true,buttons:[{pressed:false,value:0},{pressed:false,value:0}],axes:[0,0]}];navigator.getGamepads=()=>window.__pads;
 window.__seen=[];(function poll(){const p=navigator.getGamepads()[0];window.__seen.push(p?(p.buttons[0].pressed?1:0):-1);requestAnimationFrame(poll)})();
})()"""
def fresh(b,vp=(844,390),touch=False):
    c=b.new_context(viewport={'width':vp[0],'height':vp[1]},device_scale_factor=2,has_touch=touch);c.add_init_script(INIT);pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append('pageerror:'+str(e)));pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None)
    return c,pg,errs
def boot(pg,base,wait=1200):
    pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat&&window.BattleLoading');pg.wait_for_timeout(wait);pg.evaluate('closeDialogue()')
MODE="document.body.classList.contains('raiderBattleMode')?'raider':document.body.classList.contains('normalBattleMode')?'normal':null"
def wait_end(pg,limit=9000):
    t=time.time()
    while time.time()-t<limit/1000:
        if not pg.evaluate('BattleLoading.active'):return True
        pg.wait_for_timeout(40)
    return False
def pad(pg,down):pg.evaluate("window.__pads[0].buttons[0]={pressed:%s,value:%d}"%('true' if down else 'false',1 if down else 0))
EXE=os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None
with server(8817) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE)
    for kind,call,act in (('normal',"startAttackBattle('northGob1',180)","chooseNormalAct('attack','normal_enemy_0')"),('raider',"startRaiderBattle()","choosePartyAct('guard')")):
        c,pg,errs=fresh(b,touch=True);boot(pg,base)
        kd0=pg.evaluate('__kd');pg.evaluate('BattleLoading.setLimits({minMs:3500})');pg.evaluate(call);pg.wait_for_timeout(80)
        check(pg.evaluate('BattleLoading.frozen')==True,'%s: frozen while preparing'%kind)
        # keyboard (a Bluetooth pad on Android arrives as these keys)
        for k in ('Enter','Space','Escape','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','z','x','Tab'):pg.keyboard.press(k)
        check(pg.evaluate('__kd')==kd0,'%s: no page key listener ran for Enter/Space/Esc/arrows/z/x/Tab during Loading'%kind,(kd0,pg.evaluate('__kd')))
        # mouse + touch: the overlay is what is hit, everywhere on screen
        pts=[(x,y) for x in (20,200,422,640,820) for y in (20,120,195,300,370)]
        hit=pg.evaluate("(pts)=>pts.every(([x,y])=>{const e=document.elementFromPoint(x,y);return e&&!!e.closest('#battleLoading')})",pts)
        check(hit,'%s: every screen point hits the Loading overlay (mouse/touch cannot reach the game)'%kind)
        pg.mouse.click(422,195);pg.touchscreen.tap(422,300);pg.mouse.click(800,360)
        check(pg.evaluate(MODE) is None and pg.evaluate('BattleLoading.status.state')=='preparing','%s: clicks/taps during Loading do nothing'%kind)
        # gamepad: poller sees no pad while frozen
        pad(pg,True);pg.wait_for_timeout(200)
        seen=pg.evaluate('__seen.slice(-8)')
        check(all(v==-1 for v in seen),'%s: gamepad poller sees NO pad / no pressed button while Loading'%kind,seen)
        # still held across the end of Loading: stays masked, then a fresh press works
        pg.evaluate('BattleLoading.setLimits({minMs:0})');wait_end(pg);pg.wait_for_timeout(200)
        seen=pg.evaluate('__seen.slice(-8)')
        check(all(v==-1 for v in seen),'%s: button held through the end of Loading stays masked (no phantom press)'%kind,seen)
        pad(pg,False);pg.wait_for_timeout(120);pad(pg,True);pg.wait_for_timeout(120)
        seen=pg.evaluate('__seen.slice(-6)')
        check(all(v==1 for v in seen),'%s: after release, a new gamepad press is visible again (input restored)'%kind,seen);pad(pg,False)
        pg.wait_for_timeout(1800)
        check(pg.evaluate(MODE)==kind and not pg.evaluate('BattlePresentation.busy'),'%s: battle started, opening done, COMMAND unlocked'%kind)
        OBS="({actor:normalActor})" if kind=='normal' else "({actor:rbActor,acts:rbActs.length})"
        if os.getenv('NEG')=='1':pg.evaluate("window.chooseNormalAct=()=>{};window.choosePartyAct=()=>{}")    # negative control: the command silently does nothing
        st0=pg.evaluate(OBS);pg.evaluate(act);pg.wait_for_timeout(250)
        st1=pg.evaluate(OBS)
        # measured effect per battle kind (no escape clause): normal -> the turn passes from Aidan to Fiona; raider -> one more action is queued and Fiona is up
        exp=(st0['actor']=='aidan' and st1['actor']=='fiona') if kind=='normal' else (st0['actor']=='aidan' and st1['actor']=='fiona' and st1['acts']==st0['acts']+1)
        check(exp,'%s: a real command is accepted after Loading (its effect is measured)'%kind,(st0,st1))
        if os.getenv('NEG_STOP')=='1':print('FAILS',fails);sys.exit(1 if fails else 0)     # negative-control runs stop right after the checked condition
        kd1=pg.evaluate('__kd');pg.keyboard.press('ArrowDown');pg.keyboard.press('Enter')
        check(pg.evaluate('__kd')>kd1,'%s: keyboard reaches the game again after Loading'%kind)
        check(not errs,'%s: no browser errors'%kind,errs[:3]);c.close()
    # bypass: flag must be exactly true, set before load, local origin only
    for flag,name,exp in (("true",'true before load',True),("1",'number 1 (not exactly true)',False),("'true'",'string "true"',False)):
        c=b.new_context();c.add_init_script("window.WINDBOUND_NO_BATTLE_LOADING=%s"%flag);pg=c.new_page();pg.goto(base+'/index.html');pg.wait_for_function('window.BattleLoading')
        check(pg.evaluate('BattleLoading.bypassed')==exp,'bypass %s -> %s'%(name,exp),pg.evaluate('BattleLoading.bypassed'));c.close()
    c=b.new_context();pg=c.new_page();pg.goto(base+'/index.html');pg.wait_for_function('window.BattleLoading&&window.PrologueCombat');pg.evaluate("window.WINDBOUND_NO_BATTLE_LOADING=true")
    check(pg.evaluate('BattleLoading.bypassed')==False and pg.evaluate("BattleLoading.gate('normal','x',()=>{})")==True,'flag set after load has no effect (cannot flip mid-play)');pg.evaluate('BattleLoading.cancel()');c.close()
    # non-local origin: the flag is ignored even when true (served as example.test -> 127.0.0.1)
    port=base.rsplit(':',1)[1];b2=p.chromium.launch(executable_path=EXE,args=['--host-resolver-rules=MAP bl-test.example 127.0.0.1'])
    c=b2.new_context();c.add_init_script("window.WINDBOUND_NO_BATTLE_LOADING=true");pg=c.new_page();pg.goto('http://bl-test.example:%s/index.html'%port);pg.wait_for_function('window.BattleLoading')
    check(pg.evaluate('location.hostname')=='bl-test.example' and pg.evaluate('BattleLoading.bypassed')==False,'non-local host: bypass flag ignored even if true',pg.evaluate('[location.hostname,BattleLoading.bypassed]'));c.close();b2.close()
    # timeout fallback: COMMAND not locked, late arrival of the hung asset starts nothing, one battle only
    c,pg,errs=fresh(b);boot(pg,base);pg.evaluate("BattleLoading.setLimits({maxMs:1200})")
    held=[]
    def hold(route):held.append(route)
    pg.route('**/idle/fiona_idle_05.png',hold)
    pg.evaluate("window.__bl.length=0;window.__open=0;startRaiderBattle()");ok=wait_end(pg,5000);pg.wait_for_timeout(2000)
    check(ok and pg.evaluate('BattleLoading.status.last.state')=='failed','timeout: fell back at the limit',pg.evaluate('BattleLoading.status.last.reason'))
    check(pg.evaluate(MODE)=='raider' and not pg.evaluate('BattlePresentation.busy') and not pg.evaluate("document.body.classList.contains('battlePresentationBusy')"),'timeout: battle running, COMMAND not locked')
    pg.evaluate("choosePartyAct('guard')");pg.wait_for_timeout(150);check(pg.evaluate('rbActor')=='fiona','timeout: a command is accepted (Aidan guard -> Fiona turn)',pg.evaluate('rbActor'))
    for r in held:
        try:r.fulfill(path=str(ROOT/'img/battle/characters/fiona/idle/fiona_idle_05.png'))
        except Exception:pass
    pg.wait_for_timeout(1500)
    ph=[e['phase'] for e in pg.evaluate('__bl')]
    check(ph==['start','fallback'] and pg.evaluate('__open')==1,'late arrival of the hung asset starts nothing more (one start/fallback, one opening)',(ph,pg.evaluate('__open')))
    check(not pg.evaluate("document.body.classList.contains('battleLoading')"),'timeout: no leftover Loading class')
    check(not errs,'timeout: no browser errors',errs[:3]);c.close()
    # cancel, then the old assets finishing must not start the battle
    c,pg,errs=fresh(b);boot(pg,base)
    pg.evaluate("window.__bl.length=0;startAttackBattle('northGob1',180)");pg.wait_for_timeout(100);pg.evaluate("BattleLoading.cancel('test')");pg.wait_for_timeout(2500)
    check(pg.evaluate(MODE) is None and [e['phase'] for e in pg.evaluate('__bl')]==['start','cancelled'],'cancel: old Promise never starts the battle even after its assets finished',[e['phase'] for e in pg.evaluate('__bl')])
    pg.evaluate("window.__bl.length=0;startRaiderBattle()");wait_end(pg);pg.wait_for_timeout(300)
    check(pg.evaluate(MODE)=='raider' and [e['phase'] for e in pg.evaluate('__bl')]==['start','ready'],'after a cancel a new Loading works normally');c.close()
    # 404 / decode failure: substitute display
    c,pg,errs=fresh(b);boot(pg,base);pg.route('**/aidan_battle_idle.png',lambda r:r.fulfill(status=404,body='x'));pg.evaluate("startAttackBattle('northGob1',180)");wait_end(pg,9000);pg.wait_for_timeout(2400)
    sub=pg.evaluate("(()=>{const c=document.querySelector('#bAidan2 canvas.battle-idle-canvas');const i=document.querySelector('#bAidan2 img');return {canvas:!!c&&!c.hidden,iw:i.naturalWidth,fi:document.querySelector('#bFiona2 canvas.battle-idle-canvas')&&!document.querySelector('#bFiona2 canvas.battle-idle-canvas').hidden}})()")
    check(pg.evaluate(MODE)=='normal' and sub['canvas'] and sub['fi'],'404 still: battle runs; the 6-frame idle canvas substitutes for the missing still',sub);c.close()
    c,pg,errs=fresh(b);boot(pg,base);pg.evaluate("BattleLoading.setLimits({maxMs:5000});window.__fail=/idle\\/fiona_idle_04/")
    pg.evaluate("startRaiderBattle()");wait_end(pg,9000);pg.wait_for_timeout(2400)
    sub=pg.evaluate("(()=>{const i=document.querySelector('#rbFiona img');const c=document.querySelector('#rbFiona canvas.battle-idle-canvas');return {iw:i.naturalWidth,imgShown:getComputedStyle(i).visibility!=='hidden'&&getComputedStyle(i).display!=='none',canvasHidden:!c||c.hidden,last:BattleLoading.status.last.state}})()")
    check(pg.evaluate(MODE)=='raider' and sub['last']=='failed' and sub['iw']>0 and sub['imgShown'] and sub['canvasHidden'],'decode failure of one idle frame: the actor shows its still image instead (no blank), battle runs',sub)
    ba=pg.evaluate("BattleActorState.get('raider','fiona')");check(ba=='idle','decode failure: Fiona state is idle',ba);c.close()
    # consecutive battles with Loading enabled: normal -> raider -> normal
    c,pg,errs=fresh(b);boot(pg,base)
    def endbattle(kind):
        if kind=='normal':pg.evaluate("BattleActorState.end('normal');BattleActorState.end('normal','fiona');document.body.classList.remove('battleMode','normalBattleMode');document.getElementById('attackBattle').style.display='none'")
        else:pg.evaluate("for(const a of ['aidan','fiona','lou','goblin_raider'])BattleActorState.end('raider',a==='aidan'?undefined:a);document.body.classList.remove('battleMode','raiderBattleMode');document.getElementById('raiderBattle').style.display='none'")
        pg.evaluate("window.PrologueCombat&&0")
    seq=[]
    for kind,call in (('normal',"startAttackBattle('northGob1',180)"),('raider',"startRaiderBattle()"),('normal',"startAttackBattle('northGob2',180)")):
        pg.evaluate("window.__bl.length=0;attackBattleBusy=false;"+call);wait_end(pg);pg.wait_for_timeout(1700)
        seq.append((kind,pg.evaluate(MODE),[e['phase'] for e in pg.evaluate('__bl')],pg.evaluate('BattlePresentation.busy')));endbattle(kind);pg.wait_for_timeout(120)
    check(all(k==m and ph==['start','ready'] and not busy for k,m,ph,busy in seq),'consecutive battles normal->raider->normal each: Loading -> battle -> COMMAND free',seq)
    check(not pg.evaluate("document.body.classList.contains('battleLoading')"),'no Loading residue after the sequence');c.close()
    b.close()
print('FAILS',fails)
sys.exit(1 if fails else 0)
