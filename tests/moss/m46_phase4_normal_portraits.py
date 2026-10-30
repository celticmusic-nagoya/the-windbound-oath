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
    def wait_char(pg,c):pg.wait_for_function("c=>TalkPortrait.status.visible&&TalkPortrait.status.char===c&&TalkPortrait.status.blinkReady",arg=c)
    def world_tap(pg,x,y):
        pt=pg.evaluate("([x,y])=>{const r=document.querySelector('#forestWorld').getBoundingClientRect(),s=FieldCamera.scale;return[r.left+x*s,r.top+y*s]}",[x,y]);pg.touchscreen.tap(*pt)
    def natural_pixels(pg,c):
        # Sample the actual production canvas, including both eyes, for THREE unscripted cycles.
        pg.evaluate("""()=>{const e=document.querySelector('#talkPortrait'),cv=e.querySelector('canvas');window.naturalFrames=[{state:0,t:Date.now(),png:cv.toDataURL()}];window.naturalObserver=new MutationObserver(()=>naturalFrames.push({state:+e.dataset.eye,t:Date.now(),png:cv.toDataURL()}));naturalObserver.observe(e,{attributes:true,attributeFilter:['data-eye']})}""")
        pg.wait_for_function("naturalFrames.filter(f=>f.state===0).length>=4",timeout=25000)
        pg.evaluate('naturalObserver.disconnect()')
        frames=pg.evaluate('naturalFrames.map(({state,t})=>({state,t}))')
        ok=pg.evaluate("""async ()=>{
          const frames=window.naturalFrames;
          const c=PortraitRegistry.get(TalkPortrait.status.char),b=PortraitRegistry.blinkOf(c.id,'normal'),k=c.crop;
          const load=u=>new Promise((r,j)=>{const im=new Image();im.onload=()=>r(im);im.onerror=j;im.src=u});
          const base=await load(PortraitRegistry.imageUrl(c.id,'normal')),overlays={};
          for(const [eye,e] of Object.entries(b.eyes)) overlays[eye]=await Promise.all(e.urls.map(load));
          const cv=document.createElement('canvas');cv.width=k.w;cv.height=k.h;const cx=cv.getContext('2d');
          const diffs=[];
          for(const f of frames){cx.clearRect(0,0,k.w,k.h);cx.drawImage(base,k.x,k.y,k.w,k.h,0,0,k.w,k.h);
            if(f.state)for(const [eye,e]of Object.entries(b.eyes))cx.drawImage(overlays[eye][f.state-1],e.box[0]-k.x,e.box[1]-k.y);
            if(cv.toDataURL()!==f.png)return false;
            if(f.state) for(const e of Object.values(b.eyes)){const a=e.box;const pix=cx.getImageData(a[0]-k.x,a[1]-k.y,a[2]-a[0],a[3]-a[1]).data;
              const temp=document.createElement('canvas');temp.width=a[2]-a[0];temp.height=a[3]-a[1];const tx=temp.getContext('2d');tx.drawImage(base,a[0],a[1],temp.width,temp.height,0,0,temp.width,temp.height);const orig=tx.getImageData(0,0,temp.width,temp.height).data;
              if(!pix.some((v,i)=>v!==orig[i]))return false;}
          }return true;
        }""")
        states=[f['state'] for f in frames[1:25]]
        gaps=[frames[i]['t']-frames[i-1]['t'] for i in range(1,len(frames)) if frames[i]['state']==1 and frames[i-1]['state']==0]
        check(ok and states==[1,2,3,4,3,2,1,0]*3 and all(2900<=g<=6200 for g in gaps[1:]),c+': THREE natural 3–6s blinks match actual full canvas/source overlays; BOTH eye pixels change',{'states':states,'gaps':gaps})
        if OUT:
            import base64,json
            (OUT/f'{c}_natural_frames.json').write_text(json.dumps([{'state':f['state'],'t':f['t']} for f in frames]))
            for state in [0,2,4]:
                f=pg.evaluate('state=>naturalFrames.find(f=>f.state===state)',state)
                (OUT/f'{c}_normal_actual_{state}.png').write_bytes(base64.b64decode(f['png'].split(',')[1]))
    def layouts(pg,c,anchor):
        for w,h in [(390,844),(360,800),(412,915),(844,390),(915,412),(1920,1080)]:
            pg.set_viewport_size({'width':w,'height':h});pg.wait_for_timeout(120)
            g=pg.evaluate("""s=>{const e=document.querySelector('#talkPortrait'),r=e.getBoundingClientRect(),m=document.querySelector(s),t=m.getBoundingClientRect(),hit=document.elementFromPoint(t.left+t.width/2,t.top+t.height/2);return {inside:r.left>=-1&&r.top>=-1&&r.right<=innerWidth+1&&r.bottom<=t.top,pointer:getComputedStyle(e).pointerEvents,textVisible:hit===m||m.contains(hit),state:TalkPortrait.status}}""",anchor)
            check(g['inside'] and g['pointer']=='none' and g['textVisible'] and g['state']['blinkReady'] and g['state']['blink'] is not None,f'{c} {w}x{h}: visible normal portrait above actual dialogue, natural blink ready',g)
            if OUT:pg.screenshot(path=str(OUT/f'phase4_{c}_{w}x{h}.png'))
    # Actual Emma NPC interaction on the ordinary peaceful village map, no injected talk data.
    ctx,pg=boot();pg.evaluate("MossForestStory.enterMap('rilde_village','from_aidan')")
    pg.wait_for_function("MossForest.mapId==='rilde_village_01_peace'&&!MossForest.busy&&!LoadingInput.busy")
    pg.evaluate('MossForest.teleportFeet(920,900)');pg.wait_for_timeout(500);world_tap(pg,920,852);wait_char(pg,'emma')
    check(pg.evaluate("FieldTalk.history.at(-1).id==='emma'") and 'おや、エイダンかい' in pg.locator('#msg').inner_text(),'Emma first real NPC dialogue uses adopted normal')
    natural_pixels(pg,'emma');layouts(pg,'emma','#msg');pg.locator('#msg').tap();pg.wait_for_timeout(100)
    check(not pg.evaluate('TalkPortrait.status.visible'),'Emma normal conversation end clears portrait');ctx.close()
    # Actual bench question: Fiona, then narration/choices clears it (no story change on decline).
    ctx,pg=boot();pg.evaluate("storyStage=3;document.querySelector('#hillExit').click()")
    pg.wait_for_function("MossForest.mapId==='cliff_moher_01_spiral_ascent'&&!MossForest.busy&&!LoadingInput.busy")
    pg.evaluate('MossForest.teleportFeet(2400,1040)');pg.wait_for_timeout(1200);world_tap(pg,2400,960)
    pg.wait_for_function('FieldTalk.active');pg.locator('#msg').tap();wait_char(pg,'fiona')
    check('夕日、見ていこうよ' in pg.locator('#msg').inner_text(),'Fiona actual bench question uses adopted normal')
    natural_pixels(pg,'fiona');layouts(pg,'fiona','#msg');pg.locator('#msg').tap();pg.wait_for_timeout(100)
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
    natural_pixels(pg,'lou');layouts(pg,'lou','#aftermathText')
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
    # Registry-driven DEV: provisionally authorized faces and normal blink; excluded Lou faces never requested.
    ctx,pg=boot();requests=[];pg.on('request',lambda r:requests.append(r.url) if '/portraits/' in r.url else None)
    pg.locator('#devBtn').tap();pg.locator('#devPortraitTest').tap();pg.wait_for_function('TalkPortrait.status.visible')
    for c in SHA:
        pg.locator('[data-char='+c+']').tap();wait_char(pg,c)
        check(pg.locator('#devPortraitFaces button').count()==(6 if c=='lou' else 8) and 'QA候補' in pg.locator('#devPortraitStatus').inner_text() and not pg.locator('#devPortraitBlink').is_disabled(),c+': DEV approved normal plus provisional faces, QA label, normal blink enabled')
        for side in ['Left','Right']:
            pg.locator('#devPortrait'+side).tap();wait_char(pg,c)
    pg.locator('#devPortraitClose').tap();pg.wait_for_timeout(100)
    check(not pg.evaluate('TalkPortrait.status.visible') and pg.evaluate('DevPortraitTest.timers===0'),'DEV exit releases all portraits and timers')
    check(not any('/lou/' in u and any(f in u for f in ['lou_smile','lou_relieved']) for u in requests),'excluded Lou expressions never requested',requests)
    check(not errors,'no page errors',errors);ctx.close();b.close()
print('FAILS',len(fails));raise SystemExit(1 if fails else 0)
