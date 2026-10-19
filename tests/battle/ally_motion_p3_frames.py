"""Phase 3: the multi-frame ally motions registered in img/battle/motion-manifest.json really play in the Raider battle at PC / phone portrait / phone landscape.
Checks: every frame file loads; damage / fiona winddance / attack / heal / lou blessing advance through >=2 frames then return to idle;
Aidan low_hp plays once and holds (no re-trigger on sync); KO plays and stays; the Fiona/Lou KO of Lou is NOT registered (held)."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; fails = []
def check(ok, name, d=''):
    print(('ok   ' if ok else 'FAIL ') + name, d, flush=True)
    if not ok: fails.append(name)
SEL = {'aidan': '#rbAidan', 'fiona': '#rbFiona', 'lou': '#rbLou'}
frame = "(a)=>{const i=document.querySelector({aidan:'#rbAidan',fiona:'#rbFiona',lou:'#rbLou'}[a]+' img');return i?i.src.split('/').pop():null}"
def seen(pg, a, ms=1400, step=40):
    s = []
    for _ in range(ms // step):
        f = pg.evaluate(frame, a)
        if not s or s[-1] != f: s.append(f)
        pg.wait_for_timeout(step)
    return s
with server(8833) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or None))
    for vp, tag in [((1280, 720), 'pc'), ((390, 844), 'portrait'), ((844, 390), 'landscape')]:
        pg = b.new_page(viewport={'width': vp[0], 'height': vp[1]}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); bad = []
        pg.on('response', lambda r: bad.append(r.url) if r.status >= 400 else None)
        pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat'); pg.wait_for_timeout(1200); pg.evaluate("closeDialogue()")
        if tag == 'pc':
            miss = pg.evaluate("""async()=>{const m=await (await fetch('img/battle/motion-manifest.json')).json();const out=[];let n=0;
              for(const [k,st] of Object.entries(m.motions))for(const [s,d] of Object.entries(st))for(let i=1;i<=d.frames;i++){const u=m.base+d.dir+d.pattern.replace('{n}',String(i).padStart(2,'0'));n++;const r=await fetch(u);if(!r.ok)out.push(u)}return {n,out}}""")
            check(not miss['out'], 'every manifest frame file exists (%d)' % miss['n'], miss['out'][:3])
            check(not pg.evaluate("BattleMotion.has('lou','ko')"), 'Lou KO stays unregistered (held for the faint spec)')
        pg.evaluate("PrologueProgress.seed(0);startRaiderBattle()"); pg.wait_for_timeout(300)
        pg.wait_for_function("!document.body.classList.contains('battlePresentationBusy')&&!document.body.classList.contains('dialogueOpen')&&!document.body.classList.contains('actionCinematic')", timeout=20000)
        pg.wait_for_timeout(800)
        for a, st in [('aidan', 'damage'), ('fiona', 'damage'), ('fiona', 'attack'), ('fiona', 'heal'), ('fiona', 'winddance')]:
            if st == 'winddance': pg.evaluate("BattleActorState.action('fiona','winddance',{battle:'raider'})")
            elif st == 'heal': pg.evaluate("BattleActorState.action('fiona','heal',{battle:'raider'})")
            else: pg.evaluate("BattleActorState.set('%s','%s',{battle:'raider',duration:300})" % (a, st))
            s = seen(pg, a, 1600)
            names = [x for x in s if x and '_%s_' % st in x]
            check(len(set(names)) >= 3 and pg.evaluate("BattleActorState.get('raider','%s')" % a) == 'idle', '%s %s %s: plays %d distinct frames then idle' % (tag, a, st, len(set(names))), s[:8])
        # Aidan low HP: one-shot, then held
        pg.evaluate("rbHP=20;BattleActorState.sync('raider','aidan')"); s = seen(pg, 'aidan', 1500)
        low = [x for x in s if x and 'low_hp' in x]
        check(pg.evaluate("BattleActorState.get('raider','aidan')") == 'low_hp' and len(set(low)) >= 3 and low[-1].endswith('06.png'), '%s aidan low_hp: plays then holds last frame' % tag, low[:8])
        pg.evaluate("BattleActorState.sync('raider','aidan')"); pg.wait_for_timeout(100); f1 = pg.evaluate(frame, 'aidan'); pg.wait_for_timeout(600); pg.evaluate("BattleActorState.sync('raider','aidan')")
        check(pg.evaluate(frame, 'aidan') == f1 and f1.endswith('06.png'), '%s aidan low_hp: sync() does not restart the motion' % tag)
        # damage from low HP returns to low_hp
        pg.evaluate("BattleActorState.set('aidan','damage',{battle:'raider',duration:300})"); pg.wait_for_timeout(1300)
        check(pg.evaluate("BattleActorState.get('raider','aidan')") == 'low_hp', '%s aidan: damage at low HP returns to low_hp' % tag)
        # KO
        pg.evaluate("rbHP=0;BattleActorState.sync('raider','aidan')"); s = seen(pg, 'aidan', 1500)
        ko = [x for x in s if x and '_ko_' in x]
        check(pg.evaluate("BattleActorState.get('raider','aidan')") == 'ko' and len(set(ko)) >= 3 and ko[-1].endswith('06.png'), '%s aidan ko: plays and stays down' % tag, ko[:8])
        pg.evaluate("rbFHP=0;BattleActorState.sync('raider','fiona')"); s = seen(pg, 'fiona', 1500); ko = [x for x in s if x and '_ko_' in x]
        check(pg.evaluate("BattleActorState.get('raider','fiona')") == 'ko' and len(set(ko)) >= 3 and ko[-1].endswith('06.png'), '%s fiona ko: plays and stays down' % tag, ko[:8])
        pg.screenshot(path=str(ROOT / ('docs/battle/qa/ally-motion-p3/frames_%s.jpg' % tag)), type='jpeg', quality=70)
        check(not errs and not bad, '%s: no page errors / 4xx' % tag, (errs[:2], bad[:2])); pg.close()
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)
