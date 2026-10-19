"""T18 read-only measurement: auto-plays N real-flow Goblin Raider battles with a seeded Math.random and a fast-forwarded setTimeout
(timer delays only; no game rule/number is touched). Usage: lou_faint_baseline.py <base_url> <n> <out.json> [seed]
Works on both trees: if window.BattleLouFaint is missing (baseline = main) Lou never faints."""
import json, os, sys
from playwright.sync_api import sync_playwright
CAREFUL = os.getenv('LF_POLICY') == 'careful'  # heals earlier (HP<95) and guards earlier (HP<65)
base, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]; seed0 = int(sys.argv[4]) if len(sys.argv) > 4 else 1
INIT = """
(()=>{let s=%d>>>0;window.__seed=v=>{s=v>>>0};Math.random=function(){s=(s+0x6D2B79F5)|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296};
const st=window.setTimeout.bind(window);window.setTimeout=(f,ms,...a)=>st(f,Math.min(ms||0,(ms||0)/25),...a);})();
"""
res = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or None))
    for i in range(n):
        pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.add_init_script(INIT % (seed0 * 1000 + i))
        pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat'); pg.wait_for_timeout(600); pg.evaluate("closeDialogue()")
        pg.evaluate("""()=>{window.__m={starts:0,support:0,heal:0,bless:0,fainted:0,rounds:0,faintRounds:0,final:0,done:false};
         const sr=window.startRaiderBattle;window.startRaiderBattle=function(){__m.starts++;return sr.apply(this,arguments)};
         const ac=BattleActorState.action;
         const fr=window.finishRaider;window.finishRaider=function(){__m.done=true;return fr.apply(this,arguments)};
         const bp=BattleStatus.apply;}""")
        # count Lou support via BattleActorState.get transitions is unreliable; hook log text via the raider log function
        pg.evaluate("""()=>{const o=window.showRaiderBattleLog;window.showRaiderBattleLog=function(t){try{if(/妖精の癒し/.test(t))__m.heal++;if(/風の加護/.test(t))__m.bless++;if(/妖精の祝福/.test(t))__m.final++;if(/気を失/.test(t))__m.fainted++}catch(e){}return o.apply(this,arguments)}}""")
        pg.evaluate("PrologueProgress.seed(0);startRaiderBattle()")
        pg.evaluate("window.__m.starts=1")
        for step in range(4000):
            m = pg.evaluate("__m")
            if step % 100 == 0 and os.getenv('LF_DEBUG'): print('step', step, m, pg.evaluate("({r:rbRound,a:rbActor,busy:rbBusy,bp:BattlePresentation.busy,hp:[rbHP,rbFHP,rbBoss],d:document.body.className})"), flush=True)
            if m['done'] or m['starts']>1: break
            if pg.evaluate("document.body.classList.contains('dialogueOpen')"): pg.evaluate("closeDialogue()"); continue
            ready = pg.evaluate("!window.BattlePresentation.busy&&!rbBusy&&!BattleTargetSelector.active&&document.body.classList.contains('raiderBattleMode')&&!document.body.classList.contains('actionCinematic')")
            if not ready: pg.wait_for_timeout(30); continue
            pg.evaluate("""(C)=>{
              const gA=C?65:45,hF=C?95:70;
              const f=(window.BattleLouFaint&&BattleLouFaint.fainted)?1:0; __m.rounds=Math.max(__m.rounds,rbRound); if(rbActor==='aidan'){__m.faintRounds+=f}
              if(rbActor==='aidan'){ if(rbRune>=100) choosePartyAct('wind','raider_enemy_0'); else if(rbQueued||rbHP<gA) choosePartyAct('guard',null); else if(rbTP>=30) choosePartyAct('skill','raider_enemy_0'); else choosePartyAct('attack','raider_enemy_0'); }
              else { if(rbQueued) choosePartyAct('guard',null); else if(rbFHP<hF&&rbFMP>=8) choosePartyAct('heal','fiona'); else if(rbHP<hF&&rbFMP>=8) choosePartyAct('heal','aidan'); else choosePartyAct('attack','raider_enemy_0'); }
            }""", CAREFUL)
            pg.wait_for_timeout(30)
        m = pg.evaluate("__m"); m['i'] = i; m['won'] = bool(m['done']); m['errs'] = errs[:2]; res.append(m); pg.close()
        print(i, m, flush=True)
    b.close()
json.dump(res, open(out, 'w'), indent=1)
