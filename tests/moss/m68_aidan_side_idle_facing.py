# FIELD-STATE-01: after a left/right walk, Aidan stops in idle art that faces the same way as the walk.
# Content check: the registered idle_<side> image must correlate with walk_<side>_01, not its opposite.
# Runtime check: keyboard walk -> release -> settled frame is the registered idle_<side>, with no post-release displacement.
import os, sys
from pathlib import Path
from urllib.parse import urlsplit
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
fails = []; errs = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
def head(path):
    im = Image.open(ROOT / urlsplit(path).path).convert('RGBA'); bb = im.getbbox(); cx = (bb[0] + bb[2]) // 2
    a = np.asarray(im.crop((cx - 300, bb[1], cx + 300, bb[1] + 420)).convert('L').resize((150, 105)), float)
    return (a - a.mean()) / a.std()
SETTLED = """(()=>{const i=[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden);return i?{src:i.dataset.src,mirror:i.style.transform.includes('scaleX')}:null})()"""
with server(8868) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    pg = b.new_page(viewport={'width': 1280, 'height': 720})
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(base + '/index.html?title=0'); pg.wait_for_function('window.AidanFieldAssets && window.MossForest && MossForest.active && !MossForest.busy', timeout=40000)
    frames = pg.evaluate("Object.fromEntries(Object.entries(AidanFieldAssets.frames).filter(([k])=>/^aidan_(idle_(left|right)|walk_(left|right)_01)$/.test(k)).map(([k,v])=>[k,v.path]))")
    for side, other in (('left', 'right'), ('right', 'left')):
        idle = head(frames['aidan_idle_' + side])
        same = float((idle * head(frames['aidan_walk_%s_01' % side])).mean()); opp = float((idle * head(frames['aidan_walk_%s_01' % other])).mean())
        check(same > opp + .2, 'registered idle_%s art faces %s (corr same=%.3f opposite=%.3f)' % (side, side, same, opp))
    pg.evaluate("typeof closeDialogue==='function'&&closeDialogue()"); pg.wait_for_timeout(600)
    for key, side in (('ArrowLeft', 'left'), ('ArrowRight', 'right'), ('ArrowLeft', 'left')):
        pg.keyboard.down(key); pg.wait_for_timeout(500)
        moving = pg.evaluate(SETTLED); pg.keyboard.up(key)
        released = pg.evaluate('MossForest.feet'); pg.wait_for_timeout(500)
        settled = pg.evaluate(SETTLED); after = pg.evaluate('MossForest.feet')
        check('walk_%s_' % side in moving['src'], '%s walk uses walk_%s (%s)' % (key, side, moving['src'].split('/')[-1]))
        check(released == after, '%s: no displacement after release %s -> %s' % (key, released, after))
        check(settled['src'] == frames['aidan_idle_' + side] and not settled['mirror'], '%s stop settles on registered idle_%s (%s)' % (key, side, settled['src'].split('/')[-1]))
    check(not errs, 'no page errors %s' % errs[:3])
    b.close()
print('FAILS %d' % len(fails)); sys.exit(1 if fails else 0)
