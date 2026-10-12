# フォレストバット: 戦闘(2体・吸血・idle4コマ)、フィールドAI(飛行・追跡・復帰)、接触→既存戦闘、撃破後消滅・再入場復活、A3ストーリーゴブリン不変。 needs http.server (PORT env)
import os, sys
from playwright.sync_api import sync_playwright
PORT=os.environ.get('PORT','8765'); fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
A2='moss_forest_02_mossy_ravine'
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:%s/index.html'%PORT); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=9;enterMossForest()"); pg.wait_for_timeout(2500)
    ev("(()=>{window.__starts=0;const _s=startAttackBattle;window.startAttackBattle=function(){window.__starts++;return _s.apply(this,arguments)};return 1})()")
    ev("""window.__rec=[];window.__bad=0;(function loop(){const f=MossForest.feet;for(const m of MossForest.monsters){window.__rec.push({id:m.id,s:m.state,x:m.x,y:m.y,d:Math.hypot(f.x-m.x,f.y-m.y),t:performance.now(),src:m.el.dataset.src||''});if(MossForest.blocked(m.x,m.y))window.__bad++;}
      if(window.__rec.length>20000)window.__rec.splice(0,10000);requestAnimationFrame(loop)})()""")
    def states(i):
        out=[]
        for x in ev("window.__rec.filter(x=>x.id==='%s')"%i):
            if not out or out[-1]!=x['s']: out.append(x['s'])
        return out
    put=lambda x,y: ev("MossForest.teleportFeet(%d,%d)"%(x,y))
    # ---- 1) art + stats
    sizes=ev("Promise.all(Object.values(BATTLE_ASSETS.forest_bat).map(u=>new Promise(r=>{const i=new Image();i.onload=()=>r([i.naturalWidth,i.naturalHeight]);i.onerror=()=>r(null);i.src=u;})))")
    check(all(s==[1536,1024] for s in sizes),'battle bat art loads (idle frame aliases for attack/damage/ko) %s'%sizes[:1])
    check(ev("BATTLE_IDLE_ASSETS.forest_bat.frames.length")==4,'4 idle frames registered')
    T=ev("FieldMonsters.MONSTER_TYPES"); S=T['moss_slime']; B=T['forest_bat']
    check(B['speed']>S['speed'] and B['detect']>S['detect'],'bat is faster / notices from farther than a slime')
    # ---- 2) field: A2 shows two bats; homes walkable; flap frames; hover
    ev("MossForest.enter({map:'%s',spawn:'from_area1'})"%A2); pg.wait_for_timeout(2500)
    L=ev("MossForest.monsters.filter(m=>m.type==='forest_bat').map(m=>[m.id,m.type,m.x,m.y,MossForest.blocked(m.x,m.y)])")
    L=[m for m in L if m[1]=='forest_bat']; check(len(L)==6 and all(not m[4] for m in L),'A2 has 6 forest bats on walkable ground %s'%[m[0] for m in L])
    check(ev("MossForest.monsters.filter(m=>m.type==='forest_bat').length")==6 and ev("MossForest.monsters.length")==24,'6 bats mounted among the 24 A2 monsters (6 each of slime/boar/bat/goblin)')
    put(4850,5330+700); ev("window.__rec.length=0"); pg.wait_for_timeout(2500)
    srcs=ev("[...new Set(window.__rec.filter(x=>x.id==='a2_bat_south_wall_w').map(x=>x.src))]")
    check(len(srcs)==4,'bat flaps through all 4 frames even while wandering (%d)'%len(srcs))
    # ---- 3) alert -> chase -> return, escape
    h=ev("(()=>{const m=MossForest.monsters.filter(m=>m.type==='forest_bat')[0];return [m.x,m.y]})()")
    put(round(h[0]),round(h[1]+320)); ev("window.__rec.length=0"); pg.wait_for_timeout(1400)
    st=states('a2_bat_south_wall_w'); check('alert' in st and 'chase' in st,'bat notices at ~320: alert -> chase %s'%st)
    r=ev("window.__rec.filter(x=>x.id==='a2_bat_south_wall_w'&&x.s==='chase')")
    if len(r)>20:
        dd=((r[-1]['x']-r[0]['x'])**2+(r[-1]['y']-r[0]['y'])**2)**.5/((r[-1]['t']-r[0]['t'])/1000); check(80<dd<170,'bat chase speed ~120px/s (%.0f)'%dd)
    put(round(h[0]),round(h[1]+1000)); pg.wait_for_timeout(9000)
    st=states('a2_bat_south_wall_w'); check('return' in st and st[-1]=='wander','after the player escapes: return -> wander %s'%st)
    check(ev("window.__bad")==0 and ev("window.__starts")==0,'never inside a blocker, no battle without contact')
    # ---- 4) contact -> exactly one battle with two bats
    put(round(h[0]),round(h[1]+40)); pg.wait_for_timeout(300)
    for i in range(40):
        if ev("document.body.classList.contains('normalBattleMode')"): break
        pg.wait_for_timeout(100)
    pg.wait_for_timeout(2000)
    check(ev("currentGoblin")=='forestBat2' and ev("window.__starts")==1,'touching a bat starts the existing battle once (%s, starts=%d)'%(ev("currentGoblin"),ev("window.__starts")))
    en=ev("PrologueCombat.enemies.normal.map(e=>[e.type,e.hp,e.maxHp])")
    check(en==[['forest_bat',91,91],['forest_bat',91,91]],'two forest bats (91 HP) %s'%en)
    check('フォレストバット' in ev("document.querySelector('#v2EnemyName').textContent"),'enemy name shows フォレストバット')
    st=ev("BattleIdleMotion.status.actors.filter(a=>a.actor==='forest_bat').map(a=>a.showing)")
    check(st[:2]==[True,True],'idle flap canvases are showing for both bats %s'%st)
    pg.wait_for_timeout(2600); fr=set()
    for i in range(30):
        fr.add(ev("BattleIdleMotion.status.actors.find(a=>a.actor==='forest_bat').frame")); pg.wait_for_timeout(250)
    check(len(fr)>=2,'idle frames advance %s'%sorted(fr))
    # ---- 5) vampiric attack: heals ~60% of damage dealt, capped at max HP
    ev("(()=>{const e=PrologueCombat.enemies.normal[0];e.hp=20;PrologueCombat.sync('normal');})()")
    a0=ev("aahp"); f0=ev("normalFHP"); ev("PrologueCombat.performEnemy('normal',PrologueCombat.enemies.normal[0],'attack')"); pg.wait_for_timeout(2600)
    dmg=(a0-ev("aahp"))+(f0-ev("normalFHP")); hp=ev("PrologueCombat.enemies.normal[0].hp")
    check(dmg>0 and hp-20==max(1,round(dmg*0.6)),'bat drained: dealt %d, healed %d (60%%)'%(dmg,hp-20))
    ev("(()=>{PrologueCombat.enemies.normal[0].hp=90;PrologueCombat.sync('normal');})()")
    ev("PrologueCombat.performEnemy('normal',PrologueCombat.enemies.normal[0],'attack')"); pg.wait_for_timeout(2600)
    check(ev("PrologueCombat.enemies.normal[0].hp")==91,'healing is capped at max HP')
    # ---- 6) win: rewards EXP+20 / GOLD+8, bats gone, no story progress, forestShow no respawn, re-entry respawn
    exp0=ev("PartyManager.members.aidan.exp"); gold0=ev("gold")
    ev("PrologueCombat.instantKill('normal')"); pg.wait_for_timeout(2600)
    check('EXP +30' in ev("document.querySelector('#resultExp').textContent") and ev("gold")-gold0==12,'result: EXP +30, GOLD +12')
    for i in range(8):
        if ev("getComputedStyle(document.querySelector('#battleResult')).display")=='none': break
        ev("(document.querySelector('#battleResult button')||document.querySelector('#battleResult')).click()"); pg.wait_for_timeout(500)
    pg.wait_for_timeout(1200)
    check(ev("forestActive") and ev("MossForest.monsters.filter(m=>m.type==='forest_bat').map(m=>m.id).includes('a2_bat_south_wall_w')")==False and ev("MossForest.monsters.filter(m=>m.type==='forest_bat').length")==5,'back in the forest; defeated bat symbol is gone, the other 5 remain')
    ev("forestShow()"); pg.wait_for_timeout(600); check(ev("MossForest.monsters.filter(m=>m.type==='forest_bat').length")==5,'forestShow() does not respawn it')
    check(ev("PrologueProgress.count()")==0 and ev("storyStage")==9,'story progress untouched')
    ev("MossForest.enter({map:'moss_forest_03_ancient_grove',spawn:'from_area2'})"); pg.wait_for_timeout(2500)
    check(ev("MossForest.monsters.every(m=>m.type!=='goblin')") and ev("MossForest.symbolsAlive")==3,'A3 story goblin symbols untouched')
    ev("MossForest.enter({map:'%s',spawn:'from_area1'})"%A2); pg.wait_for_timeout(2500)
    check(ev("MossForest.monsters.filter(m=>m.type==='forest_bat').length")==6,'re-entering A2 respawns all 6 bats')
    # next battle on the same slot: a goblin/slime battle shows no bat canvas
    ev("startAttackBattle('mossSlime1',56)"); pg.wait_for_timeout(1800)
    check(not ev("BattleIdleMotion.status.actors.some(a=>a.actor==='forest_bat'&&a.showing)") and 'moss_slime' in ev("document.querySelector('#bGob img').getAttribute('src')"),'afterwards a slime battle in the same slot shows no bat art')
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)
