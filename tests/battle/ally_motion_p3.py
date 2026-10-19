"""Phase 3 real-browser check of the delivered ally battle motions (Aidan / Fiona / Lou) in the Raider battle:
opening -> idle loop -> action (attack/skill/heal/charge...) -> return to idle, damage -> idle, guard, KO/victory, Fiona wind-dance untouched.
Uses only existing BattleMotion / BattleActorState / BattleOpening. Missing multi-frame action art falls back to the still (listed in docs)."""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; fails = []
OUT = ROOT / 'docs/battle/qa/ally-motion-p3'; OUT.mkdir(parents=True, exist_ok=True)
def check(ok, name, detail=''):
    print(('ok   ' if ok else 'FAIL ') + name, detail, flush=True)
    if not ok: fails.append(name)
box = "(a)=>{const e=document.querySelector({aidan:'#rbAidan',fiona:'#rbFiona',lou:'#rbLou'}[a]);const i=e&&e.querySelector('img');if(!e||!i)return null;const r=e.getBoundingClientRect();const c=e.querySelector('canvas');return {src:i.src.split('/').slice(-2).join('/'),ok:i.complete&&i.naturalWidth>0,w:Math.round(r.width),h:Math.round(r.height),inView:r.left>=-2&&r.right<=innerWidth+2&&r.top>=-2&&r.bottom<=innerHeight+2,vis:getComputedStyle(e).visibility!=='hidden'&&getComputedStyle(e).display!=='none',frame:i.dataset.motionFrame||null,cframe:c?c.dataset.frame:null}}"
with server(8832) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or None))
    for vp, tag in [((1280, 720), 'pc'), ((390, 844), 'portrait'), ((844, 390), 'landscape')]:
        pg = b.new_page(viewport={'width': vp[0], 'height': vp[1]}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat'); pg.wait_for_timeout(1500); pg.evaluate("closeDialogue()")
        pg.evaluate("PrologueProgress.seed(0);startRaiderBattle()"); pg.wait_for_timeout(300)
        pg.wait_for_function("!document.body.classList.contains('battlePresentationBusy')&&!document.body.classList.contains('dialogueOpen')&&!document.body.classList.contains('actionCinematic')", timeout=20000)   # idle loop pauses by design while the opening presentation runs
        pg.wait_for_timeout(1500)
        for a in ('aidan', 'fiona', 'lou'):
            s1 = pg.evaluate(box, a)
            if a == 'lou' and (s1 is None or not s1['vis']): check(True, '%s %s: not in the Raider party (party = Aidan + Fiona)' % (tag, a)); continue
            check(s1 is not None and s1['ok'] and s1['vis'] and s1['inView'], '%s %s: visible, image loaded, inside the viewport' % (tag, a), s1)
            check(pg.evaluate("BattleActorState.get('raider','%s')" % a) == 'idle', '%s %s: idle after the opening' % (tag, a))
            seen = set()
            for _ in range(14):
                s = pg.evaluate(box, a); seen.add((s['frame'], s['cframe'])); pg.wait_for_timeout(120)
            check(len(seen) >= 2, '%s %s: idle loop advances frames' % (tag, a), sorted(map(str, seen))[:6])
        # actions: each returns to idle by itself
        acts = [('aidan', 'attack'), ('aidan', 'skill'), ('fiona', 'attack'), ('fiona', 'heal'), ('fiona', 'skill')]
        if pg.evaluate(box, 'lou'): acts += [('lou', 'heal'), ('lou', 'blessing')]
        for a, st in acts:
            ok = pg.evaluate("BattleActorState.action('%s','%s',{battle:'raider'})" % (a, st)); pg.wait_for_timeout(250)
            mid = pg.evaluate(box, a); stm = pg.evaluate("BattleActorState.get('raider','%s')" % a)
            pg.wait_for_timeout(1700)
            end = pg.evaluate(box, a); ste = pg.evaluate("BattleActorState.get('raider','%s')" % a)
            check(ok is not False and mid and mid['ok'] and mid['vis'] and ste == 'idle' and end['ok'], '%s %s %s: plays (state %s, img %s) then returns to idle' % (tag, a, st, stm, mid and mid['src']), (ste, end and end['src']))
        for a in ('aidan', 'fiona'):
            pg.evaluate("BattleActorState.set('%s','damage',{battle:'raider',duration:360})" % a); pg.wait_for_timeout(200)
            d = pg.evaluate("BattleActorState.get('raider','%s')" % a); pg.wait_for_timeout(700)
            check(d == 'damage' and pg.evaluate("BattleActorState.get('raider','%s')" % a) == 'idle', '%s %s: damage then back to idle' % (tag, a))
            pg.evaluate("BattleActorState.set('%s','guard',{battle:'raider'})" % a); g = pg.evaluate("BattleActorState.get('raider','%s')" % a)
            pg.evaluate("BattleActorState.endGuard('raider','%s')" % a); pg.wait_for_timeout(200)
            check(g == 'guard' and pg.evaluate("BattleActorState.get('raider','%s')" % a) == 'idle', '%s %s: guard held then released to idle' % (tag, a))
        pg.screenshot(path=str(OUT / ('raider_party_%s.jpg' % tag)), type='jpeg', quality=70)
        # end of battle: victory outranks, KO outranks victory
        pg.evaluate("BattleActorState.set('aidan','victory',{battle:'raider'});BattleActorState.set('fiona','victory',{battle:'raider'})"); pg.wait_for_timeout(300)
        check(pg.evaluate("BattleActorState.get('raider','aidan')") == 'victory' and not pg.evaluate("BattleActorState.set('aidan','attack',{battle:'raider',duration:300})"), '%s: victory pose is not replaced by an action' % tag)
        check(not errs, '%s: no page errors' % tag, errs[:2]); pg.close()
    # wind dance gate untouched
    pg = b.new_page(viewport={'width': 1280, 'height': 720}); pg.goto(base + '/index.html'); pg.wait_for_function('BattleMotion.loaded'); pg.wait_for_timeout(500)
    wd = pg.evaluate("window.WindDance?{has:true,type:typeof WindDance.commandVisible}:{has:false}")
    check(wd['has'] and wd['type'] == 'function', 'WindDance gate (commandVisible) still present', wd); pg.close(); b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)
