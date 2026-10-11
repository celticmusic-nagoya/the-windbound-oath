# 戦闘演出: 近接は敵位置へ飛び込む / 魔法職は少し前進+魔弾 / ルーの飛び回り+浮き沈み / カットイン・勝利ポーズ延長 / A1・A2配置
import os
from playwright.sync_api import sync_playwright
PORT=os.environ.get('PORT','8765'); fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:%s/index.html'%PORT); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=9;enterMossForest()"); pg.wait_for_timeout(2500)
    # --- placement
    def census(m):
        ev("MossForest.enter({map:'%s'})"%m); pg.wait_for_timeout(1800)
        L=ev("MossForest.monsters.map(m=>[m.type,MossForest.blocked(m.x,m.y)])")
        c={}
        for t,bl in L: c[t]=c.get(t,0)+1
        return c,any(bl for _,bl in L)
    c,bl=census('moss_forest_01_sunlit_path'); check(c=={'moss_slime':2,'leafy_boar':2,'goblin':2} and not bl,'A1: slime2 boar2 goblin2, none blocked %s'%c)
    c,bl=census('moss_forest_02_mossy_ravine'); check(c=={'moss_slime':2,'leafy_boar':2,'forest_bat':2} and not bl,'A2: slime2 boar2 bat2, none blocked %s'%c)
    # --- goblin contact -> battle (fieldGob), reward id accepted
    ev("MossForest.enter({map:'moss_forest_01_sunlit_path'})"); pg.wait_for_timeout(1500)
    ev("MossForest.teleportFeet(MossForest.monsters.find(m=>m.type==='goblin').x+10,MossForest.monsters.find(m=>m.type==='goblin').y+60)"); pg.wait_for_timeout(2500)
    check(ev("currentGoblin")=='fieldGob1' and ev("document.body.classList.contains('normalBattleMode')"),'goblin contact starts battle fieldGob1 (%s)'%ev("currentGoblin"))
    check(ev("PrologueCombat.targets('normal').length")==1,'goblin roster has 1 enemy')
    # --- melee dives to the target; ranged steps a little
    pg.wait_for_timeout(1500)
    ev("window.__imp=()=>PrologueCombat.impactTarget()")
    ge=ev("(()=>{const g=WBApproach('v2AidanUnit');const f=WBApproach('v2FionaUnit');return {g,f}})()")
    check(ge['g'] is None,'approach needs an impact target (none yet -> fallback) %s'%ge['g'])
    ev("PrologueCombat.beginNormal('leafyBoar2')"); pg.wait_for_timeout(500)
    ev("(()=>{window.__t=null})()")
    ev("""window.__min=1e9;window.__bolt=0;window.__fdx=0;(function loop(){const a=document.getElementById('bAidan2'),t=document.querySelector('#normalEnemy1 .prologueSprite');
      if(a&&t){const r=a.getBoundingClientRect(),q=t.getBoundingClientRect();const g=Math.abs((q.left+q.width/2)-(r.left+r.width/2));window.__min=Math.min(window.__min,g);window.__lim=(r.width+q.width)*.5*.62}
      window.__bolt=Math.max(window.__bolt,document.querySelectorAll('.wbBolt').length);
      const f=document.getElementById('bFiona2').getBoundingClientRect();window.__f0=window.__f0??f.left;window.__fdx=Math.max(window.__fdx,Math.abs(f.left-window.__f0));
      if(!window.__stop)requestAnimationFrame(loop)})()""")
    pg.wait_for_timeout(300)
    ev("normalActor='aidan';chooseNormalAct('atk',PrologueCombat.targets('normal')[1].id)")
    ev("chooseNormalAct('atk',PrologueCombat.targets('normal')[1].id)")
    pg.wait_for_timeout(4500); ev("window.__stop=1")
    mn=ev("window.__min"); lim=ev("window.__lim")
    check(mn<lim*1.8,'Aidan dives to the targeted enemy (closest gap %.0f px, contact range %.0f, start gap ~500)'%(mn,lim))
    check(ev("document.getElementById('v2AidanUnit').getAnimations().length")==0,'lunge finished and he returned')
    check(ev("window.__bolt")>=1,'Fiona fires a bolt (%s)'%ev("window.__bolt"))
    check(ev("window.__fdx")<260,'Fiona only steps slightly forward (max %.0f px)'%ev("window.__fdx"))
    # --- cutin duration
    check(ev("BattleCutinManager.durations.SHORT")>=1100 and ev("BattleCutinManager.durations.SPECIAL")>=1800,'cut-in display times extended %s'%ev("JSON.stringify(BattleCutinManager.durations)"))
    # --- victory pose lasts
    ev("PrologueCombat.beginNormal('mossSlime1')"); pg.wait_for_timeout(400)
    ev("window.__t0=performance.now();window.__res=null;const o=window.showBattleResult;window.showBattleResult=function(){window.__res=performance.now()-window.__t0;return o.apply(this,arguments)}")
    ev("PrologueCombat.targets('normal');finishAttackBattle()"); pg.wait_for_timeout(3600)
    r=ev("window.__res"); check(r is not None and r>=2200,'result screen appears after the extended victory pose (%.0f ms)'%(r or -1))
    # --- Lou
    ev("MossForest.reset();storyStage=9"); 
    ev("startRaiderBattle()"); pg.wait_for_timeout(1500)
    check(ev("BattleLouFlight.running"),'Lou flight active in raider battle')
    offs=set()
    for _ in range(10):
        pg.wait_for_timeout(700); o=ev("(()=>{const a=document.getElementById('rbLou').getBoundingClientRect();return [Math.round(a.left/10),Math.round(a.top/10)]})()"); offs.add(tuple(o))
    check(len(offs)>=5,'Lou drifts around (%d distinct positions)'%len(offs))
    check('louFloat' in ev("getComputedStyle(document.querySelector('#rbLou>img')).animationName"),'Lou bobs up/down continuously')
    ev("BattleActorState.action('lou','blessing',{battle:'raider'})"); pg.wait_for_timeout(600)
    check(ev("BattleLouFlight.running"),'flight continues during support action')
    ev("(()=>{document.getElementById('raiderBattle').style.display='none';document.body.classList.remove('raiderBattleMode','battleMode')})()"); pg.wait_for_timeout(900)
    check(not ev("BattleLouFlight.running"),'flight stops when the battle closes')
    check(not errs,'no page errors %s'%errs[:3])
    b.close()
print('FAILS:',fails); raise SystemExit(1 if fails else 0)
