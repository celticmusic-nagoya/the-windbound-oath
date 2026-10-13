# DEV opt-in height-spec overlay (?feature=heightSpecs): off by default (no fetch, no height); on -> data/height-specs/<id>.json is laid over a map that has none.
import os, sys, json
from playwright.sync_api import sync_playwright
PORT=os.environ.get('PORT','8765'); fails=[]; errs=[]
def ck(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
spec={"levelHeight":56,"levels":{"1":{"walk":[[600,300,200,200]]}},"connectors":[],"overpasses":[],"visuals":[]}
with sync_playwright() as p:
    b=p.chromium.launch()
    for flag in (False,True):
        pg=b.new_page(viewport={'width':844,'height':390}); hits=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        def route(r):
            hits.append(r.request.url); r.fulfill(status=200,content_type='application/json',body=json.dumps(spec))
        pg.route('**/data/height-specs/rilde_in_barn.json',route)
        pg.goto('http://localhost:%s/index.html?dev=1%s'%(PORT,'&feature=heightSpecs' if flag else '')); pg.wait_for_timeout(1500); ev=pg.evaluate; ev('closeDialogue()')
        ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=15;enterMossForest()"); pg.wait_for_timeout(2000)
        ev("MossForest.enter({map:'rilde_in_barn'})"); pg.wait_for_timeout(2500)
        has=ev("!!MossForest.height"); tag='[flag %s] '%('on' if flag else 'off')
        ck(has==flag,tag+'height present only with the flag (%s)'%has)
        ck((len(hits)>0)==flag,tag+'spec fetched only with the flag (%d fetches)'%len(hits))
        pg.close()
    b.close()
ck(not errs,'no page errors %s'%errs[:2]); print('FAILS',len(fails)); sys.exit(1 if fails else 0)
