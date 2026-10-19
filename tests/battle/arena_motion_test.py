"""ARENA-MOTION-01: DEV motion test inside the existing arena panel. Real browser at PC / phone portrait / phone landscape.
Access (DEV > MONSTER ARENA > モーションテスト), 6 characters, computed statuses (delivered-but-unusable is never 'implemented'),
play / pause / stop / restart / loop / frame step / speed, start->idle, attack->idle, damage->idle, KO stop, KO dissolve hide, foot position,
image-load-failure fallback, no overlap of stage and panel, independence from save data / HP / TP / flags, existing arena buttons intact."""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; fails = []
OUT = ROOT / 'docs/battle/qa/arena-motion-01'; OUT.mkdir(parents=True, exist_ok=True)
def check(ok, name, d=''):
    print(('ok   ' if ok else 'FAIL ') + name, d, flush=True)
    if not ok: fails.append(name)
SNAP = "MotionTest.snapshot()"
GUARD = """()=>{const o={};try{o.ls=JSON.stringify(Object.fromEntries(Object.entries(localStorage).sort()))}catch(e){o.ls='x'}
 for(const k of ['aahp','rbHP','rbFHP','normalFHP','gghp','rbBoss']){try{o[k]=eval(k)}catch(e){o[k]='-'}}
 try{o.cls=[...document.body.classList].filter(c=>/battle|raider/i.test(c)).join(' ')}catch(e){}
 try{o.prog=JSON.stringify(window.PrologueProgress&&PrologueProgress.state?PrologueProgress.state():null)}catch(e){o.prog='x'}
 return JSON.stringify(o)}"""
def wait_idx(pg, n, to=3000):
    pg.wait_for_function("(n)=>MotionTest.snapshot().idx>=n", arg=n, timeout=to)
