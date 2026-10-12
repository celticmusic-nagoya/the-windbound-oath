# リーフィボア: 戦闘(静止画/idle4コマ/モーション)、街道の突進AI(alert→windup→rush直線→recover→return)、側方回避、壁で突進停止、接触→既存戦闘1回、撃破後消滅・再入場復活。 needs http.server (PORT env)
import os, sys
from playwright.sync_api import sync_playwright
PORT=os.environ.get('PORT','8765'); fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
ROAD='road_dunvall_capital_01'
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:%s/index.html'%PORT); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=9;enterMossForest()"); pg.wait_for_timeout(2500)
    ev("(()=>{window.__starts=0;const _s=startAttackBattle;window.startAttackBattle=function(){window.__starts++;return _s.apply(this,arguments)};return 1})()")
    ev("""window.__rec=[];window.__bad=0;(function loop(){const f=MossForest.feet;for(const m of MossForest.monsters){window.__rec.push({id:m.id,s:m.state,x:m.x,y:m.y,d:Math.hypot(f.x-m.x,f.y-m.y),t:performance.now(),src:m.el.dataset.src||''});if(MossForest.blocked(m.x,m.y))window.__bad++;}
      if(window.__rec.length>20000)window.__rec.splice(0,10000);requestAnimationFrame(loop)})()""")
    put=lambda x,y: ev("MossForest.teleportFeet(%d,%d)"%(x,y))
    def states(i):
        out=[]
        for x in ev("window.__rec.filter(x=>x.id==='%s')"%i):
            if not out or out[-1]!=x['s']: out.append(x['s'])
        return out
    def setup(defs):
        ev("MossForest.enter({map:'%s',spawn:'from_fort'})"%ROAD); pg.wait_for_timeout(1500)
        ev("(d)=>{MossForest.map.monsters=d}",defs); ev("MossForest.enter({map:'%s',spawn:'from_fort'})"%ROAD); pg.wait_for_timeout(1800)
        ev("window.__rec.length=0;window.__bad=0")
    # 1) art
    paths=ev("Object.values(BATTLE_ASSETS.leafy_boar)")
    sizes=ev("(ps)=>Promise.all(ps.map(u=>new Promise(r=>{const i=new Image();i.onload=()=>r([i.naturalWidth,i.naturalHeight]);i.onerror=()=>r(null);i.src=u;})))",paths)
    check(len(paths)==5 and all(s==[480,400] for s in sizes),'5 battle stills load on one canvas %s'%sizes[:1])
    check(all(ev("(s)=>BattleMotion.has('leafy_boar',s)",s) for s in ('attack','damage','ko')),'attack / damage / ko motions registered')
    fr=ev("Promise.all(Array.from({length:11},(_,i)=>new Promise(r=>{const im=new Image();im.onload=()=>r([im.naturalWidth,im.naturalHeight]);im.onerror=()=>r(null);im.src='img/field/monsters/leafy_boar/leafy_boar_'+String(i+1).padStart(2,'0')+'.png';})))")
    check(all(s==[240,160] for s in fr),'11 field frames load')
    # 2) road placement
    ev("MossForest.enter({map:'%s',spawn:'from_fort'})"%ROAD); pg.wait_for_timeout(2500)
    L=ev("MossForest.monsters.map(m=>[m.id,m.type,m.x,m.y,MossForest.blocked(m.x,m.y)])")
    check(len(L)==6 and all(m[1]=='leafy_boar' and not m[4] for m in L),'road has 6 leafy boars on walkable ground %s'%[m[0] for m in L])
    check(ev("MossForest.map.transitions.every(t=>MossForest.monsters.every(m=>Math.hypot(m.x-(t.rect.x+t.rect.w/2),m.y-(t.rect.y+t.rect.h/2))>600))"),'boars keep away from both road exits')
    ev("MossForest.enter({map:'%s',spawn:'from_fort'})"%ROAD); pg.wait_for_timeout(1500)
    CX=ev("(()=>{for(let x=1900;x<2700;x+=20){let ok=true;for(let y=1100;y<=1700&&ok;y+=10)for(const dx of [-40,0,40])if(MossForest.blocked(x+dx,y)){ok=false;break;}if(ok)return x;}return null})()")
    check(CX is not None,'found a prop-free column for the dash tests (x=%s)'%CX)
    # 3) rush: straight line, sidestep avoids it, then recover -> return -> wander
    setup([{"id":"t_boar","type":"leafy_boar","x":CX,"y":1300}])
    h=(CX,1300); put(CX,1300+300); pg.wait_for_timeout(1250)
    put(CX+260,1300+300)       # sidestep once the dash has started (its direction was locked at the end of the windup)
    pg.wait_for_timeout(3600)
    st=states('t_boar'); check(st[:4]==['wander','alert','windup','rush'] and 'recover' in st and ev("window.__starts")==0,'alert -> windup -> rush; sidestepping the locked dash avoids the fight %s'%st)
    r=[x for x in ev("window.__rec.filter(x=>x.id==='t_boar'&&x.s==='rush')")]
    if len(r)>10:
        import math
        a=(r[0]['x'],r[0]['y']); z=(r[-1]['x'],r[-1]['y']); L2=math.dist(a,z)
        dev=max(abs((z[0]-a[0])*(a[1]-q['y'])-(a[0]-q['x'])*(z[1]-a[1]))/max(1,L2) for q in r)
        sp=L2/((r[-1]['t']-r[0]['t'])/1000)
        check(dev<6,'dash is a straight line (max deviation %.1f px)'%dev); check(220<sp<330,'dash speed ~280px/s (%.0f)'%sp); check(L2<=480,'dash length <= ~460 (%.0f)'%L2)
    put(CX-900,1300+300); pg.wait_for_timeout(9000)
    st=states('t_boar'); check('return' in st and st[-1]=='wander','after recovering it walks home and idles %s'%st)
    check(len(ev("[...new Set(window.__rec.filter(x=>x.id==='t_boar').map(x=>x.src))]"))>=5,'several distinct poses were drawn')
    check(ev("window.__bad")==0,'never inside a blocker')
    # 4) a wall ends the dash early (dash north into the forest wall)
    setup([{"id":"t_wall","type":"leafy_boar","x":3680,"y":1200}])   # south of the hill's cliff face; the player stands on the hilltop behind it
    put(3680,985); ev("window.__rec.length=0"); pg.wait_for_timeout(3200)
    r=ev("window.__rec.filter(x=>x.id==='t_wall'&&x.s==='rush')"); st=states('t_wall')
    d=max([abs(q['y']-r[0]['y']) for q in r]) if r else 0
    check('recover' in st and d<200 and ev("window.__bad")==0,'dash into the cliff stops early (%s, %.0f px) and never enters it'%(st[:5],d))
    # 5) contact -> exactly one battle, one boar
    ev("closeDialogue()")
    setup([{"id":"t_boar","type":"leafy_boar","x":CX,"y":1300}])
    put(CX,1300+200)
    for i in range(60):
        if ev("document.body.classList.contains('normalBattleMode')"): break
        pg.wait_for_timeout(100)
    pg.wait_for_timeout(2000)
    check(ev("currentGoblin")=='leafyBoar1' and ev("window.__starts")==1,'rush contact starts the existing battle once (%s, %d)'%(ev("currentGoblin"),ev("window.__starts")))
    en=ev("PrologueCombat.enemies.normal.map(e=>[e.type,e.hp,e.maxHp])"); check(en==[['leafy_boar',70,70]],'one leafy boar (70 HP) %s'%en)
    check('リーフィボア' in ev("document.querySelector('#v2EnemyName').textContent"),'enemy name shows リーフィボア')
    pg.wait_for_timeout(2500); fr=set()
    for i in range(30):
        fr.add(ev("BattleIdleMotion.status.actors.find(a=>a.actor==='leafy_boar'&&a.showing)?.frame")); pg.wait_for_timeout(250)
    check(len([f for f in fr if f is not None])>=2,'idle frames advance %s'%sorted(f for f in fr if f is not None))
    check(not ev("BattleIdleMotion.status.actors.some(a=>a.actor==='forest_bat'&&a.showing)"),'no bat idle canvas leaks into the boar battle')
    ev("(()=>{const e=PrologueCombat.enemies.normal[0];e.hp=15;PrologueCombat.sync('normal');})()"); pg.wait_for_timeout(600)
    check('low_hp' in ev("document.querySelector('#bGob img').getAttribute('src')"),'low-HP still is shown at <=30% HP')
    # 6) win -> gone, forestShow no respawn, re-entry respawn
    gold0=ev("gold")
    ev("PrologueCombat.instantKill('normal')"); pg.wait_for_timeout(2600)
    check('EXP +9' in ev("document.querySelector('#resultExp').textContent") and ev("gold")-gold0==5,'result: EXP +9, GOLD +5')
    for i in range(8):
        if ev("getComputedStyle(document.querySelector('#battleResult')).display")=='none': break
        ev("(document.querySelector('#battleResult button')||document.querySelector('#battleResult')).click()"); pg.wait_for_timeout(500)
    pg.wait_for_timeout(1200)
    check(ev("forestActive") and ev("MossForest.monsters.length")==0,'back in the forest; the boar is gone')
    ev("forestShow()"); pg.wait_for_timeout(600); check(ev("MossForest.monsters.length")==0,'forestShow() does not respawn it')
    check(ev("PrologueProgress.count()")==0 and ev("storyStage")==9,'story progress untouched')
    ev("MossForest.enter({map:'moss_forest_03_ancient_grove',spawn:'from_area2'})"); pg.wait_for_timeout(2000)
    ev("MossForest.enter({map:'%s',spawn:'from_fort'})"%ROAD); pg.wait_for_timeout(2500)
    check(ev("MossForest.monsters.map(m=>m.id)")==['t_boar'],'re-entering the road respawns the defeated boar')
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)
