# 風の舞 in battle (decided numbers: +15pt evasion, all allies, 3 enemy phases, MP10, refresh) and the provisional bolt MP regain (off/hit/action).
import os, sys
from playwright.sync_api import sync_playwright
PORT=os.environ.get('PORT','8765'); fails=[]; errs=[]
def ck(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    def fresh(q=''):
        pg=b.new_page(viewport={'width':844,'height':390}); pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e)))
        pg.goto('http://localhost:%s/index.html?dev=1%s'%(PORT,q)); pg.wait_for_timeout(1500); pg.evaluate('closeDialogue()'); return pg
    def battle(pg):
        pg.evaluate("PrologueProgress.seed(3);startAttackBattle('fieldGob1',100)"); pg.wait_for_timeout(1500)
    def idle(pg,t=20000):
        for _ in range(t//200):
            pg.wait_for_timeout(200)
            if pg.evaluate("attackBattleBusy===false"): return True
        return False
    def rnd(pg,acts):
        pg.evaluate("a=>{PrologueCombat.round('normal',a)}",acts); pg.wait_for_timeout(300); return idle(pg)
    def st(pg,who='aidan'): return pg.evaluate("w=>BattleStatus.list('normal',w).filter(e=>e.type==='eva_up')",who)
    # ---- flag off: the command does not exist and the engine ignores it
    pg=fresh(); battle(pg); ev=pg.evaluate
    ev("WindDance.learn()")
    ck(ev("WindDance.commandVisible()")==False,'flag off: command not visible even after learning')
    ev("normalFMP=30"); ok=rnd(pg,[{'who':'fiona','kind':'winddance'}])
    ck(ok and ev("normalFMP")==30 and st(pg)==[],'flag off: a forced winddance action costs nothing and applies nothing')
    ev("BattleStatus.apply({battle:'normal',target:'aidan',type:'atk_up',magnitude:.15,remainingTurns:3,source:'t'})")
    ck(ev("BattleStatus.dodges('normal','aidan',()=>0)")==False and ev("BattleStatus.evasion('normal','aidan')")==0,'no eva_up effect: evasion 0, never rolls')
    ck(ev("(()=>{let n=0;const r=Math.random;Math.random=()=>{n++;return 0};PrologueCombat.enemies;BattleStatus.dodges('normal','fiona');Math.random=r;return n})()")==0,'no eva_up effect: no random number is consumed')
    # bolt MP default off
    ev("normalFMP=10"); rnd(pg,[{'who':'fiona','kind':'atk','target':'normal_enemy_0'}]); ck(ev("normalFMP")==10,'bolt MP regain defaults to off (MP unchanged)')
    pg.close()
    # ---- flag on
    pg=fresh('&feature=windDanceCommand'); battle(pg); ev=pg.evaluate
    ck(ev("WindDance.commandVisible()")==False,'flag on but not learned: unusable')
    ev("normalFMP=30"); rnd(pg,[{'who':'fiona','kind':'winddance'}]); ck(ev("normalFMP")==30 and st(pg)==[],'not learned: forced action does nothing')
    ev("WindDance.learn();updateNormalCommands()")
    ev("normalActor='fiona'; updateNormalCommands()")
    ck(ev("!document.querySelector('#nWindDance').hidden")==True,'learned + flag: command shown in Fiona\'s row')
    ev("normalFMP=9;updateNormalCommands()"); ck(ev("document.querySelector('#nWindDance').disabled")==True,'MP9: command disabled (cost 10)')
    ev("normalFMP=30;updateNormalCommands()")
    # cast through the UI path: Aidan guards, Fiona casts
    ev("normalActor='fiona';updateNormalCommands();chooseNormalAct('winddance')"); pg.wait_for_timeout(800); ck(idle(pg),'cast round finished (via the command button path)')
    ck(ev("normalFMP")==20,'MP10 spent (30 -> %s)'%ev("normalFMP"))
    a=st(pg,'aidan'); f=st(pg,'fiona')
    ck(len(a)==1 and len(f)==1 and abs(a[0]['magnitude']-.15)<1e-9 and abs(f[0]['magnitude']-.15)<1e-9,'all allies get +15pt evasion %s'%a)
    ck(a[0]['remainingTurns']==2,'after the cast round 2 phases remain (the cast round\'s own enemy phase was covered) -> 3 in total (remaining %s)'%a[0]['remainingTurns'])
    # refresh, no stacking
    ev("normalFMP=30"); rnd(pg,[{'who':'fiona','kind':'winddance'}])
    a=st(pg); ck(len(a)==1 and abs(a[0]['magnitude']-.15)<1e-9 and a[0]['remainingTurns']==2 and abs(ev("BattleStatus.evasion('normal','aidan')")-.15)<1e-9,'recast refreshes duration, does not stack (evasion %s)'%ev("BattleStatus.evasion('normal','aidan')"))
    # forced dodge while active: no damage taken
    ev("Math.random=()=>0"); h0=ev("[aahp,normalFHP]")
    rnd(pg,[{'who':'fiona','kind':'guard'}]); h1=ev("[aahp,normalFHP]"); ck(h0==h1,'dodge roll succeeds -> no HP lost during phase 2 %s %s'%(h0,h1))
    ck(st(pg)[0]['remainingTurns']==1,'phase 2 ticked (remaining 1)')
    rnd(pg,[{'who':'fiona','kind':'guard'}]); h2=ev("[aahp,normalFHP]"); ck(h1==h2,'dodge roll succeeds -> no HP lost during phase 3')
    ck(st(pg)==[],'effect gone after the 3rd phase')
    rnd(pg,[{'who':'fiona','kind':'guard'}]); rnd(pg,[{'who':'fiona','kind':'guard'}]); h3=ev("[aahp,normalFHP]"); ck(h3!=h2,'after expiry the enemy hits again %s -> %s'%(h2,h3))
    ev("Math.random=()=>0.999")
    # evasion cap
    ev("BattleStatus.apply({battle:'normal',target:'aidan',type:'eva_up',magnitude:1,remainingTurns:2,source:'t'})")
    ck(ev("BattleStatus.evasion('normal','aidan')")==0.5,'evasion is capped at 50%')
    pg.close()
    # ---- bolt MP regain modes
    for mode,hit_gain,dead_gain in (('hit',3,0),('action',3,3)):
        pg=fresh('&boltMana='+mode); battle(pg); ev=pg.evaluate
        ev("normalFMP=10"); rnd(pg,[{'who':'fiona','kind':'atk','target':'normal_enemy_0'}])
        ck(ev("normalFMP")==10+hit_gain,'[%s] bolt on a living target: MP +%d (got %s)'%(mode,hit_gain,ev("normalFMP")))
        ev("normalFMP=10"); rnd(pg,[{'who':'fiona','kind':'atk','target':'nobody'}])
        ck(ev("normalFMP")==10+dead_gain,'[%s] bolt with no valid target: MP +%d (got %s)'%(mode,dead_gain,ev("normalFMP")))
        ev("normalFMP=29"); rnd(pg,[{'who':'fiona','kind':'atk','target':'normal_enemy_0'}]); ck(ev("normalFMP")==30,'[%s] capped at max MP 30'%mode)
        ev("normalFMP=10"); rnd(pg,[{'who':'aidan','kind':'atk','target':'normal_enemy_0'}]); ck(ev("normalFMP")==10,'[%s] Aidan\'s attack gives no MP'%mode)
        pg.close()
    ck(not errs,'no page errors %s'%errs[:2])
    b.close()
print('FAILS',len(fails)); sys.exit(1 if fails else 0)
