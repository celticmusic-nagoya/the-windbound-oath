"""Raider party wipe -> Lou rewinds time -> the same battle restarts (DIRECTIVE-17D P0).
Regression: BattleLoading.start() refuses while battleMode is on, so the wipe's restart was refused and the battle stalled forever
(HP 0, command lock on, no restart). Covers wipe -> rematch -> victory, wipe -> rematch -> wipe again -> rematch, PC and phone portrait.
Run with QA_OUT outside the checkout (tools/qa/run_regressions.py sets PORT; this test serves the checkout itself).
"""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ['QA_OUT']).resolve(); OUT.mkdir(parents=True, exist_ok=True)
rows, errors = [], []
def ck(name, ok, info=''):
    rows.append({'name': name, 'status': 'PASS' if ok else 'FAIL', 'info': str(info)[:300]})
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else '  ' + str(info)[:300]), flush=True)
    (OUT / 'raider_wipe_rematch.json').write_text(json.dumps(rows, indent=1, ensure_ascii=False))
STATE = "({hp:rbHP,fhp:rbFHP,mp:rbFMP,tp:rbTP,boss:rbBoss,round:rbRound,actor:rbActor,busy:rbBusy,adds:rbAdds,locked:battleCommandLocked('raider'),loading:BattleLoading.phase,shown:document.querySelector('#raiderBattle').style.display!=='none',raider:document.body.classList.contains('raiderBattleMode'),stage:storyStage,result:getComputedStyle(document.querySelector('#battleResult')).display!=='none'})"
def act(p, kind='atk'):
    """one party round: Aidan and Fiona both use `kind` (auto-target the boss)"""
    for who in ('aidan', 'fiona'):
        p.wait_for_function("w=>rbActor===w&&!rbBusy&&!battleCommandLocked('raider')", arg=who, timeout=15000)
        p.evaluate("k=>choosePartyAct(k,'raider_enemy_0')", kind)
def wipe(p, tag):
    """take the party to 1 HP with no dodge, end the round, and wait for the rematch"""
    p.evaluate("rbHP=1;rbFHP=1;updateRaider();window.__rnd=Math.random;Math.random=()=>0.99")
    act(p, 'atk')
    p.wait_for_function("rbHP<=0||rbFHP<=0", timeout=30000)
    ck(f'{tag}: party wiped (HP 0)', True)
    try: p.wait_for_function("rbHP===120&&rbFHP===105&&rbRound===1&&rbActor==='aidan'", timeout=8000); ok = True
    except Exception: ok = False
    s = p.evaluate(STATE); p.evaluate("Math.random=window.__rnd")
    ck(f'{tag}: the battle restarts (fresh HP/MP/TP, boss 1250, round 1, no reinforcements)', ok and s['mp'] == 36 and s['tp'] == 0 and s['boss'] == 1250 and s['adds'] == 0 and s['shown'] and s['raider'], s)
    try: p.wait_for_function("!battleCommandLocked('raider')&&!rbBusy", timeout=15000); ok = True
    except Exception: ok = False
    ck(f'{tag}: commands usable again after the opening', ok, p.evaluate(STATE))
    p.wait_for_timeout(3000); s = p.evaluate(STATE)
    ck(f'{tag}: no stale enemy turn from the wiped battle (3 s idle: HP full, still round 1)', s['hp'] == 120 and s['fhp'] == 105 and s['round'] == 1 and not s['busy'], s)
with server(int(os.environ.get('PORT', '8941'))) as base, sync_playwright() as pw:
    b = pw.chromium.launch()
    for label, w, h, touch in [('pc', 1280, 720, False), ('portrait', 390, 844, True)]:
        ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=touch); p = ctx.new_page()
        p.on('pageerror', lambda e: errors.append(str(e))); p.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        p.goto(base + '/index.html?dev=1&title=0#field'); p.wait_for_function("LoadCoordinator.phase==='READY'")
        ck(f'{label}: raider battle starts', p.evaluate("async()=>{closeDialogue();storyStage=12;return await startRaiderBattle()}") is True)
        p.wait_for_function("!battleCommandLocked('raider')", timeout=15000)
        # 1 wipe -> rematch -> wipe again -> rematch
        wipe(p, f'{label}/wipe1'); wipe(p, f'{label}/wipe2')
        # 2 rematch -> victory -> result -> back to the story
        p.evaluate("rbBoss=1;updateRaider();window.__rnd=Math.random;Math.random=()=>0.0")
        act(p, 'atk')
        try: p.wait_for_function("getComputedStyle(document.querySelector('#battleResult')).display!=='none'", timeout=30000); ok = True
        except Exception: ok = False
        p.evaluate("Math.random=window.__rnd")
        ck(f'{label}: rematch won -> result screen', ok, p.evaluate(STATE))
        p.screenshot(path=str(OUT / f'raider_rematch_victory_{label}.png'))
        for _ in range(6):
            if p.evaluate("getComputedStyle(document.querySelector('#battleResult')).display==='none'"): break
            p.evaluate("document.querySelector('#battleResult button, #battleResult')?.click()"); p.keyboard.press('Enter'); p.wait_for_timeout(700)
        p.wait_for_timeout(1000); s = p.evaluate(STATE)
        ck(f'{label}: after the result the battle is closed (no battle mode, raider hidden)', not s['raider'] and not s['shown'] and not s['result'], s)
        ctx.close()
    errs = [e for e in errors if 'Failed to load resource' not in e]
    ck('no page errors / console errors', not errs, errs[:3])
    b.close()
fails = [r for r in rows if r['status'] == 'FAIL']
print('FAILS', len(fails)); raise SystemExit(1 if fails else 0)
