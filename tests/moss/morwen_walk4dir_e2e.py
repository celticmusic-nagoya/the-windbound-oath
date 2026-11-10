# MORWEN-WALK-4DIR e2e (playwright). Branch on :8765, reference main worktree on :8766 (python3 -m http.server).
# 1) flag OFF: globals / forest DOM / console errors / localStorage keys identical to main.
# 2) flag ON: one walker element, 4-direction travel shows left / right / up banks (down keeps the side), no errors,
#    localStorage unchanged (SAVE untouched), other actors (#forestPlayer, #forestFiona) still present.
import sys, json
from playwright.sync_api import sync_playwright
fails = []; out = {}
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
def snap(pg):
    return pg.evaluate("""(()=>({globals:Object.keys(window).filter(k=>/^[A-Z]/.test(k)).sort(),
      forest:[...document.querySelectorAll('#forestWorld > *')].map(e=>e.id||e.className).sort(),
      storage:Object.keys(localStorage).sort()}))()""")
def open_forest(p, port, flag):
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1000, 'height': 640}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.goto(f'http://localhost:{port}/index.html?title=0' + ('&morwenWalk4=1' if flag else '')); pg.wait_for_timeout(900)
    pg.evaluate("devJump('map:dev_monster_arena')"); pg.wait_for_function('MossForest.active && !MossForest.busy', timeout=30000)
    pg.wait_for_timeout(700); pg.evaluate('closeDialogue()')
    return b, pg, errs
with sync_playwright() as p:
    b0, m0, e0 = open_forest(p, 8766, False); s_main = snap(m0); b0.close()
    b1, m1, e1 = open_forest(p, 8765, False); s_off = snap(m1); b1.close()
    check(s_main['globals'] == s_off['globals'], 'flag OFF: global names identical to main (%d)' % len(s_off['globals']))
    check(s_main['forest'] == s_off['forest'], 'flag OFF: forest DOM identical to main')
    check(s_main['storage'] == s_off['storage'], 'flag OFF: localStorage keys identical to main')
    check(len(e0) == len(e1), 'flag OFF: console errors main %d / branch %d' % (len(e0), len(e1)))
    b2, pg, e2 = open_forest(p, 8765, True)
    st0 = pg.evaluate('JSON.stringify(localStorage)')
    check(pg.evaluate("document.querySelectorAll('#forestMorwenWalk4Dev').length") == 1, 'flag ON: one walker element')
    seen = {}
    for key, want in (('ArrowRight', 'right'), ('ArrowUp', 'up'), ('ArrowLeft', 'left'), ('ArrowDown', 'side'), ('ArrowRight', 'right')):
        pg.keyboard.down(key); fr = set(); faces = set()
        for i in range(24):
            pg.wait_for_timeout(50)
            d = pg.evaluate("(()=>{const e=document.querySelector('#forestMorwenWalk4Dev');const v=[...e.querySelectorAll('img')].filter(i=>!i.hidden);return [e.dataset.face,e.dataset.frame,v.length,v[0]?v[0].getAttribute('src'):'']})()")
            faces.add(d[0]); fr.add(int(d[1])); check(d[2] <= 1, 'one visible frame') if d[2] > 1 else None
            last = d
        pg.keyboard.up(key); pg.wait_for_timeout(400)
        seen[key + ':' + want] = dict(faces=sorted(faces), frames=sorted(fr), src=last[3])
        ok_face = (want in faces) if want != 'side' else (faces <= {'left', 'right', 'up'} and 'down' not in faces)
        check(ok_face and len(fr) >= 4, f'{key}: facing {sorted(faces)} frames {sorted(fr)}')
        pg.screenshot(path=f'/tmp/aw/walk4_{key}.png')
    pg.wait_for_timeout(600)
    d = pg.evaluate("(()=>{const e=document.querySelector('#forestMorwenWalk4Dev');return [e.dataset.moving,e.dataset.frame]})()")
    check(d[0] == 'false' and int(d[1]) % 6 == 0, 'stopped on a contact frame (F%s)' % d[1])
    check(pg.evaluate('JSON.stringify(localStorage)') == st0, 'flag ON: localStorage unchanged (SAVE untouched)')
    check(pg.evaluate("!!document.querySelector('#forestPlayer') && !!document.querySelector('#forestFiona')"), 'player / Fiona still present')
    real = [e for e in e2 if 'favicon' not in e]
    check(len(real) <= len(e1), 'flag ON: no new console errors %s' % real[:2])
    out = dict(main=s_main, off=s_off, seen=seen, errors_on=real)
    b2.close()
json.dump(out, open('/tmp/aw/walk4_e2e.json', 'w'), ensure_ascii=False, indent=1)
print('FAILS %d' % len(fails)); sys.exit(1 if fails else 0)
