# SCENARIO-PROLOGUE-02 エマの差し入れ: plays once right after the training dummy is beaten (stage 3), verbatim script,
# Emma provisional portrait, no re-fire after SAVE/CONTINUE, no fire when training is interrupted, Emma talk / charm quest intact.
# needs http.server 8765
import sys
from playwright.sync_api import sync_playwright
fails = []; errs = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

def to_training(pg):
    ev = pg.evaluate
    pg.goto('http://localhost:8765/index.html?title=0'); pg.wait_for_timeout(1800)
    ev("localStorage.removeItem(SAVE_KEY)")
    ev("RildeVillage.startOpening()"); pg.wait_for_timeout(2500); ev("closeDialogue()")
    ev("MossForestStory.enterMap('rilde_village','from_aidan')"); pg.wait_for_timeout(1800); ev("closeDialogue()")
    ev("RildeVillage.hook({hook:'rilde_fiona'},MossForest)"); pg.wait_for_timeout(400); ev("closeDialogue()")
    ev("RildeVillage.hook({hook:'rilde_dummy'},MossForest)"); pg.wait_for_timeout(800)
    ev("window.__snackEnds=0;addEventListener('field-talk-end',e=>{if(e.detail&&e.detail.id==='scene_emma_snack')window.__snackEnds++})")

with sync_playwright() as p:
    b = p.chromium.launch()
    for name, vp in (('pc', {'width': 1280, 'height': 720}), ('android_port', {'width': 412, 'height': 915})):
        pg = b.new_page(viewport=vp)
        pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        ev = pg.evaluate
        to_training(pg)
        check(ev('storyStage') == 2, name + ': training battle open (stage 2)')
        quest0 = ev("JSON.stringify(Quest.state('q_emma_charm'))")
        ev("dhp=0;enemyTurn()"); pg.wait_for_timeout(2200)
        check(ev('storyStage') == 3, name + ': victory -> stage 3')
        check(ev('FieldScene.running') == 'emma_snack', name + ': emma_snack scene runs after the win (%s)' % ev('FieldScene.running'))
        pages = []; chars = set()
        for _ in range(40):
            if not ev("FieldTalk.active"): break
            pages.append(ev("(()=>{const m=document.getElementById('msg');const n=m.querySelector('.talkName'),t=m.querySelector('.talkText');return (n?n.textContent+'：':'')+(t?t.textContent:'')})()"))
            st = ev("TalkPortrait.status");
            if st and st.get('visible') and st.get('char'): chars.add((st['char'], st.get('face')))
            pg.click('#msg'); pg.wait_for_timeout(120)
        pg.wait_for_timeout(600)
        exp = open('tests/fixtures/prologue02_emma_snack_script.txt', encoding='utf-8').read().strip().split('\n')
        exp = [l[1:-1] if l.startswith('（') else l for l in exp]
        check(pages == exp, name + ': 27 pages verbatim and in order (%d pages)' % len(pages))
        check(('emma', 'normal') in chars and ('emma', 'smile') in chars, name + ': Emma portrait normal + smile (provisional-20c) shown')
        check(ev('__snackEnds') == 1, name + ': scene conversation ended exactly once')
        check(ev("FieldTalk.flag('emma_snack_done')") is True, name + ': emma_snack_done flag set')
        check('一瞬だけ変な光' in ev("document.getElementById('msg').textContent"), name + ': existing post-training Fiona line follows')
        check(ev('currentObjective') == 'フィオナと風見の断崖へ向かおう', name + ': objective unchanged (cliff)')
        check(ev('storyStage') == 3, name + ': stage still 3 (no stage added)')
        check(ev("JSON.stringify(Quest.state('q_emma_charm'))") == quest0, name + ': Emma charm quest untouched')
        check(ev("Inventory.count('baked_goods')+Inventory.count('canteen')") == 0, name + ': no snack items granted')
        ev("closeDialogue()"); pg.wait_for_timeout(2000)
        a0 = ev("MossForest.actor('aidan').get().x"); pg.keyboard.down('ArrowLeft'); pg.wait_for_timeout(500); pg.keyboard.up('ArrowLeft')
        check(abs(ev("MossForest.actor('aidan').get().x") - a0) > 10, name + ': player control returns after the event')
        check(ev("RildeVillage.afterTraining(()=>{})") is False, name + ': does not fire again in the same session')
        check(bool(ev("FieldTalk.pick('emma')")), name + ': Emma field conversation still available')
        if name == 'pc':
            ev("saveGrowthData()")
            saved = ev("JSON.parse(localStorage.getItem(SAVE_KEY))")
            check(saved['talk']['flags'].get('emma_snack_done') is True and saved['prologue']['storyStage'] == 3, 'pc: SAVE keeps the flag (format unchanged)')
            pg.goto('http://localhost:8765/index.html?title=0'); pg.wait_for_timeout(1800)
            ev("window.__snackEnds=0;addEventListener('field-talk-end',e=>{if(e.detail&&e.detail.id==='scene_emma_snack')window.__snackEnds++})")
            ev("loadGrowthData()"); pg.wait_for_timeout(3500)
            check(ev('storyStage') == 3 and ev("FieldTalk.flag('emma_snack_done')") is True, 'pc: CONTINUE restores stage 3 + flag')
            check(ev('FieldScene.running') is None and ev('__snackEnds') == 0, 'pc: no re-fire after CONTINUE')
            check(ev("RildeVillage.afterTraining(()=>{})") is False, 'pc: guard holds after CONTINUE')
            ev("RildeVillage.hook({hook:'rilde_dummy'},MossForest)"); pg.wait_for_timeout(300)
            check(ev('storyStage') == 3 and ev('FieldScene.running') is None, 'pc: revisiting the dummy does not restart training/event')
        pg.close()
    # interruption: the win timer is cancelled (load / reset during training) -> no scene, no flag
    pg = b.new_page(viewport={'width': 1280, 'height': 720}); ev = pg.evaluate
    pg.on('pageerror', lambda e: errs.append('PAGEERR3 ' + str(e)))
    to_training(pg)
    ev("dhp=0;enemyTurn();TrainingCheckpoint.cancel()"); pg.wait_for_timeout(2500)
    check(ev('FieldScene.running') is None and ev('__snackEnds') == 0 and ev("FieldTalk.flag('emma_snack_done')") is False, 'interrupted training: no event, no flag')
    check(ev('storyStage') == 2, 'interrupted training: stage not advanced')
    # legacy village host: no scene, existing line only
    pg2 = b.new_page(); pg2.on('pageerror', lambda e: errs.append('PAGEERR4 ' + str(e)))
    pg2.goto('http://localhost:8765/index.html?legacyVillage=1'); pg2.wait_for_timeout(1200)
    check(pg2.evaluate("RildeVillage.afterTraining(()=>{})") is False, 'legacy village: scene skipped (caller runs the existing line)')
errs = [e for e in errs if 'favicon' not in e]
check(not errs, 'no console errors %s' % errs[:3])
print('FAILS', fails); sys.exit(1 if fails else 0)
