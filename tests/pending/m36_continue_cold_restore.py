# SAVE-LOAD-CONTINUE (#21) — PENDING (RED by design until the restore path is implemented). Not part of run_all.sh.
# Desired behaviour: a save made inside the new Rilde village (stage 0..8) restores, after a cold page load, into the SAME new-village map at the saved position
# (today it falls into the legacy DOM village: MossForest inactive, map None). needs http.server 8765.
import sys
from playwright.sync_api import sync_playwright
fails = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
CASES = [('village0', "RildeVillage.enter('from_aidan')", 0, 'rilde_village_01_peace'),
         ('training', "storyStage=1;RildeVillage.enter('from_training')", 1, 'rilde_village_01_peace'),
         ('sunset', "storyStage=3;RildeVillage.enter('from_sunset')", 3, 'rilde_village_01_peace'),
         ('opening-house', None, 0, 'rilde_in_aidan')]
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, setup, stage, mapid in CASES:
        pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(3500); pg.evaluate('closeDialogue()')
        if setup: pg.evaluate(setup); pg.wait_for_function("MossForest.active&&!MossForest.busy", timeout=20000); pg.wait_for_timeout(800)
        pg.evaluate('closeDialogue()'); pg.click('#menuOpen'); pg.click('[data-stab=save]'); pg.click('#doSave'); pg.wait_for_timeout(400)
        want = pg.evaluate("(()=>{const f=MossForest.feet;return {map:MossForest.mapId,x:Math.round(f.x),y:Math.round(f.y),stage:storyStage}})()")
        raw = pg.evaluate("localStorage.getItem(SAVE_KEY)")
        check(want['map'] == mapid and want['stage'] == stage, '%s: save made in %s (stage %d) %s' % (name, mapid, stage, want))
        pg.reload(); pg.wait_for_timeout(400)
        pg.evaluate("loadGrowthData()")
        try: pg.wait_for_function("MossForest.active&&!MossForest.busy", timeout=15000)
        except Exception: pass
        got = pg.evaluate("(()=>{const f=MossForest.feet;return {map:MossForest.mapId,x:f?Math.round(f.x):null,y:f?Math.round(f.y):null,stage:storyStage,legacyHome:document.getElementById('inside').style.display==='block'}})()")
        check(got['map'] == want['map'] and got['stage'] == stage, '%s: cold-start load returns to the same map and stage %s' % (name, got))
        check(got['x'] is not None and abs(got['x'] - want['x']) <= 2 and abs(got['y'] - want['y']) <= 2, '%s: same player position (+-2) %s vs %s' % (name, got, want))
        check(not got['legacyHome'], '%s: legacy DOM house is not shown' % name)
        check(pg.evaluate("localStorage.getItem(SAVE_KEY)") == raw, '%s: loading leaves the save data byte-identical' % name)
        check(not errs, '%s: no page errors %s' % (name, errs[:2])); pg.close()
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)
