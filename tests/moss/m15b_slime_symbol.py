# FieldMonsters: モススライム／ゴブリンのシンボルエンカウント(AI: wander/alert/chase/return、collision、接触→既存戦闘、撃破後消滅・再入場で復活)。 needs http.server (PORT env)
import os, sys
from playwright.sync_api import sync_playwright
PORT=os.environ.get('PORT','8765'); fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
A1='moss_forest_01_sunlit_path'
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:%s/index.html'%PORT); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=9;enterMossForest()"); pg.wait_for_timeout(2500)
    ev("(()=>{window.__starts=0;const _s=startAttackBattle;window.startAttackBattle=function(){window.__starts++;return _s.apply(this,arguments)};return 1})()")
    # recorder: state / position / blocked per frame for every monster (invariants are checked over the whole run)
    ev("""window.__rec=[];window.__bad=0;(function loop(){const L=MossForest.monsters;for(const m of L){const f=MossForest.feet;window.__rec.push({id:m.id,s:m.state,x:m.x,y:m.y,d:Math.hypot(f.x-m.x,f.y-m.y),t:performance.now(),src:m.el.dataset.src||''});if(MossForest.blocked(m.x,m.y))window.__bad++;}
      if(window.__rec.length>20000)window.__rec.splice(0,10000);requestAnimationFrame(loop)})()""")
    def setup(defs,spawn='from_lind'):
        ev("(d)=>{MossForest.map&&0;}",defs)
        ev("(d)=>{window.__defs=d}",defs)
        ev("MossForest.enter({map:'%s',spawn:'%s'})"%(A1,spawn)); pg.wait_for_timeout(1800)
        ev("(d)=>{MossForest.map.monsters=d}",defs); ev("MossForest.enter({map:'%s',spawn:'%s'})"%(A1,spawn)); pg.wait_for_timeout(1800)
        ev("window.__rec.length=0;window.__bad=0")
    def states(i=0):
        r=ev("window.__rec.filter(x=>x.id==='%s')"%i); out=[]
        for x in r:
            if not out or out[-1]!=x['s']: out.append(x['s'])
        return out
    def put(fx,fy): ev("MossForest.teleportFeet(%d,%d)"%(fx,fy))
    # ---- 1) shipped A1 map: two slimes, placed off the main road, not in blockers
    ev("MossForest.enter({map:'%s',spawn:'from_lind'})"%A1); pg.wait_for_timeout(2500)
    L=ev("MossForest.monsters.filter(m=>m.type==='moss_slime').map(m=>[m.id,m.type,m.state,m.x,m.y])")
    L=[m for m in L if m[1]=='moss_slime']; check(len(L)==6,'A1 shows 6 moss slimes %s'%[m[0] for m in L])
    check(ev("MossForest.monsters.every(m=>!MossForest.blocked(m.x,m.y))"),'slime homes are on walkable ground')
    check(ev("document.querySelectorAll('.forest-monster').length")==18,'18 monster elements in the DOM (A1: 6 slimes, 6 boars, 6 goblins)')
    check(ev("FieldMonsters.MONSTER_TYPES.moss_slime.art.frames")==6,'slime uses the 6-frame walk')
    check(ev("MossForest.encounters()")==False,'random step encounters are off')
    sp=ev("MossForest.map.spawns.points.from_lind"); main_close=min(abs(m[3]-sp['x'])+abs(m[4]-sp['y']) for m in L)
    check(main_close>1500,'slimes are not at the arrival point (%d)'%main_close)
    # ---- 2) wander (player far away): moves within wanderRadius around home, stays in wander
    put(1520-700,3590-300); ev("window.__rec.length=0"); pg.wait_for_timeout(9000)
    r=ev("window.__rec.filter(x=>x.id==='a1_slime_hollow')"); xs=[(x['x'],x['y']) for x in r]; home=(1520,3590)
    mx=max(((x-home[0])**2+(y-home[1])**2)**.5 for x,y in xs); mv=max(abs(x-xs[0][0])+abs(y-xs[0][1]) for x,y in xs)
    check(mv>8 and mx<=130,'wander: drifts around home (moved %.0f, max %.0f from home)'%(mv,mx))
    check(set(x['s'] for x in r)=={'wander'},'wander: stays in wander while the player is far')
    # ---- 3) alert -> chase; 6 walk frames
    h=ev("(()=>{const m=MossForest.monsters[0];return [m.x,m.y]})()")
    put(round(h[0]-230),round(h[1])); ev("window.__rec.length=0"); pg.wait_for_timeout(1000)
    st=states('a1_slime_hollow'); check(st[:3]==['wander','alert','chase'] or st[:2]==['alert','chase'],'in detect range: alert then chase %s'%st)
    pg.wait_for_timeout(2500)
    srcs=ev("[...new Set(window.__rec.filter(x=>x.id==='a1_slime_hollow'&&x.s==='chase').map(x=>x.src))]")
    check(len(srcs)==6,'chasing slime cycles all 6 walk frames (%d)'%len(srcs))
    # slime speed ~45
    r=ev("window.__rec.filter(x=>x.id==='a1_slime_hollow'&&x.s==='chase')")
    if len(r)>20:
        dd=((r[-1]['x']-r[0]['x'])**2+(r[-1]['y']-r[0]['y'])**2)**.5/((r[-1]['t']-r[0]['t'])/1000); check(30<dd<60,'slime chase speed ~45px/s (%.0f)'%dd)
    # ---- 4) escape + return: player runs away; slime gives up, goes home, becomes wander; never touched
    put(round(h[0]-700),round(h[1])); pg.wait_for_timeout(9000)
    st=states('a1_slime_hollow'); check('return' in st and st[-1]=='wander','after the player leaves: return -> wander %s'%st)
    hm=ev("(()=>{const m=MossForest.monsters[0];return Math.hypot(m.x-m.home[0],m.y-m.home[1])})()")
    check(hm<=140,'slime is back near home (%.0f)'%hm)
    check(ev("window.__starts")==0 and not ev("document.body.classList.contains('normalBattleMode')"),'no battle while the player only approached and left')
    check(ev("window.__bad")==0,'monster never stood inside a blocker')
    # ---- 5) the player can outrun a chasing slime (walk away at normal pace)
    # The earlier wander position is random; its x-700/y-100 destination
    # can land inside scenery. Choose a clear straight retreat from the current
    # slime position, then test the same normal movement and 5-second gap.
    escape=ev("""(()=>{const m=MossForest.monsters.find(m=>m.id==='a1_slime_hollow');
      for(let i=0;i<72;i++){const a=i*Math.PI/36,c=Math.cos(a),s=Math.sin(a);
        const point=r=>[Math.round(m.x+r*c),Math.round(m.y+r*s)];let clear=true;
        for(let r=200;r<=700;r+=4){const [x,y]=point(r);if(MossForest.blocked(x,y)){clear=false;break;}}
        if(clear)return {start:point(200),goal:point(700)};
      }return null;})()""")
    check(escape is not None,'escape fixture has a clear 500px retreat')
    if escape is None: raise RuntimeError('No walkable slime escape fixture')
    print('   escape fixture',escape)
    put(*escape['start']); pg.wait_for_timeout(1500)
    check(ev("MossForest.monsters.find(m=>m.id==='a1_slime_hollow').state")== 'chase','slime is chasing before the escape walk')
    check(ev("([x,y])=>MossForest.goFeet(x,y)",escape['goal']),'escape movement accepted')
    pg.wait_for_timeout(5000)
    d=ev("window.__rec.filter(x=>x.id==='a1_slime_hollow').slice(-1)[0].d"); check(d>350 and ev("window.__starts")==0,'player outruns the slime (gap %.0f)'%d)
    # ---- 6) contact -> exactly one battle
    put(round(h[0]-40),round(h[1])); pg.wait_for_timeout(250)
    for i in range(40):
        if ev("document.body.classList.contains('normalBattleMode')"): break
        pg.wait_for_timeout(100)
    pg.wait_for_timeout(1500)
    check(ev("document.body.classList.contains('normalBattleMode')") and ev("currentGoblin")=='mossSlime1','touching the slime starts the existing slime battle (%s)'%ev("currentGoblin"))
    check(ev("window.__starts")==1,'battle started exactly once (no double fire) %d'%ev("window.__starts"))
    # ---- 7) win: slime gone; forestShow does not revive; another map -> A1 revives
    ev("PrologueCombat.instantKill('normal')"); pg.wait_for_timeout(2600)
    for i in range(8):
        if ev("getComputedStyle(document.querySelector('#battleResult')).display")=='none': break
        ev("(document.querySelector('#battleResult button')||document.querySelector('#battleResult')).click()"); pg.wait_for_timeout(500)
    pg.wait_for_timeout(1200)
    check(ev("forestActive")and not ev("document.body.classList.contains('normalBattleMode')"),'back in the forest')
    check(ev("MossForest.monsters.filter(m=>m.type==='moss_slime').map(m=>m.id).includes('a1_slime_hollow')")==False and ev("MossForest.monsters.filter(m=>m.type==='moss_slime').length")==5,'defeated slime is gone, the other 5 remain')
    ev("forestShow()"); pg.wait_for_timeout(800); check(ev("MossForest.monsters.filter(m=>m.type==='moss_slime').length")==5,'forestShow() alone does not respawn it')
    check(ev("PrologueProgress.count()")==0 and ev("storyStage")==9,'story progress untouched')
    ev("MossForest.enter({map:'moss_forest_03_ancient_grove',spawn:'from_area2'})"); pg.wait_for_timeout(2000)
    check(ev("MossForest.monsters.filter(m=>m.id==='a1_slime_hollow').length")==0 and ev("MossForest.monsters.length")==9,'other map (A3) holds its own 9 monsters, not the A1 ones')
    ev("MossForest.enter({map:'%s',spawn:'from_lind'})"%A1); pg.wait_for_timeout(2000)
    check(ev("MossForest.monsters.filter(m=>m.type==='moss_slime').length")==6,'re-entering A1 from another map respawns all 6 slimes')
    # ---- 8) A3 story goblins untouched
    ev("MossForest.enter({map:'moss_forest_03_ancient_grove',spawn:MossForest.map&&'from_area2'})"); pg.wait_for_timeout(2500)
    check(ev("MossForest.monsters.every(m=>m.type!=='goblin')") and ev("MossForest.symbolsAlive")==3,'A3 story goblin symbols (forestGob1-3) stay plain symbols (no field goblins there), still 3 alive')
    # ---- 9) collision: a goblin chasing across the pond's deep core never enters it / never jumps through it
    setup([{"id":"t_pond","type":"goblin","x":7370,"y":5330,"tune":{"battle":"moss_slime","touch":1}}])
    put(7740,5330); ev("window.__rec.length=0"); pg.wait_for_timeout(5000)
    r=ev("window.__rec"); jump=max(((a['x']-b_['x'])**2+(a['y']-b_['y'])**2)**.5 for a,b_ in zip(r[1:],r[:-1]))
    check('chase' in states('t_pond'),'pond goblin chases from across the water %s'%states('t_pond'))
    check(ev("window.__bad")==0 and jump<12,'goblin goes around the deep water: never inside a blocker, no jumps (max step %.1f)'%jump)
    ev("MossForest.enter({map:'moss_forest_02_mossy_ravine',spawn:'from_area1'})"); pg.wait_for_timeout(1500)
    # ---- 10) goblin type: faster / wider detect / longer chase than the slime; collision-safe; returns home; escapable; hands over to the existing battle
    setup([{"id":"t_gob","type":"goblin","x":3000,"y":5400,"tune":{"battle":"moss_slime"}},{"id":"t_slime","type":"moss_slime","x":3000,"y":5000}])
    T=ev("FieldMonsters.MONSTER_TYPES"); S=T['moss_slime']; G=T['goblin']
    check(G['speed']>S['speed']*2 and G['detect']>S['detect'] and G['chaseMax']>S['chaseMax'] and G['leash']>S['leash'] and G['alertTime']<S['alertTime'],'goblin: faster, wider detect, longer chase, quicker reaction than slime')
    check(G['speed']<290,'goblin is slower than the player (escapable)')
    put(3000-380,5400); ev("window.__rec.length=0"); pg.wait_for_timeout(1500)
    st=states('t_gob'); check('alert' in st and 'chase' in st,'goblin detects at ~380 (slime would not): alert -> chase %s'%st)
    r=ev("window.__rec.filter(x=>x.id==='t_gob'&&x.s==='chase')")
    if len(r)>20:
        dd=((r[-1]['x']-r[0]['x'])**2+(r[-1]['y']-r[0]['y'])**2)**.5/((r[-1]['t']-r[0]['t'])/1000); check(100<dd<200,'goblin chase speed ~150px/s (%.0f)'%dd)
    put(3000-380,5400+0); put(2000,5400); pg.wait_for_timeout(1500)
    pg.wait_for_timeout(12000); st=states('t_gob'); check('return' in st and st[-1]=='wander','goblin gives up and returns home %s'%st)
    gh=ev("(()=>{const m=MossForest.monsters.find(m=>m.id==='t_gob');return Math.hypot(m.x-m.home[0],m.y-m.home[1])})()"); check(gh<=200,'goblin is back at its post (%.0f)'%gh)
    check(ev("window.__bad")==0,'goblin/slime never inside a blocker')
    put(3000-300,5400); pg.wait_for_timeout(800); ev("MossForest.goFeet(1800,5500)"); pg.wait_for_timeout(8000)
    d=ev("window.__rec.filter(x=>x.id==='t_gob').slice(-1)[0].d"); check(d>200 and ev("window.__starts")==1,'player can outrun the goblin (gap %.0f)'%d)
    put(3000-50,5400); pg.wait_for_timeout(300)
    for i in range(40):
        if ev("document.body.classList.contains('normalBattleMode')"): break
        pg.wait_for_timeout(100)
    pg.wait_for_timeout(1200)
    check(ev("document.body.classList.contains('normalBattleMode')") and ev("window.__starts")==2,'goblin touch -> existing battle exactly once (%d)'%ev("window.__starts"))
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)
