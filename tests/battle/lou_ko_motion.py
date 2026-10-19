"""Lou KO (lou_new_ko, formally adopted 10/16): 6 frames registered as lou/ko, plays once and holds the last frame in the Raider battle at PC / portrait / landscape.
Lou has no HP in the battle logic, so nothing in a normal battle may put her into KO; the motion only plays when ko is requested (DEV / future trigger).
Checks: 6 frame files; manifest def; KO plays >=6 distinct frames then holds 06; sync() does not restart or revive it; a normal battle round never sets Lou to ko; no 気絶/stun state or status type is introduced."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
fails = []
def check(ok, name, d=''):
    print(('ok   ' if ok else 'FAIL ') + name, d, flush=True)
    if not ok: fails.append(name)
cur = "()=>{const i=document.querySelector('#rbLou img');return i?i.src.split('/').pop():null}"
with server(8839) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or None))
    for vp, tag in [((1280, 720), 'pc'), ((390, 844), 'portrait'), ((844, 390), 'landscape')]:
        pg = b.new_page(viewport={'width': vp[0], 'height': vp[1]}); errs = []; bad = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('response', lambda r: bad.append(r.url) if r.status >= 400 else None)
        pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat'); pg.wait_for_timeout(1200); pg.evaluate("closeDialogue()")
        if tag == 'pc':
            r = pg.evaluate("""async()=>{const f=BattleMotion.frames('lou','ko');const bad=[];for(const u of f.urls){const x=await fetch(u);if(!x.ok)bad.push(u)}return {n:f.urls.length,bad,hold:f.hold,ms:f.ms}}""")
            check(r['n'] == 6 and not r['bad'] and r['hold'] == 'last', 'lou ko: 6 frame files, hold last', r)
            check(not pg.evaluate("BattleMotion.has('lou','stun')||BattleMotion.has('lou','faint')||BattleMotion.has('aidan','stun')"), 'no 気絶/stun motion state is registered (separate spec pending)')
            check(pg.evaluate("window.BattleStatus ? !BattleStatus.apply({battle:'raider',target:'lou',type:'stun',magnitude:0,remainingTurns:1,source:'x'}) : true"), 'BattleStatus still rejects a stun type (no logic change)')
        pg.evaluate("PrologueProgress.seed(0);startRaiderBattle()"); pg.wait_for_timeout(300)
        for _ in range(40):
            if pg.evaluate("document.body.classList.contains('dialogueOpen')"): pg.evaluate("closeDialogue()")
            if pg.evaluate("!document.body.classList.contains('battlePresentationBusy')&&!document.body.classList.contains('dialogueOpen')&&!document.body.classList.contains('actionCinematic')"): break
            pg.wait_for_timeout(500)
        pg.wait_for_function("!document.body.classList.contains('battlePresentationBusy')&&!document.body.classList.contains('dialogueOpen')&&!document.body.classList.contains('actionCinematic')", timeout=20000)
        pg.wait_for_timeout(500)
        check(pg.evaluate("BattleActorState.get('raider','lou')") != 'ko', '%s Lou is not KO in a fresh battle (no HP)' % tag)
        pg.evaluate("rbHP=0;rbFHP=0;BattleActorState.sync('raider','lou')"); pg.wait_for_timeout(200)
        check(pg.evaluate("BattleActorState.get('raider','lou')") != 'ko', '%s Lou does not KO when Aidan/Fiona HP hit 0 (logic unchanged)' % tag)
        pg.evaluate("rbHP=120;rbFHP=105")
        ok = pg.evaluate("BattleActorState.set('lou','ko',{battle:'raider'})"); s = []
        for _ in range(45):
            f = pg.evaluate(cur)
            if not s or s[-1] != f: s.append(f)
            pg.wait_for_timeout(40)
        ko = [x for x in s if x and '_ko_' in x]
        check(ok and len(set(ko)) == 6 and ko[-1].endswith('06.png') and pg.evaluate("BattleActorState.get('raider','lou')") == 'ko', '%s lou ko: plays 6 frames then holds 06' % tag, ko)
        pg.evaluate("BattleActorState.sync('raider','lou')"); pg.wait_for_timeout(500)
        check(pg.evaluate(cur) == 'lou_ko_06.png', '%s sync() keeps the final frame (no restart)' % tag)
        check(not errs, '%s no page errors' % tag, errs[:2]); check(not [u for u in bad if 'lou' in u], '%s no 4xx for lou assets' % tag, bad[:2])
        pg.close()
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)
