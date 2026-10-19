"""T19: no stale Lou-faint judgement / recovery survives battle end, retry (wipe) or restart; defeat is judged before the round-end recovery."""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
fails = []
def check(ok, name, d=''):
    print(('ok   ' if ok else 'FAIL ') + name, d, flush=True)
    if not ok: fails.append(name)
IDLE = "!document.body.classList.contains('battlePresentationBusy')&&!document.body.classList.contains('dialogueOpen')&&!document.body.classList.contains('actionCinematic')"
def settle(pg, n=60):
    for _ in range(n):
        if pg.evaluate("document.body.classList.contains('dialogueOpen')"): pg.evaluate("closeDialogue()")
        if pg.evaluate(IDLE): return
        pg.wait_for_timeout(400)
def fresh(pg, script):
    pg.evaluate("PrologueProgress.seed(0);startRaiderBattle()"); pg.wait_for_timeout(300); settle(pg); pg.wait_for_timeout(300)
    pg.evaluate("s=>{BattleLouFaint.reset();BattleLouFaint.setScript(s)}", script)
def rnd(pg, queued, hp=None):
    pg.evaluate("([q,hp])=>{rbHP=hp??120;rbFHP=105;rbRound=1;rbQueued=q;window.__done=false;rbEnemyParty().then(()=>window.__done=true)}", [queued, hp])
    for _ in range(80):
        if pg.evaluate("document.body.classList.contains('dialogueOpen')"): pg.evaluate("closeDialogue()")
        if pg.evaluate("window.__done"): break
        pg.wait_for_timeout(400)
    settle(pg)
S = "()=>({f:BattleLouFaint.fainted,af:BattleActorState.fainted('raider','lou'),lou:BattleActorState.get('raider','lou'),d:BattleLouFaint.draws,r:rbRound,a:rbActor,busy:rbBusy,badge:document.querySelector('#rbLou').classList.contains('louFainted'),ep:PrologueCombat.enragePending})"
with server(8853) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or None))
    pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat&&window.BattleLouFaint'); pg.wait_for_timeout(1000); pg.evaluate("closeDialogue()")
    # a) retry (startRaiderBattle) while fainted
    fresh(pg, [0.1]); rnd(pg, True); check(pg.evaluate(S)['f'], 'a) setup: fainted')
    pg.evaluate("startRaiderBattle()"); pg.wait_for_timeout(500); settle(pg); s = pg.evaluate(S)
    check(not s['f'] and not s['af'] and not s['badge'] and s['lou'] != 'ko' and s['d'] == 0, 'a) restart clears faint, badge, KO pose and draw count', s)
    # b) wipe while fainted: defeat is judged first, no recovery log/draw, new battle starts clean
    fresh(pg, [0.1, 0.1]); rnd(pg, True); rnd(pg, False); rnd(pg, False, hp=1)  # R+2 would draw 0.1 (=wake) but the party is wiped
    pg.wait_for_timeout(2500); settle(pg); s = pg.evaluate(S)
    check(not s['f'] and s['r'] == 1 and s['a'] == 'aidan' and not s['busy'] and s['lou'] != 'ko', 'b) wipe at the would-be recovery round -> clean new battle (no stale wake)', s)
    # c) generation change during the post-wake pending blessing
    fresh(pg, [0.1, 0.1]); rnd(pg, True); pg.evaluate("PrologueCombat.enrageMoment()")
    pg.evaluate("rbRound=1;window.__done=false;rbEnemyParty().then(()=>window.__done=true)"); settle(pg)
    pg.evaluate("rbRound=1;window.__done=false;rbHP=120;rbFHP=105;rbEnemyParty().then(()=>window.__done=true)")
    for _ in range(40):  # wait until recovery happened and the deferred blessing is running (presentation busy)
        if not pg.evaluate("BattleLouFaint.fainted"): break
        if pg.evaluate("document.body.classList.contains('dialogueOpen')"): pg.evaluate("closeDialogue()")
        pg.wait_for_timeout(250)
    pg.evaluate("startRaiderBattle()"); pg.wait_for_timeout(3500); settle(pg); s = pg.evaluate(S)
    check(s['r'] == 1 and s['a'] == 'aidan' and not s['busy'] and not s['f'] and not s['ep'], 'c) restart during post-wake blessing: old flow leaves the new battle untouched', s)
    # d) victory while fainted, then a new battle
    fresh(pg, [0.1]); rnd(pg, True)
    pg.evaluate("rbBoss=1;finishRaider()"); pg.wait_for_timeout(600)
    v = pg.evaluate(S)
    check(v['lou'] == 'victory' and not v['f'] and not v['af'] and not v['badge'], 'd) victory pose wins over faint; flag and badge cleared', v)
    pg.evaluate("startRaiderBattle()"); pg.wait_for_timeout(500); settle(pg); s = pg.evaluate(S)
    check(not s['f'] and s['lou'] != 'victory' and s['lou'] != 'ko' and s['d'] == 0, 'd) next battle starts without leftovers', s)
    check(not errs, 'no page errors', errs[:3])
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)
