# Phase 1 height-level prototype (dev_height_proto): levels, connectors, no-clip, level-aware tap-to-move, draw order, save round trip.
# Env: PORT (8765), OUT (screenshot dir; default docs/qa/field-height-proto), PERF=1 adds the frame-time section.
import os, json, random
from playwright.sync_api import sync_playwright
PORT = os.environ.get('PORT', '8765'); OUT = os.environ.get('OUT', 'docs/qa/field-height-proto'); os.makedirs(OUT, exist_ok=True)
fails = []; errs = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
VIEWS = {'pc': (1366, 768), 'portrait': (390, 844), 'landscape': (844, 390)}
MAP = 'dev_height_proto'

def run(view, shots=True, deep=True):
    w, h = VIEWS[view]
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=view != 'pc', has_touch=view != 'pc')
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        pg.goto('http://localhost:%s/index.html?dev=1' % PORT); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
        ev = pg.evaluate
        ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=15;enterMossForest()"); pg.wait_for_timeout(2500)
        def tp(fx, fy, lv):
            ev("MossForest.enter({map:'%s',x:%d,y:%d,level:%d})" % (MAP, fx - 17, fy - 42, lv)); pg.wait_for_timeout(1300)
            ev("document.querySelector('#msg')&&(document.querySelector('#msg').style.display='none')")
        def st(): return ev("({x:MossForest.feet.x,y:MossForest.feet.y,l:MossForest.level,z:+document.querySelector('#forestPlayer').style.zIndex,under:!!(MossForest.height&&MossForest.height.under)})")
        def hold(key, ms):
            pg.keyboard.down(key); pg.wait_for_timeout(ms); pg.keyboard.up(key); pg.wait_for_timeout(120)
        def shot(name):
            if shots: pg.screenshot(path='%s/%s_%s.png' % (OUT, view, name))
        def tap_to(fx, fy, ms=14000):
            ok = ev("MossForest.goFeet(%d,%d)" % (fx, fy))
            for _ in range(ms // 250):
                pg.wait_for_timeout(250)
                if ev("FieldNavigation.status.outcome") != 'moving': break
            return ok
        ev("MossForest.enter({map:'%s'})" % MAP); pg.wait_for_timeout(2500)
        ev("document.querySelector('#msg')&&(document.querySelector('#msg').style.display='none')")
        check(ev("MossForest.map.id") == MAP and ev("!!MossForest.height"), '[%s] dev_height_proto loads with a height spec' % view)
        s = st(); check(s['l'] == 0 and abs(s['x'] - 300) < 3 and abs(s['y'] - 1250) < 3, '[%s] spawns at level 0 on the low ground' % view)
        shot('01_start')
        if not deep: return b.close()
        # ---- (1) tap-to-move: low ground -> bridge deck (a different level at a far point), arrives at the right level
        ok = tap_to(1560, 600); s = st()
        check(ok and s['l'] == 1 and abs(s['x'] - 1560) < 6 and abs(s['y'] - 600) < 6, '[%s] tap on the bridge deck -> routed over the ramp, arrives at level 1 (%s)' % (view, s))
        zinfo = ev("(()=>{const q=n=>+document.querySelector('[data-piece=\"'+n+'\"]').style.zIndex;return {floor:q('deck_floor'),canopy:q('tree_canopy'),railFront:q('rail_w_640')}})()")
        s = st(); check(s['z'] > zinfo['floor'], '[%s] on the deck the player is drawn above the deck floor (z %d > %d)' % (view, s['z'], zinfo['floor']))
        check(ev("document.querySelector('[data-piece=\"deck_floor\"]').style.opacity") in ('', '1'), '[%s] deck is not faded while nobody is under it' % view)
        shot('02_on_deck')
        # ---- (2) deck edges: no falling off sideways
        tp(1560, 800, 1)
        hold('ArrowRight', 1800); s = st(); check(s['l'] == 1 and 1500 <= s['x'] <= 1620, '[%s] pushing sideways on the deck stays on the deck (x=%d, level %d)' % (view, s['x'], s['l']))
        hold('ArrowLeft', 2400); s = st(); check(s['l'] == 1 and 1500 <= s['x'] <= 1620, '[%s] the other side too (x=%d)' % (view, s['x']))
        # ---- (3) same XY, two levels: under the deck and on it
        tp(1560, 900, 0); a = st()
        check(a['l'] == 0 and a['under'] and a['z'] < zinfo['floor'], '[%s] under the bridge at level 0: drawn below the deck floor (z %d < %d)' % (view, a['z'], zinfo['floor']))
        check(float(ev("document.querySelector('[data-piece=\"deck_floor\"]').style.opacity")) < .6, '[%s] the deck fades while the player is under it' % view)
        shot('03_under_bridge')
        tp(1560, 900, 1); b1 = st()
        check(b1['l'] == 1 and not b1['under'] and (a['x'], a['y']) == (b1['x'], b1['y']), '[%s] same XY (%d,%d) restored at level 1 is the deck, not the underpass' % (view, b1['x'], b1['y']))
        shot('03b_on_deck_same_xy')
        # ---- (4) piers under the deck block level 0 only
        tp(1560, 955, 0); hold('ArrowRight', 1200); s = st()
        check(s['l'] == 0 and s['x'] < 1590 and ev("MossForest.height.blockedAtLevel(1600-17,955-42,0)") and not ev("MossForest.height.blockedAtLevel(1600-17,955-42,1)"), '[%s] the east pier stops a level-0 walker (x=%d) and does not block level 1 at the same XY' % (view, s['x']))
        # ---- (5) keyboard up the south ramp, then onto the deck
        tp(1560, 1290, 0); hold('ArrowUp', 1800); s = st()
        check(s['l'] == 1 and s['y'] < 1120, '[%s] walking up the south ramp ends on the deck at level 1 (y=%d)' % (view, s['y']))
        hold('ArrowDown', 2600); s = st()
        check(s['l'] == 0 and s['y'] > 1130, '[%s] and walking back down returns to level 0 (y=%d)' % (view, s['y']))
        # ---- (6) cliff: cannot enter the plateau from the front / cannot fall off it
        tp(1800, 520, 0); hold('ArrowUp', 1500); s = st()
        check(s['l'] == 0 and s['y'] >= 429, '[%s] the cliff front is a wall at level 0 (y=%d)' % (view, s['y']))
        tp(1800, 380, 1); hold('ArrowDown', 1500); s = st()
        check(s['l'] == 1 and s['y'] <= 421, '[%s] the plateau front edge does not let you fall (y=%d)' % (view, s['y']))
        tp(2230, 250, 1); hold('ArrowRight', 1200); s = st(); check(s['l'] == 1 and s['x'] <= 2251, '[%s] the plateau east edge too (x=%d)' % (view, s['x']))
        shot('04_plateau_edge')
        # ---- (7) stairs and slope
        tp(1960, 580, 0); hold('ArrowUp', 1700); s = st()
        check(s['l'] == 1 and s['y'] < 430, '[%s] stairs: level 1 once the top is reached (y=%d)' % (view, s['y']))
        tp(1960, 580, 0); hold('ArrowUp', 300); mid = ev("MossForest.height.lift(MossForest.feet.x-17,MossForest.feet.y-42,MossForest.level)")
        check(0 < mid < 56, '[%s] mid-stairs the sprite is lifted partway (%.1f px of 56)' % (view, mid)); shot('05_mid_stairs')
        tp(1560, 270, 0); hold('ArrowRight', 1600); s = st()
        check(s['l'] == 1 and s['x'] > 1760, '[%s] slope: walking east up the slope reaches the plateau at level 1 (x=%d)' % (view, s['x']))
        # ---- (8) tap-to-move across levels (plateau and back)
        tp(300, 1250, 0); ok = tap_to(2000, 250); s = st()
        check(ok and s['l'] == 1 and abs(s['x'] - 2000) < 6 and abs(s['y'] - 250) < 6, '[%s] tap on the plateau from the low ground -> via stairs/slope, level 1 (%s)' % (view, s))
        check(ev("FieldNavigation.status.outcome") == 'arrived', '[%s] navigation reports arrived' % view)
        # foreground tree vs plateau actor
        tp(2100, 395, 1); s = st()
        check(s['z'] < zinfo['canopy'], '[%s] a plateau actor near the front edge is drawn behind the foreground tree canopy (z %d < %d)' % (view, s['z'], zinfo['canopy']))
        shot('06_behind_tree')
        ok = tap_to(300, 1250, 16000); s = st()
        check(ok and s['l'] == 0 and abs(s['x'] - 300) < 6 and abs(s['y'] - 1250) < 6, '[%s] and back down to the start at level 0 (%s)' % (view, s))
        # tap on an unreachable point (inside the river) / cliff top seen from the low ground
        check(ev("MossForest.goFeet(1000,660)") is False, '[%s] tapping the river is refused' % view)
        # ---- (9) no-clip random walks at every level
        res = ev("""(()=>{const h=MossForest.height,rnd=(()=>{let s=12345;return()=>(s=(s*1664525+1013904223)>>>0)/4294967296;})();let bad=0,steps=0,leaks=0;
          const starts=[[300,1250,0],[1560,800,1],[2000,250,1],[1450,900,0],[2100,600,0],[1560,300,0]];
          for(const [fx,fy,l0] of starts){h.setLevel(l0);let x=fx-17,y=fy-42;
            for(let i=0;i<4000;i++){const a=rnd()*6.2832,d=6+rnd()*16;const r=FieldMovement.advance(x,y,Math.cos(a)*d,Math.sin(a)*d,h.blocked,{bounds:{width:2400,height:1600}});x=r.x;y=r.y;h.commit(x,y);steps++;
              if(h.blockedAtLevel(x,y,h.level))bad++;
              const px=x+17,py=y+42;if(h.level===0&&px>1770&&px<2230&&py>80&&py<410)leaks++;if(h.level===1&&!(px>=1489&&px<=1631&&py>=349&&py<=1251||px>=1619&&px<=2261&&py>=105&&py<=431||px>=1889&&px<=2031&&py>=409&&py<=551))leaks++;}}
          return {bad,steps,leaks};})()""")
        check(res['bad'] == 0 and res['leaks'] == 0, '[%s] %d random-walk steps over 6 starts: 0 blocked positions, 0 level leaks (%s)' % (view, res['steps'], res))
        # ---- (10) save round trip (prototype state only)
        tp(1560, 900, 1); s1 = ev("MossForest.heightState()"); tp(300, 1250, 0)
        ev("MossForest.enter({map:'%s',x:%d,y:%d,level:%d})" % (s1['map'], s1['x'], s1['y'], s1['level'])); pg.wait_for_timeout(1300)
        s2 = ev("MossForest.heightState()"); check(s1 == s2 and s2['level'] == 1, '[%s] position+level round-trips: %s' % (view, json.dumps(s2)))
        # position without a level falls back to derive(): ambiguous XY gives the top level, never a blocked state
        check(ev("MossForest.height.derive(1560-17,900-42)") == 1 and ev("MossForest.height.derive(300-17,1250-42)") == 0, '[%s] derive() fallback: deck XY -> 1, low ground -> 0 (ambiguous XY needs the saved level)' % view)
        # ---- (11) plain 2D maps are untouched
        ev("MossForest.enter({map:'moss_forest_01_sunlit_path'})"); pg.wait_for_timeout(2200)
        check(ev("MossForest.height") is None and ev("MossForest.level") == 0 and ev("document.querySelector('#forestPlayer').style.transform") == '', '[%s] a normal map has no height state and no sprite lift' % view)
        b.close()

for v in (os.environ.get('VIEWS', 'pc,portrait,landscape')).split(','): run(v)
check(not errs, 'no page errors %s' % errs[:3])
print('FAILS', len(fails), fails)
raise SystemExit(1 if fails else 0)
