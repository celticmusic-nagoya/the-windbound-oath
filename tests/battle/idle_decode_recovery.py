"""BattleIdleMotion frame loading: Image.decode() failure (EncodingError) must not be cached for good.
Transient failure -> canvas recovers by retry; persistent failure -> bounded attempts, no loop/throw, next battle re-arms; stale retries stop with the battle;
shared in-flight requests; one canvas per actor; clean loads stay single-attempt."""
import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail)
    if not ok:fails.append(name)
INIT="""(()=>{const d=HTMLImageElement.prototype.decode;window.__dc={};window.__rule=null;
 HTMLImageElement.prototype.decode=function(){const u=this.src.split('/').slice(-2).join('/').split('?')[0];__dc[u]=(__dc[u]||0)+1;
  const r=window.__rule;if(r&&r.re.test(u)&&__dc[u]<=r.times)return Promise.reject(new DOMException('The source image cannot be decoded.','EncodingError'));return d.call(this)}})()"""
CANV="document.querySelectorAll(%r).length"
A='#rbAidan canvas.battle-idle-canvas';F='#rbFiona canvas.battle-idle-canvas'
def fresh(b,rule=None,vp=(844,390)):
    c=b.new_context(viewport={'width':vp[0],'height':vp[1]},device_scale_factor=3);c.add_init_script(INIT);pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append('pageerror:'+str(e)));pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' else None)
    return c,pg,errs
def boot(pg,base,rule=None):
    pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat');pg.wait_for_timeout(1500);pg.evaluate('closeDialogue()')
    if rule:pg.evaluate("(r)=>{window.__rule={re:new RegExp(r.re),times:r.times};window.__dc={}}",rule)
