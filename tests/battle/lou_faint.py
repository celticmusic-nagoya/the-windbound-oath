"""Lou-only faint (lou_faint) — confirmed spec 2026-10-16 (docs/battle/lou-faint/). NOT the general stun candidate.
Covers T1,T1b,T2-T5 (counter 0/1/2/3), T6/T7 (final blessing deferral), T9, T10 (victory), T11-T13 (RNG independence, DEV-only), T14/T15 (badge, no counts in DOM), T21.
Deterministic: DEV setScript() injects the draw values; the 33% / 50% boundaries are exercised exactly (0.329 / 0.33, 0.49 / 0.5)."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
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
def fresh(pg, script=None):
    pg.evaluate("PrologueProgress.seed(0);startRaiderBattle()"); pg.wait_for_timeout(300); settle(pg); pg.wait_for_timeout(300)
    pg.evaluate("BattleLouFaint.reset()")
    if script is not None: pg.evaluate("s=>BattleLouFaint.setScript(s)", script)
def smash_round(pg):
    """Run one enemy round with 破砕斬 queued (party HP reset so nobody is defeated)."""
    pg.evaluate("rbHP=120;rbFHP=105;rbQueued=true;window.__done=false;rbEnemyParty().then(()=>window.__done=true)")
    for _ in range(80):
        if pg.evaluate("document.body.classList.contains('dialogueOpen')"): pg.evaluate("closeDialogue()")
        if pg.evaluate("window.__done"): break
        pg.wait_for_timeout(400)
    settle(pg)
st = "()=>({f:BattleLouFaint.fainted,s:BattleActorState.get('raider','lou'),d:BattleLouFaint.draws,r:rbRound})"
with server(8851) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or None))
    pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat&&window.BattleLouFaint'); pg.wait_for_timeout(1200); pg.evaluate("closeDialogue()")
    # T1 / T1b: boundary 0.329 faints, 0.33 does not
    fresh(pg, [0.33]); smash_round(pg); s = pg.evaluate(st)
    check(not s['f'] and s['s'] != 'ko' and s['d'] == 1, 'T1b draw 0.33 -> no faint (one draw)', s)
    fresh(pg, [0.329]); smash_round(pg); s = pg.evaluate(st)
    check(s['f'] and s['s'] == 'ko' and s['d'] == 1, 'T1 draw 0.329 -> faint, Lou shows existing KO motion', s)
    check(pg.evaluate("rbHP>0&&rbFHP>0&&document.body.classList.contains('raiderBattleMode')"), 'T9 Lou faint alone is not a wipe / no restart')
    check(pg.evaluate("document.querySelector('#rbLou').classList.contains('louFainted')&&getComputedStyle(document.querySelector('#rbLou .louFaintTag')).display!=='none'"), 'T14 faint badge shown')
    txt = pg.evaluate("document.querySelector('#rbLou').innerText+'|'+document.querySelector('#rbLou').outerHTML+'|'+document.body.innerText")
    import re
    check('気絶中' in txt and not re.search(r'残り|確率|33%|50%|カウント|ターン後', pg.evaluate("document.querySelector('#rbLou').outerHTML")), 'T15 no turns/probability/count in Lou DOM')
    # no support while fainted
    check(pg.evaluate("PrologueCombat.support()===false&&PrologueCombat.support('blessing')===false"), 'T5 support (incl. blessing) is a no-op while fainted')
    # repeat smash while fainted: no draw, count not changed (justFainted already consumed this round)
    d0 = pg.evaluate("BattleLouFaint.draws"); smash_round(pg); s = pg.evaluate(st)
    check(s['f'] and s['d'] == d0, 'T4 repeat smash while fainted = no RNG draw, still fainted', s)
    # T6: final blessing deferred while fainted
    pg.evaluate("PrologueCombat.enrageMoment()"); pg.wait_for_timeout(300)
    check(pg.evaluate("PrologueCombat.enragePending===true")  and pg.evaluate("BattleLouFaint.fainted"), 'T6 enrageMoment while fainted -> pending only')
    # Recovery timing. Fresh battle, faint on round R, then rounds R+1 (count1), R+2 (50% draw), R+3 (forced).
    for tag, draw, expect_at_r2 in [('0.49', 0.49, True), ('0.5', 0.5, False)]:
        fresh(pg, [0.1, draw, 0.9]); smash_round(pg)   # faint at end of round R (no increment)
        check(pg.evaluate("BattleLouFaint.fainted"), 'T2 [%s] fainted at R' % tag)
        pg.evaluate("rbQueued=false"); pg.evaluate("rbRound++")  # no-op placeholder to keep round counters moving
        # R+1 : plain enemy action
        def plain():
            pg.evaluate("rbHP=120;rbFHP=105;rbQueued=false;rbRound=1;window.__done=false;rbEnemyParty().then(()=>window.__done=true)")
            for _ in range(80):
                if pg.evaluate("document.body.classList.contains('dialogueOpen')"): pg.evaluate("closeDialogue()")
                if pg.evaluate("window.__done"): break
                pg.wait_for_timeout(400)
            settle(pg)
        d1 = pg.evaluate("BattleLouFaint.draws"); plain(); s1 = pg.evaluate(st)
        check(s1['f'] and s1['d'] == d1, 'T3 [%s] R+1: still fainted, no draw' % tag, s1)
        plain(); s2 = pg.evaluate(st)
        check(s2['d'] == d1 + 1, 'T4 [%s] R+2: exactly one recovery draw' % tag, s2)
        check((not s2['f']) == expect_at_r2, 'T4 [%s] R+2 recovery %s' % (tag, expect_at_r2), s2)
        if not expect_at_r2:
            plain(); s3 = pg.evaluate(st)
            check((not s3['f']) and s3['d'] == s2['d'], 'T5 R+3: guaranteed recovery without a draw', s3)
        check(pg.evaluate("BattleActorState.get('raider','lou')") != 'ko', 'recovered Lou returns to resting pose')
    # T6b: pending blessing resumes after wake
    fresh(pg, [0.1, 0.1]); smash_round(pg); pg.evaluate("PrologueCombat.enrageMoment()")
    for _ in range(3):
        if not pg.evaluate("BattleLouFaint.fainted"): break
        pg.evaluate("rbHP=120;rbFHP=105;rbQueued=false;rbRound=1;window.__done=false;rbEnemyParty().then(()=>window.__done=true)")
        for _ in range(80):
            if pg.evaluate("document.body.classList.contains('dialogueOpen')"): pg.evaluate("closeDialogue()")
            if pg.evaluate("window.__done"): break
            pg.wait_for_timeout(400)
        settle(pg)
    check(not pg.evaluate("BattleLouFaint.fainted") and pg.evaluate("PrologueCombat.enragePending===false"), 'T7 pending blessing ran after Lou woke (once)')
    # T10: victory while fainted
    fresh(pg, [0.1]); smash_round(pg)
    check(pg.evaluate("BattleActorState.set('lou','victory',{battle:'raider'})") and pg.evaluate("BattleActorState.get('raider','lou')") == 'victory' and not pg.evaluate("BattleActorState.fainted('raider','lou')"), 'T10 victory pose outranks faint (atomic)')
    # T11/T13: RNG is independent of Math.random and DEV-only
    fresh(pg); r = pg.evaluate("()=>{Math.random=()=>{throw new Error('Math.random used')};BattleLouFaint.fixSeed(7);BattleLouFaint.reset();const a=[];for(let i=0;i<3;i++){BattleLouFaint.judge();a.push(BattleLouFaint.fainted)};return a.length}")
    check(r == 3, 'T11 RNG does not touch Math.random')
    pg.close()
    pg = b.new_page(viewport={'width': 1280, 'height': 720}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(base + '/index.html'); pg.wait_for_function('window.PrologueCombat&&window.BattleLouFaint'); 
    pg.evaluate("BattleLouFaint.fixSeed(1);window.WINDBOUND_DEV=false")  # release build: fixed seed set earlier must be dropped
    check(pg.evaluate("BattleLouFaint.fixSeed(1)===false&&BattleLouFaint.setScript([0])===false"), 'T13 fixSeed/setScript refused with DEV off')
    check(pg.evaluate("()=>{BattleLouFaint.reset();BattleLouFaint.fixSeed;return BattleLouFaint.draws===0}"), 'T20 DEV off: reset drops the fixed seed/script')
    check(pg.evaluate("!!(BattleLouFaint.reset(),BattleLouFaint.judge,true)"), 'T21 reset before any draw does not throw')
    check(not errs, 'no page errors', errs[:3])
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)
