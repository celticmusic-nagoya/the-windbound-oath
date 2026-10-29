"""19B: approved normal-only assets through production NPC, bench and Raider aftermath routes."""
import os, hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=Path(os.environ['QA_OUT']) if os.getenv('QA_OUT') else None
if OUT:OUT.mkdir(parents=True,exist_ok=True)
fails=[]
def check(ok,name,d=None):
    print(('ok   ' if ok else 'FAIL ')+name,'' if ok else d,flush=True)
    if not ok:fails.append(name)
SHA={'fiona':'89efd67352ac7f03882242d2363a2a2c8762bc0489e447a7d6089745a227094a','lou':'c2cc6d70614b18c685ef773e27bf4f50a7ed2947cb6e6b9367a5ba9e32e59e8f','emma':'f4dfd09d08e3bd333743f677afbe84e4e1771b295863e92a96a3b4c0904114b2'}
for c,h in SHA.items():
    folder=ROOT/'assets/images/characters/portraits'/c
    check(sorted(f.name for f in folder.glob('*.png'))==[c+'_normal.png'] and hashlib.sha256((folder/(c+'_normal.png')).read_bytes()).hexdigest()==h,c+': only approved normal, exact adopted SHA')
with sync_playwright() as p:
    b=p.chromium.launch();errors=[]
    def boot():
        ctx=b.new_context(viewport={'width':390,'height':844},has_touch=True)
        pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)))
        pg.goto('http://localhost:%s/index.html?title=0'%os.environ.get('PORT','8765'));pg.wait_for_function("LoadCoordinator.phase==='READY'");pg.wait_for_timeout(300);pg.evaluate('closeDialogue()');return ctx,pg
    def wait_char(pg,c):pg.wait_for_function("c=>TalkPortrait.status.visible&&TalkPortrait.status.char===c",arg=c)
    def world_tap(pg,x,y):
        pt=pg.evaluate("([x,y])=>{const r=document.querySelector('#forestWorld').getBoundingClientRect(),s=FieldCamera.scale;return[r.left+x*s,r.top+y*s]}",[x,y]);pg.touchscreen.tap(*pt)
    def layouts(pg,c,anchor):
        for w,h in [(390,844),(360,800),(412,915),(844,390),(915,412),(1920,1080)]:
            pg.set_viewport_size({'width':w,'height':h});pg.wait_for_timeout(120)
            g=pg.evaluate("""s=>{const e=document.querySelector('#talkPortrait'),r=e.getBoundingClientRect(),m=document.querySelector(s),t=m.getBoundingClientRect(),hit=document.elementFromPoint(t.left+t.width/2,t.top+t.height/2);return {inside:r.left>=-1&&r.top>=-1&&r.right<=innerWidth+1&&r.bottom<=t.top,pointer:getComputedStyle(e).pointerEvents,textVisible:hit===m||m.contains(hit),state:TalkPortrait.status}}""",anchor)
            check(g['inside'] and g['pointer']=='none' and g['textVisible'] and g['state']['blink'] is None and not g['state']['blinkReady'],f'{c} {w}x{h}: visible still portrait above actual dialogue, no timer',g)
            if OUT:pg.screenshot(path=str(OUT/f'phase4_{c}_{w}x{h}.png'))
    # Actual Emma NPC interaction on the ordinary peaceful village map, no injected talk data.
    ctx,pg=boot();pg.evaluate("MossForestStory.enterMap('rilde_village','from_aidan')")
    pg.wait_for_function("MossForest.mapId==='rilde_village_01_peace'&&!MossForest.busy&&!LoadingInput.busy")
    pg.evaluate('MossForest.teleportFeet(920,900)');pg.wait_for_timeout(500);world_tap(pg,920,852);wait_char(pg,'emma')
    check(pg.evaluate("FieldTalk.history.at(-1).id==='emma'") and 'おや、エイダンかい' in pg.locator('#msg').inner_text(),'Emma first real NPC dialogue uses adopted normal')
    layouts(pg,'emma','#msg');pg.locator('#msg').tap();pg.wait_for_timeout(100)
    check(not pg.evaluate('TalkPortrait.status.visible'),'Emma normal conversation end clears portrait');ctx.close()
    # Actual bench question: Fiona, then narration/choices clears it (no story change on decline).
    ctx,pg=boot();pg.evaluate("storyStage=3;document.querySelector('#hillExit').click()")
    pg.wait_for_function("MossForest.mapId==='cliff_moher_01_spiral_ascent'&&!MossForest.busy&&!LoadingInput.busy")
    pg.evaluate('MossForest.teleportFeet(2400,1040)');pg.wait_for_timeout(1200);world_tap(pg,2400,960)
    pg.wait_for_function('FieldTalk.active');pg.locator('#msg').tap();wait_char(pg,'fiona')
    check('夕日、見ていこうよ' in pg.locator('#msg').inner_text(),'Fiona actual bench question uses adopted normal')
    layouts(pg,'fiona','#msg');pg.locator('#msg').tap();pg.wait_for_timeout(100)
    check(not pg.evaluate('TalkPortrait.status.visible'),'Fiona narration/choice page hides portrait')
    pg.locator('.talkChoices button').nth(1).tap()
    while pg.evaluate('FieldTalk.active'):pg.locator('#msg').tap()
    check(pg.evaluate("storyStage===3&&!FieldTalk.flag('cliff_bench_sat')"),'decline preserves existing story flag/stage');ctx.close()
    # Real Raider victory -> existing aftermath scene. DEV is used only to reach the battle quickly.
    ctx,pg=boot();pg.evaluate("devJump('raider')")
    pg.wait_for_function("document.querySelector('#raiderBattle').style.display==='block'&&!rbBusy&&!battleCommandLocked('raider')",timeout=30000)
    pg.evaluate("PrologueCombat.instantKill('raider')");pg.wait_for_function("getComputedStyle(document.querySelector('#battleResult')).display!=='none'",timeout=30000)
    pg.locator('#resultContinue').tap();pg.wait_for_function("document.querySelector('#aftermathScene').style.display==='block'")
    lines=pg.evaluate('aftermathLines');lou_pages={6,8,9,10,12,14,15,18,21}
    for i in range(6):pg.locator('#aftermathScene').tap()
    wait_char(pg,'lou');check(pg.locator('#aftermathText').inner_text()==lines[6],'Lou portrait reached through actual battle result and original aftermath line')
    check(not pg.evaluate('DevPortraitTest.open()'),'DEV cannot steal scene-owned story portrait')
    layouts(pg,'lou','#aftermathText')
    for i in range(6,len(lines)):
        if i in lou_pages:wait_char(pg,'lou')
        else:pg.wait_for_timeout(30);check(not pg.evaluate('TalkPortrait.status.visible'),'aftermath non-Lou page hides portrait '+str(i))
        check(pg.locator('#aftermathText').inner_text()==lines[i] and pg.evaluate("document.querySelectorAll('.event-cg-item.on').length===0"),'aftermath text/order and no CG '+str(i))
        pg.locator('#aftermathScene').tap()
    pg.wait_for_timeout(800)
    check(pg.evaluate('storyStage===14&&PartyManager.support.joined') and not pg.evaluate('TalkPortrait.status.visible'),'original aftermath end joins Lou/stage14 and clears portrait')
    # Cancel, LOAD, explicit scene hide and event CG takeover invalidate both ready and pending scene portraits.
    for action in ["FieldTalk.cancel()","FieldTalk.load(FieldTalk.serialize())","document.querySelector('#aftermathScene').style.display='none'","devResetScreens();startLouIntro()"]:
        pg.evaluate("devResetScreens();closeDialogue();startRaiderAftermath();aftermathIndex=6;showAftermathPage()")
        wait_char(pg,'lou');pg.evaluate(action);pg.wait_for_timeout(250)
        check(not pg.evaluate('TalkPortrait.status.visible') and pg.evaluate('TalkPortrait.status.blink') is None,'Lou lifecycle '+action)
    ctx.close()
    # Registry-driven DEV: one face, explicit still label, no unapproved asset or blink requests.
    ctx,pg=boot();requests=[];pg.on('request',lambda r:requests.append(r.url) if '/portraits/' in r.url else None)
    pg.locator('#devBtn').tap();pg.locator('#devPortraitTest').tap();pg.wait_for_function('TalkPortrait.status.visible')
    for c in SHA:
        pg.locator('[data-char='+c+']').tap();wait_char(pg,c)
        check(pg.locator('#devPortraitFaces button').all_inner_texts()==['normal'] and '未実装・静止画' in pg.locator('#devPortraitStatus').inner_text() and pg.locator('#devPortraitBlink').is_disabled(),c+': DEV normal only, still label, motion disabled')
        for side in ['Left','Right']:
            pg.locator('#devPortrait'+side).tap();wait_char(pg,c)
    pg.locator('#devPortraitClose').tap();pg.wait_for_timeout(100)
    check(not pg.evaluate('TalkPortrait.status.visible') and pg.evaluate('DevPortraitTest.timers===0'),'DEV exit releases all portraits and timers')
    check(all('/'+c+'/' not in u or u.split('?')[0].endswith(c+'_normal.png') for u in requests for c in SHA),'no unapproved expressions or nonexistent blink assets requested',requests)
    check(not errors,'no page errors',errors);ctx.close();b.close()
print('FAILS',len(fails));raise SystemExit(1 if fails else 0)
