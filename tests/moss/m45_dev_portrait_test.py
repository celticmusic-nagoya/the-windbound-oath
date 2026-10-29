"""18D: exercise real DEV controls and compare the actual displayed canvas pixels."""
import os, hashlib, base64
from pathlib import Path
from playwright.sync_api import sync_playwright
fails=[]
def check(ok,label,detail=None):
    print(('ok   ' if ok else 'FAIL ')+label, '' if ok else detail, flush=True)
    if not ok:fails.append(label)
URL='http://localhost:%s/index.html?title=0' % os.environ.get('PORT','8765')
PIX="()=>document.querySelector('#talkPortrait canvas').toDataURL()"
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},has_touch=True)
    pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
    pg.goto(URL);pg.wait_for_function("LoadCoordinator.phase==='READY'");pg.evaluate('closeDialogue()')
    saved=pg.evaluate("JSON.stringify({talk:FieldTalk.serialize(),stage:storyStage,storage:{...localStorage}})")
    pg.locator('#devBtn').tap();pg.locator('#devPortraitTest').tap()
    pg.wait_for_function("TalkPortrait.status.visible&&TalkPortrait.status.blinkReady")
    check(pg.evaluate('DevPortraitTest.active'), 'DEV menu opens portrait lab')
    check(pg.locator('#devPortraitChars button:disabled').count()==3, 'Fiona/Lou/Emma show unimplemented and disabled')
    for face in ['normal','smile','angry','worried','sad','surprised']:
        pg.locator('#devPortraitFaces button',has_text=face).tap();pg.wait_for_function("f=>TalkPortrait.status.face===f&&TalkPortrait.status.blinkReady",arg=face)
        frames=[]
        for state in range(5):
            pg.locator('#devPortraitFrames button').nth(state).tap();frames.append(pg.evaluate(PIX))
        check(len(set(frames))==5,face+': all five actual displayed pixel frames differ')
        pg.locator('#devPortraitStop').tap();check(pg.evaluate(PIX)==frames[0],face+': stop restores exact open-eye pixels')
    pg.locator('#devPortraitFaces button',has_text='normal').tap();pg.wait_for_function("TalkPortrait.status.face==='normal'&&TalkPortrait.status.blinkReady")
    pg.evaluate("window.changes=[];new MutationObserver(()=>changes.push(document.querySelector('#talkPortrait canvas').toDataURL())).observe(document.querySelector('#talkPortrait'),{attributes:true,attributeFilter:['data-eye']})")
    pg.locator('#devPortraitBlink').tap();pg.wait_for_function('changes.length>=8&&TalkPortrait.status.blink===null')
    check(len(set(pg.evaluate('changes')))==5, 'manual blink changes real canvas through five distinct frames and stops')
    pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))");pg.wait_for_timeout(100)
    check(pg.evaluate('TalkPortrait.status.blink===null'),'completed manual blink never resumes on visibility event')
    pg.evaluate('changes=[]');pg.locator('#devPortraitAuto').tap();pg.wait_for_function('changes.length>=8',timeout=7500)
    check(len(set(pg.evaluate('changes')))==5,'automatic natural blink changes real canvas pixels')
    pg.evaluate('changes=[]');pg.locator('#devPortraitLoop').tap();pg.wait_for_function('changes.length>=24',timeout=5000)
    check(len(set(pg.evaluate('changes')))==5,'continuous test repeats three actual pixel blink cycles')
    pg.locator('#devPortraitStop').tap();check(pg.evaluate('TalkPortrait.status.eye===0&&TalkPortrait.status.blink===null'),'stop clears timer and opens eyes')
    for w,h in [(390,844),(360,800),(412,915),(844,390),(915,412),(1920,1080)]:
        pg.set_viewport_size({'width':w,'height':h});pg.wait_for_timeout(150)
        for side in ['Right','Left']:
            if pg.locator('#devPortraitStage').evaluate("e=>e.classList.contains('folded')"):pg.locator('#devPortraitToggle').tap()
            pg.locator('#devPortrait'+side).tap();pg.wait_for_timeout(150)
            g=pg.evaluate("""()=>{const a=document.querySelector('#talkPortrait').getBoundingClientRect(),b=document.querySelector('#devPortraitControls').getBoundingClientRect();return {inside:a.top>=0&&a.left>=0&&a.right<=innerWidth+1&&a.bottom<=innerHeight+1,overlap:a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top}}""")
            check(g['inside'] and not g['overlap'],f'{w}x{h} {side}: inside viewport and controls do not cover portrait',g)
        if os.getenv('QA_OUT'):pg.screenshot(path=str(Path(os.environ['QA_OUT'])/f'dev_portrait_{w}x{h}.png'))
    pg.emulate_media(reduced_motion='reduce')
    for name in ['Auto','Loop','Blink']:
        pg.locator('#devPortrait'+name).tap();pg.wait_for_timeout(350)
        check(pg.evaluate('TalkPortrait.status.reduced&&TalkPortrait.status.eye===0&&TalkPortrait.status.blink===null'),name+': reduced-motion prevents animation')
    pg.emulate_media(reduced_motion='no-preference');pg.locator('#devPortraitClose').tap();pg.wait_for_timeout(200)
    check(pg.evaluate('!DevPortraitTest.active&&DevPortraitTest.timers===0&&!TalkPortrait.status.visible&&TalkPortrait.status.blink===null'),'closing DEV releases portrait and all timers')
    check(pg.evaluate("JSON.stringify({talk:FieldTalk.serialize(),stage:storyStage,storage:{...localStorage}})")==saved,'DEV leaves story flags, stage and saved data unchanged')
    # Registry discovery is generic, using approved images for a test-only registered character.
    pg.evaluate("PortraitRegistry.define('fixture',{...PortraitRegistry.get('aidan'),name:'QA fixture'})")
    pg.evaluate('DevPortraitTest.open()');pg.locator('[data-char=fixture]').tap();pg.wait_for_function("TalkPortrait.status.char==='fixture'")
    check(pg.locator('#devPortraitFaces button').count()==6,'future registered character discovered automatically')
    pg.evaluate('FieldTalk.load(FieldTalk.serialize())');pg.wait_for_timeout(200)
    check(pg.evaluate('!DevPortraitTest.active&&DevPortraitTest.timers===0&&!TalkPortrait.status.visible'),'LOAD revokes DEV without stale portrait')
    pg.evaluate('DevPortraitTest.open()');pg.wait_for_function('TalkPortrait.status.visible')
    pg.evaluate("document.body.classList.add('battleMode')");pg.wait_for_timeout(200)
    check(pg.evaluate('!DevPortraitTest.active&&DevPortraitTest.timers===0&&!TalkPortrait.status.visible'),'battle start revokes DEV and timer')
    pg.evaluate("document.body.classList.remove('battleMode');FieldTalk.talk('scene_cliff_sunset')")
    check(not pg.evaluate('DevPortraitTest.open()'),'DEV refuses an active production conversation')
    check(not pg.evaluate("TalkPortrait.devControl('loop')"),'DEV control cannot mutate production conversation owner')
    pg.evaluate('FieldTalk.cancel()')
    pg.route('**/*devMissing=1',lambda r:r.abort())
    pg.evaluate("PortraitRegistry.define('broken',{...PortraitRegistry.get('aidan'),name:'Missing QA',file:f=>'aidan_'+f+'.png?devMissing=1'});DevPortraitTest.open()")
    pg.locator('[data-char=broken]').tap();pg.wait_for_timeout(600)
    check('MISSING' in pg.locator('#devPortraitStatus').inner_text() and 'devMissing=1' in pg.locator('#devPortraitErrors').inner_text(),'missing asset shows path and error instead of perpetual LOADING')
    pg.evaluate('DevPortraitTest.close()');check(not errors,'no page errors',errors)
    ctx.close();b.close()
print('FAILS',len(fails));raise SystemExit(1 if fails else 0)
