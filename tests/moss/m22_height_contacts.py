# Level-aware contacts: on a height map an eventZone only reacts on its own level; maps without a height spec ignore `level` entirely.
import os
from playwright.sync_api import sync_playwright
PORT = os.environ.get('PORT', '8765'); fails = []; errs = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={'width': 844, 'height': 390}).new_page()
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: m.type == 'error' and '404' not in m.text and errs.append(m.text))
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
    # ---- valid shared XY (walkable on level 0 AND level 1): destination level + moving monsters
    ev("MossForest.enter({map:'dev_height_proto'})"); pg.wait_for_timeout(2500)
    ev("document.querySelector('#msg')&&(document.querySelector('#msg').style.display='none')")
    check(ev("!MossForest.height.blockedAtLevel(1543,858,0)&&!MossForest.height.blockedAtLevel(1543,858,1)"), 'fixture: (1560,900) is walkable on both levels')
    d_any = ev("FieldNavigation.destination(1543,858,MossForest.forest.blocked)")
    d_l0 = ev("FieldNavigation.destination(1543,858,MossForest.forest.blocked,0)")
    d_l1 = ev("FieldNavigation.destination(1543,858,MossForest.forest.blocked,1)")
    check(d_l0 and d_l0['level'] == 0 and d_l1 and d_l1['level'] == 1, 'destination honours an explicit target level (%s / %s; free tap -> %s)' % (d_l0 and d_l0['level'], d_l1 and d_l1['level'], d_any and d_any['level']))
    def monster_run(player_lv, mon_lv):
        ev("MossForest.enter({map:'dev_height_proto',x:1543,y:858,level:%d})" % player_lv); pg.wait_for_timeout(2000)
        ev("document.querySelector('#msg')&&(document.querySelector('#msg').style.display='none')")
        ev("FieldMonsters.removeAll()"); ev("FieldMonsters.add({type:'goblin',x:1560,y:900,level:%d})" % mon_lv)
        pg.wait_for_timeout(1800)
        return ev("(()=>{const m=FieldMonsters.list[0];return m?{state:m.state,active:MossForest.active}:null})()")
    r = monster_run(1, 0); check(r and r['state'] not in ('engage', 'engaged', 'alert') and r['active'], 'monster on level 0 ignores a player on level 1 at the same XY (%s)' % r)
    r = monster_run(1, 1); check(r and (r['state'] in ('engage', 'engaged') or not r['active']), 'control: monster on the same level engages (%s)' % r)
    # ---- walkers: pause only for a player on their own level
    def walker_pauses(player_lv, walker_lv):
        ev("MossForest.enter({map:'dev_height_proto',x:1543,y:858,level:%d})" % player_lv); pg.wait_for_timeout(1500)
        return ev("""(()=>{const el=document.createElement('img');const r={id:'w',el,frames:['a','b','c'],w:20,h:40,pts:[[1560,900],[1760,900]],i:1,x:1560,y:900,dir:1,speed:26,anim:false,fps:7,lv:%d,rest:[0,0],wait:0,clock:0,state:'walk'};
          FieldWalkers.list.push(r);FieldWalkers.update(.1);const idle=r.state==='idle';FieldWalkers.list.pop();return idle})()""" % walker_lv)
    check(walker_pauses(1, 1) is True, 'walker pauses for a player on its own level')
    check(walker_pauses(1, 0) is False, 'walker on another level does not pause (same XY)')
    ev("MossForest.enter({map:'dev_height_proto',x:1543,y:858,level:1})"); pg.wait_for_timeout(1500)
    check(ev("MossForest.snapshot().level")==1, 'snapshot carries the level on a height map (additive field)')
    # inert on a plain map
    ev("MossForest.enter({map:'moss_forest_01_sunlit_path'})"); pg.wait_for_timeout(2500)
    ev("document.querySelector('#msg')&&(document.querySelector('#msg').style.display='none')")
    check(ev("!MossForest.height"), 'plain map has no height spec')
    pt = ev("(()=>{const s=MossForest.map.spawns;const q=s.points[s.default];return q})()")
    ev("""(()=>{const q=MossForest.feet;MossForest.map.eventZones.push({id:'z_plain_l1',type:'trigger',shape:{shape:'rect',x:%d,y:%d,w:80,h:80},once:true,level:1});})()""" % (pt['x'] - 40, pt['y'] - 40))
    ev("MossForest.teleportFeet(%d,%d)" % (pt['x'], pt['y'] + 400)); pg.wait_for_timeout(300)
    ev("MossForest.teleportFeet(%d,%d)" % (pt['x'], pt['y'])); pg.wait_for_timeout(600)
    check('z_plain_l1' in fired(), 'plain map: `level` is ignored, zone fires exactly as before')
    check('level' not in ev("MossForest.snapshot()"), 'plain map: snapshot has no level key (saves unchanged)')
    check(not errs, 'no page errors %s' % errs[:2])
    b.close()
print('FAILS', len(fails)); import sys; sys.exit(1 if fails else 0)
