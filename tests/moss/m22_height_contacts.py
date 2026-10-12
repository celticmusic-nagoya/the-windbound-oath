# Level-aware contacts: on a height map an eventZone only reacts on its own level; maps without a height spec ignore `level` entirely.
import os
from playwright.sync_api import sync_playwright
PORT = os.environ.get('PORT', '8765'); fails = []; errs = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={'width': 844, 'height': 390}).new_page()
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:%s/index.html?dev=1' % PORT); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()'); ev = pg.evaluate
    ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=15;enterMossForest()"); pg.wait_for_timeout(2500)
    ev("MossForest.enter({map:'dev_height_proto'})"); pg.wait_for_timeout(2500)
    ev("document.querySelector('#msg')&&(document.querySelector('#msg').style.display='none')")
    check(ev("!!MossForest.height"), 'height map loaded')
    # zones occupy the same XY; one belongs to level 0, one to level 1, one declares levels [0,1]
    ev("""(()=>{const m=MossForest.map;const sh={shape:'rect',x:280,y:1230,w:60,h:40};
      m.eventZones.push({id:'z_l0',type:'trigger',shape:sh,once:true,level:0},{id:'z_l1',type:'trigger',shape:sh,once:true,level:1},{id:'z_both',type:'trigger',shape:sh,once:true,levels:[0,1]},{id:'z_def',type:'trigger',shape:sh,once:true});})()""")
    def fired(): return sorted(ev("MossForest.fired||[]")) if False else sorted(ev("(()=>{const s=MossForest.snapshot();return s.fired})()"))
    # stand inside on level 1 first (wrong level for z_l0 / z_def)
    ev("MossForest.teleportFeet(310,1250);MossForest.height.setLevel(1)"); pg.wait_for_timeout(600)
    f = fired(); print(f)
    check('z_l1' in f and 'z_both' in f, 'level 1 fires the level-1 zone and the [0,1] zone')
    check('z_l0' not in f and 'z_def' not in f, 'level 1 does NOT consume the level-0 / default-level zones')
    ev("MossForest.teleportFeet(100,1250)"); pg.wait_for_timeout(300)
    ev("MossForest.teleportFeet(310,1250);MossForest.height.setLevel(0)"); pg.wait_for_timeout(600)
    f = fired(); print(f)
    check('z_l0' in f and 'z_def' in f, 'back on level 0 the level-0 and default zones fire (not consumed earlier)')
    # inert on a plain map
    ev("MossForest.enter({map:'moss_forest_01_sunlit_path'})"); pg.wait_for_timeout(2500)
    ev("document.querySelector('#msg')&&(document.querySelector('#msg').style.display='none')")
    check(ev("!MossForest.height"), 'plain map has no height spec')
    pt = ev("(()=>{const s=MossForest.map.spawns;const q=s.points[s.default];return q})()")
    ev("""(()=>{const q=MossForest.feet;MossForest.map.eventZones.push({id:'z_plain_l1',type:'trigger',shape:{shape:'rect',x:%d,y:%d,w:80,h:80},once:true,level:1});})()""" % (pt['x'] - 40, pt['y'] - 40))
    ev("MossForest.teleportFeet(%d,%d)" % (pt['x'], pt['y'] + 400)); pg.wait_for_timeout(300)
    ev("MossForest.teleportFeet(%d,%d)" % (pt['x'], pt['y'])); pg.wait_for_timeout(600)
    check('z_plain_l1' in fired(), 'plain map: `level` is ignored, zone fires exactly as before')
    check(not errs, 'no page errors %s' % errs[:2])
    b.close()
print('FAILS', len(fails))