with server(8837) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or None))
    for vp, tag in [((1280, 720), 'pc'), ((390, 844), 'portrait'), ((844, 390), 'landscape')]:
        pg = b.new_page(viewport={'width': vp[0], 'height': vp[1]}); errs = []; fail404 = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('response', lambda r: fail404.append(r.url) if r.status >= 400 else None)
        pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.MotionTest&&BattleMotion.loaded'); pg.wait_for_timeout(1000); pg.evaluate('closeDialogue()')
        before = pg.evaluate(GUARD)
        # existing arena buttons intact
        pg.click('#devBtn')
        have = pg.evaluate("[...document.querySelectorAll('#devArena [data-arena]')].map(b=>b.dataset.arena)")
        check(all(k in have for k in ['go', 'clear', 'freeze', 'place', 'all']) and 'motion' in have, '%s: existing arena buttons kept + motion test button' % tag, have)
        pg.click('#devMotionTest'); pg.wait_for_selector('#motionTest.open'); pg.wait_for_timeout(500)
        # layout: stage and panel never overlap, controls reachable
        lay = pg.evaluate("""()=>{const r=s=>{const e=document.querySelector(s).getBoundingClientRect();return {l:e.left,t:e.top,r:e.right,b:e.bottom}};return {st:r('#motionTest .mtStageWrap'),pn:r('#motionTest .mtPanel'),ctl:r('#motionTest .mtCtlBox'),vw:innerWidth,vh:innerHeight,sw:document.documentElement.scrollWidth}}""")
        ov = not (lay['st']['r'] <= lay['pn']['l'] + 1 or lay['st']['b'] <= lay['pn']['t'] + 1)
        check(not ov and lay['ctl']['b'] <= lay['vh'] + 1 and lay['ctl']['r'] <= lay['vw'] + 1 and lay['sw'] <= lay['vw'], '%s: stage and panel do not overlap; controls on screen; no horizontal overflow' % tag, lay)
        # tap-select (real clicks)
        pg.click('#motionTest [data-char=aidan]'); pg.wait_for_timeout(200)
        pg.click('#motionTest .mtRow[data-slot=attack]'); pg.wait_for_timeout(150)
        s = pg.evaluate(SNAP); check(s['char'] == 'aidan' and s['slot'] == 'attack' and s['status'] == 'impl' and s['total'] == 6, '%s: tap selects character + motion (aidan attack, 6f impl)' % tag, s)
        pg.screenshot(path=str(OUT / ('arena_motion_%s.png' % tag)))
        if tag != 'pc':
            check(not errs and not fail404, '%s: no page errors / 4xx' % tag, (errs[:2], fail404[:2])); 
            pg.keyboard.press('Escape'); pg.wait_for_timeout(100); check(not pg.evaluate('MotionTest.isOpen'), '%s: Esc closes' % tag); pg.close(); continue
        # ---- statuses per character (computed, never 'implemented' for delivered-only)
        def st(c, slot, state=None, label=None):
            rows = pg.evaluate("MotionTest.rows('%s')" % c)
            return [r['status'] for r in rows if r['slot'] == slot and (state is None or r['state'] == state) and (label is None or r['label'] == label)]
        exp = [('aidan', 'start', 'draw', 'impl'), ('aidan', 'idle', 'idle', 'impl'), ('aidan', 'attack', 'attack', 'impl'), ('aidan', 'skill', 'skill', 'impl'), ('aidan', 'damage', 'damage', 'impl'), ('aidan', 'low_hp', 'low_hp', 'impl'), ('aidan', 'ko', 'ko', 'impl'), ('aidan', 'victory', 'victory', 'still'), ('aidan', 'ko_dissolve', None, 'none'), ('aidan', 'support', 'item', 'still'),
               ('fiona', 'start', 'ready', 'impl'), ('fiona', 'idle', 'idle', 'impl'), ('fiona', 'attack', 'attack', 'impl'), ('fiona', 'skill', 'winddance', 'impl'), ('fiona', 'skill', 'skill', 'still'), ('fiona', 'support', 'heal', 'impl'), ('fiona', 'damage', 'damage', 'impl'), ('fiona', 'low_hp', 'low_hp', 'still'), ('fiona', 'ko', 'ko', 'impl'),
               ('lou', 'idle', 'idle', 'impl'), ('lou', 'damage', 'damage', 'impl'), ('lou', 'support', 'blessing', 'impl'), ('lou', 'support', 'heal', 'still'), ('lou', 'ko', 'ko', 'still'), ('lou', 'attack', None, 'none'),
               ('goblin', 'idle', 'idle', 'still'), ('goblin', 'ko', 'ko', 'impl'), ('goblin', 'ko_dissolve', 'ko', 'impl'), ('goblin', 'damage', 'damage', 'still'),
               ('tainted_goblin', 'ko_dissolve', 'ko', 'impl'), ('tainted_goblin', 'attack', 'attack', 'still'),
               ('goblin_raider', 'idle', 'idle', 'impl'), ('goblin_raider', 'attack', 'attack', 'impl'), ('goblin_raider', 'skill', 'call', 'impl'), ('goblin_raider', 'skill', 'enrage', 'impl'), ('goblin_raider', 'damage', 'damage', 'impl'), ('goblin_raider', 'ko', 'ko', 'still'), ('goblin_raider', 'ko_dissolve', None, 'pending')]
        bad = [(c, sl, stt, e, st(c, sl, stt)) for c, sl, stt, e in exp if e not in st(c, sl, stt)]
        check(not bad, 'status table (%d expectations)' % len(exp), bad[:4])
        check('delivered' in st('lou', 'ko') and 'delivered' not in st('goblin_raider', 'attack') and 'pending' in st('goblin_raider', 'attack') and 'pending' in st('goblin_raider', 'ko_dissolve'), 'delivered / pending-adoption material listed but never shown as implemented')
        check(all(pg.evaluate("MotionTest.select('%s','%s',%s)" % (c, sl, json.dumps(stt))) is not None for c, sl, stt, e in exp if e in ('impl', 'still')), 'every implemented / still row can be selected (all 6 characters)')
        # ---- controls on aidan attack
        pg.evaluate("MotionTest.select('aidan','attack','attack');MotionTest.control.returnIdle(false)"); pg.wait_for_timeout(100)
        s0 = pg.evaluate(SNAP); wait_idx(pg, 2); pg.click('#motionTest [data-mt=pause]'); a = pg.evaluate(SNAP); pg.wait_for_timeout(400); c2 = pg.evaluate(SNAP)
        check(not a['playing'] and a['idx'] == c2['idx'], 'pause holds the frame', (a['idx'], c2['idx']))
        pg.click('#motionTest [data-mt=next]'); n1 = pg.evaluate(SNAP); pg.click('#motionTest [data-mt=prev]'); n2 = pg.evaluate(SNAP)
        check(n1['idx'] == (a['idx'] + 1) % 6 and n2['idx'] == a['idx'] and not n1['playing'], 'step forward / back by one frame', (a['idx'], n1['idx'], n2['idx']))
        shown = pg.evaluate("[document.querySelector('#motionTest [data-mt=cf]').textContent,document.querySelector('#motionTest [data-mt=ct]').textContent,document.querySelector('#motionTest [data-mt=cms]').textContent]")
        man = pg.evaluate("BattleMotion.frames('aidan','attack').ms")
        check(shown[1] == '6' and int(shown[0]) == n2['idx'] + 1 and int(shown[2]) == man[n2['idx']], 'frame number / total / per-frame ms displayed from the manifest', (shown, man))
        pg.click('#motionTest [data-mt=restart]'); r = pg.evaluate(SNAP); check(r['playing'] and r['idx'] <= 1, 'restart plays from the first frame', r)
        pg.wait_for_timeout(1200); e = pg.evaluate(SNAP); check(not e['playing'] and e['idx'] == 5, 'one-shot ends holding the last frame (loop OFF, return OFF)', e)
        pg.click('#motionTest [data-mt=stop]'); z = pg.evaluate(SNAP); check(not z['playing'] and z['idx'] == 0, 'stop returns to frame 1', z)
        pg.click('#motionTest [data-mt=loop]'); pg.click('#motionTest [data-mt=play]'); pg.wait_for_timeout(1700); l = pg.evaluate(SNAP); check(l['playing'] and l['loop'], 'loop ON keeps playing past the last frame', l)
        pg.click('#motionTest [data-mt=loop]'); pg.click('#motionTest [data-mt=stop]')
        # speed
        import time
        def dur(speed):
            pg.evaluate("MotionTest.control.speed(%s);MotionTest.control.restart()" % speed); t = time.time()
            pg.wait_for_function("!MotionTest.snapshot().playing", timeout=5000); return time.time() - t
        d1, d2, dh = dur(1), dur(2), dur(0.5)
        check(d2 < d1 * 0.75 and dh > d1 * 1.5, 'speed 0.5x / 1x / 2x change the playback time', (round(dh, 2), round(d1, 2), round(d2, 2)))
        pg.evaluate("MotionTest.control.speed(1)")
        # ---- returns to idle
        for ch, slot, state in [('aidan', 'start', 'draw'), ('fiona', 'start', 'ready'), ('aidan', 'attack', 'attack'), ('fiona', 'attack', 'attack'), ('aidan', 'damage', 'damage'), ('fiona', 'damage', 'damage'), ('lou', 'damage', 'damage')]:
            pg.evaluate("MotionTest.select('%s','%s','%s')" % (ch, slot, state)); pg.evaluate("MotionTest.control.returnIdle(true);MotionTest.control.restart()")
            pg.wait_for_function("MotionTest.snapshot().curSlot==='idle'", timeout=4000); pg.wait_for_timeout(500); s = pg.evaluate(SNAP)
            check(s['curSlot'] == 'idle' and s['loop'] and s['playing'] and s['total'] >= 2, '%s %s -> idle loop' % (ch, state), (s['phase'], s['idx']))
        # ---- KO: plays once and stops; dissolve hides
        pg.evaluate("MotionTest.select('aidan','ko','ko')"); pg.wait_for_function("!MotionTest.snapshot().playing", timeout=4000); k = pg.evaluate(SNAP)
        check(k['idx'] == 5 and not k['gone'] and k['curSlot'] == 'ko', 'aidan KO plays once and stops on the last frame', k)
        pg.evaluate("MotionTest.select('goblin','ko_dissolve','ko')"); pg.wait_for_function("MotionTest.snapshot().gone", timeout=4000)
        k = pg.evaluate(SNAP); hid = pg.evaluate("getComputedStyle(document.querySelector('#motionTest .mtImg')).visibility")
        check(k['gone'] and hid == 'hidden' and not k['playing'], 'goblin KO dissolve: sprite hidden after the last frame', (k['phase'], hid))
        pg.evaluate("MotionTest.control.restart()"); pg.wait_for_timeout(150); hid2 = pg.evaluate("getComputedStyle(document.querySelector('#motionTest .mtImg')).visibility")
        check(hid2 == 'visible', 'restart revives the dissolved sprite')
        # ---- foot position while looping
        for ch, slot, state in [('aidan', 'idle', 'idle'), ('fiona', 'idle', 'idle'), ('lou', 'idle', 'idle'), ('aidan', 'attack', 'attack'), ('fiona', 'damage', 'damage')]:
            pg.evaluate("MotionTest.select('%s','%s','%s')" % (ch, slot, state)); pg.wait_for_function("MotionTest.snapshot().footSpread!==undefined&&MotionTest.snapshot().footSpread!==null", timeout=4000); f = pg.evaluate(SNAP)['footSpread']
            check(f is not None and f <= 12, '%s %s: foot position stays within 12px on screen across frames' % (ch, state), f)
        # ---- image load failure -> still fallback
        pg.route('**/fiona_damage_03.png', lambda r: r.abort())
        pg.evaluate("MotionTest.select('fiona','damage','damage');MotionTest.control.returnIdle(false);MotionTest.control.restart()"); pg.wait_for_timeout(1500); w = pg.evaluate(SNAP); src = pg.evaluate("document.querySelector('#motionTest .mtImg').getAttribute('src')"); fb = pg.evaluate("document.querySelector('#motionTest .mtImg').dataset.fallback")
        check(any('fiona_damage_03' in x for x in w['warn']), 'load failure is reported', w['warn'])
        check(fb == '1' and bool(src), 'fallback to the still was applied and an image stays on screen', (fb, src))
        pg.unroute('**/fiona_damage_03.png')
        # ---- independence
        pg.evaluate("MotionTest.select('aidan','skill','skill')"); pg.wait_for_timeout(1500)
        after = pg.evaluate(GUARD); check(after == before, 'no save data / localStorage / HP / TP / flag change while testing', (before[:120], after[:120]) if after != before else '')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
        check(not pg.evaluate('MotionTest.isOpen') and pg.evaluate("getComputedStyle(document.querySelector('#devPanel')).display") == 'block', 'Esc closes and returns to the arena panel')
        check(not errs and not fail404, '%s: no page errors / 4xx' % tag, (errs[:2], fail404[:2])); pg.close()
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)