STAT="BattleIdleMotion.status.actors.filter(a=>a.context==='raider'&&(a.actor==='aidan'||a.actor==='fiona')).map(a=>[a.actor,a.loadAttempts,a.loadFailed,a.showing])"
with server(8817) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    # 1 clean load: single attempt, one decode per URL, one canvas per actor, shown quickly
    c,pg,errs=fresh(b);boot(pg,base);pg.evaluate('startRaiderBattle()');pg.wait_for_timeout(2600)
    r=pg.evaluate("({a:%s,f:%s,st:%s,dc:Object.entries(__dc).filter(([u])=>/idle_v2|idle\\/fiona_idle_0/.test(u)).map(([u,n])=>n)})"%(CANV%A,CANV%F,STAT))
    check(r['a']==1 and r['f']==1,'clean load: one canvas per actor',r)
    check(all(s[1]==1 and not s[2] and s[3] for s in r['st']),'clean load: single attempt, shown',r['st'])
    check(r['dc'] and max(r['dc'])==1,'clean load: each idle frame decoded once (in-flight/cached sharing)',r['dc'])
    check(not errs,'clean load: no console/page errors',errs);c.close()
    # 2 transient failure: first decode of every Aidan/Fiona idle frame rejects -> recovers by retry
    c,pg,errs=fresh(b);boot(pg,base,{'re':'idle_v2/aidan_idle|idle/fiona_idle_0','times':1});pg.evaluate('startRaiderBattle()');pg.wait_for_timeout(3500)
    r=pg.evaluate("({a:%s,f:%s,st:%s,dc:Object.entries(__dc).filter(([u])=>/idle_v2|idle\\/fiona_idle_0/.test(u)).map(([u,n])=>n)})"%(CANV%A,CANV%F,STAT))
    check(r['a']==1 and r['f']==1 and all(s[3] for s in r['st']),'transient decode failure: canvases recovered, exactly one per actor',r)
    check(all(2<=s[1]<=4 and not s[2] for s in r['st']),'transient decode failure: retried (2..4 attempts), not marked failed',r['st'])
    check(max(r['dc'])<=2,'transient decode failure: failed frames re-requested once, not duplicated',r['dc'])
    check(not errs,'transient decode failure: no console/page errors',errs);c.close()
    # 3 persistent failure of Aidan's frame 3: bounded attempts, no throw, other actor unaffected; then next battle re-arms and recovers
    c,pg,errs=fresh(b);boot(pg,base,{'re':'idle_v2/aidan_idle_03','times':9999});pg.evaluate('startRaiderBattle()');pg.wait_for_timeout(5000)
    r=pg.evaluate("({a:%s,f:%s,st:%s,n3:__dc['idle_v2/aidan_idle_03.png']})"%(CANV%A,CANV%F,STAT))
    ai=[s for s in r['st'] if s[0]=='aidan'][0];fi=[s for s in r['st'] if s[0]=='fiona'][0]
    check(r['a']==0 and ai[2] and ai[1]==4,'persistent failure: gives up after exactly 4 attempts, marked failed, no canvas',r)
    check(r['f']==1 and fi[3],'persistent failure: Fiona unaffected',r)
    pg.wait_for_timeout(3000);n3=pg.evaluate("__dc['idle_v2/aidan_idle_03.png']")
    check(n3==r['n3'] and n3<=4,'persistent failure: no further retries (no loop)',(r['n3'],n3))
    check(not errs,'persistent failure: no console/page errors (a warning is logged)',errs)
    pg.evaluate("window.__rule=null;PrologueCombat.cancel()");pg.wait_for_timeout(300);pg.evaluate('startRaiderBattle()');pg.wait_for_timeout(3000)
    r=pg.evaluate("({a:%s,f:%s,st:%s})"%(CANV%A,CANV%F,STAT))
    check(r['a']==1 and r['f']==1 and all(s[3] for s in r['st']),'next battle re-arms the failed asset: canvas recovers once the image is loadable',r)
    c.close()
    # 4 stale: battle ends while retries are pending -> retries stop, nothing shows in the next battle from the old load
    c,pg,errs=fresh(b);boot(pg,base,{'re':'idle_v2/aidan_idle_03','times':9999});pg.evaluate('startRaiderBattle()');pg.wait_for_timeout(900)
    pg.evaluate("PrologueCombat.cancel();for(const a of [undefined,'fiona','lou','goblin_raider'])BattleActorState.end('raider',a)");pg.wait_for_timeout(300);n0=pg.evaluate("__dc['idle_v2/aidan_idle_03.png']");pg.wait_for_timeout(3500)
    n1=pg.evaluate("__dc['idle_v2/aidan_idle_03.png']");r=pg.evaluate("({a:%s,st:%s})"%(CANV%A,STAT))
    check(n1<=n0 and r['a']==0,'battle ended mid-retry: pending retries stop and nothing is shown',(n0,n1,r))
    pg.evaluate("window.__rule=null");pg.evaluate('startRaiderBattle()');pg.wait_for_timeout(3000);r=pg.evaluate("({a:%s,f:%s})"%(CANV%A,CANV%F))
    check(r['a']==1 and r['f']==1,'next battle after the aborted retry works with one canvas each',r)
    check(not errs,'stale: no console/page errors',errs);c.close()
    # 5 normal battle context uses the same shared load (no duplicate canvas / decode)
    c,pg,errs=fresh(b,vp=(1280,720));boot(pg,base,{'re':'idle_v2/aidan_idle|idle/fiona_idle_0','times':1});pg.evaluate("startAttackBattle('attackGob1',100)");pg.wait_for_timeout(3500)
    r=pg.evaluate("({a:document.querySelectorAll('#bAidan2 canvas.battle-idle-canvas').length,f:document.querySelectorAll('#bFiona2 canvas.battle-idle-canvas').length,show:BattleIdleMotion.status.actors.filter(a=>a.context==='normal'&&(a.actor==='aidan'||a.actor==='fiona')).map(a=>a.showing)})")
    check(r['a']==1 and r['f']==1 and all(r['show']),'normal battle with a transient decode failure: recovered, one canvas each',r)
    check(not errs,'normal: no console/page errors',errs);c.close()
    b.close()
print('FAILS',fails);sys.exit(1 if fails else 0)
