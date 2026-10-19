"""T18 reproducibility / cause-analysis harness (read-only measurement; no game rule or number is touched).
usage: lou_faint_t18_matrix.py <base_url> <n> <seed> <policy A|B> <mode normal|nofaint|nolou> <out.json>
 seed   : battle i uses Math.random seed seed*1000+i and (feature tree only) Lou-faint RNG fixSeed(seed*1000+i)  [DEV]
 policy : A = attack/guard/heal bot (as T18 v1); B = A + uses きずぐすり (potion) when an ally HP < 55  (closer to a human)
 mode   : normal = tree as-is | nofaint = feature tree with Lou-faint disabled by a DEV script of 0.99 draws (control: must equal main)
          nolou  = Lou's support AND final blessing disabled by test-side proxies (answers: can this bot win without Lou at all?)
timers are only fast-forwarded (setTimeout/25)."""
import json, os, sys
from playwright.sync_api import sync_playwright
base, n, seed, policy, mode, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6]
INIT = """
(()=>{let s=%d>>>0;Math.random=function(){s=(s+0x6D2B79F5)|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296};
const st=window.setTimeout.bind(window);window.setTimeout=(f,ms,...a)=>st(f,Math.min(ms||0,(ms||0)/25),...a);})();
"""
HOOK = """([mode,seed])=>{
 window.__m={starts:1,done:false,heal:[],bless:[],final:[],faint:[],wake:[],log:[],turns:[],faintTurns:0,rounds:0};
 const sr=window.startRaiderBattle;window.startRaiderBattle=function(){__m.starts++;return sr.apply(this,arguments)};
 const fr=window.finishRaider;window.finishRaider=function(){__m.done=true;return fr.apply(this,arguments)};
 const o=window.showRaiderBattleLog;window.showRaiderBattleLog=function(t){try{const r=rbRound;__m.log.push([r,String(t).slice(0,90)]);
   if(/妖精の癒し/.test(t))__m.heal.push(r);if(/風の加護/.test(t))__m.bless.push(r);if(/妖精の祝福/.test(t))__m.final.push(r);
   if(/気を失/.test(t))__m.faint.push(r);if(/目を覚ました/.test(t))__m.wake.push(r)}catch(e){}return o.apply(this,arguments)};
 if(window.BattleLouFaint&&mode!=='nolou'){ if(mode==='nofaint')BattleLouFaint.setScript(Array(400).fill(0.99)); else BattleLouFaint.fixSeed(seed); BattleLouFaint.reset(); }
 if(mode==='nolou'){
  const A=window.BattleActorState; window.BattleActorState=new Proxy({},{get:(_,k)=>k==='get'?((c,a='aidan')=>(c==='raider'&&a==='lou')?'victory':A.get(c,a)):A[k]});
  const P=window.BattlePresentation; window.BattlePresentation=new Proxy({},{get:(_,k)=>k==='action'?((b,kind,tok)=>(b==='raider'&&kind==='blessing')?Promise.resolve(false):P.action(b,kind,tok)):P[k]});
 }
}"""
TURN = """([pol])=>{
  const f=(window.BattleLouFaint&&BattleLouFaint.fainted)?1:0; __m.rounds=Math.max(__m.rounds,rbRound);
  if(rbActor==='aidan'){__m.faintTurns+=f;__m.turns.push([rbRound,rbHP,rbFHP,rbBoss,f])}
  const B=pol==='B',pot=()=>battleItems.potion>0;
  const push=(who,item,target)=>{rbActs.push({who,kind:'item',item,target});if(who==='aidan'){rbActor='fiona';updateRaider()}else{rbBusy=true;resolvePartyRound()}};
  if(rbActor==='aidan'){
    if(B&&pot()&&rbHP<55)return push('aidan','potion','aidan');
    if(rbRune>=100)choosePartyAct('wind','raider_enemy_0'); else if(rbQueued||rbHP<45)choosePartyAct('guard',null); else if(rbTP>=30)choosePartyAct('skill','raider_enemy_0'); else choosePartyAct('attack','raider_enemy_0');
  } else {
    if(rbQueued)choosePartyAct('guard',null);
    else if(rbFHP<70&&rbFMP>=8)choosePartyAct('heal','fiona'); else if(rbHP<70&&rbFMP>=8)choosePartyAct('heal','aidan');
    else if(B&&pot()&&rbFHP<55)push('fiona','potion','fiona'); else if(B&&pot()&&rbHP<55)push('fiona','potion','aidan');
    else choosePartyAct('attack','raider_enemy_0');
  }
}"""
res = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or None))
    for i in range(n):
        sd = seed * 1000 + i
        pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.add_init_script(INIT % sd)
        pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat'); pg.wait_for_timeout(600); pg.evaluate("closeDialogue()")
        pg.evaluate(HOOK, [mode, sd]); pg.evaluate("PrologueProgress.seed(0);startRaiderBattle();__m.starts=1")
        for step in range(5000):
            m = pg.evaluate("({d:__m.done,s:__m.starts})")
            if m['d'] or m['s'] > 1: break
            if pg.evaluate("document.body.classList.contains('dialogueOpen')"): pg.evaluate("closeDialogue()"); continue
            ready = pg.evaluate("!window.BattlePresentation.busy&&!rbBusy&&!BattleTargetSelector.active&&document.body.classList.contains('raiderBattleMode')&&!document.body.classList.contains('actionCinematic')")
            if not ready: pg.wait_for_timeout(30); continue
            pg.evaluate(TURN, [policy]); pg.wait_for_timeout(30)
        m = pg.evaluate("__m"); m.update(i=i, seed=sd, won=bool(m['done']), errs=errs[:2])
        if m['won']: m['log'] = []          # keep full logs only for wipes
        res.append(m); pg.close()
        print(i, 'WIN' if m['won'] else 'WIPE', 'r', m['rounds'], 'faint', m['faint'], 'wake', m['wake'], 'final', m['final'], flush=True)
    b.close()
json.dump(dict(base=base, n=n, seed=seed, policy=policy, mode=mode, results=res), open(out, 'w'))
