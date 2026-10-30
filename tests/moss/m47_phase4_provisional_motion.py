"""20D: immutable revised20C assets; real DEV UI, expression geometry and BOTH eye canvas pixels."""
import os,json,hashlib,base64,io
from pathlib import Path
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=Path(os.environ['QA_OUT']) if os.getenv('QA_OUT') else None
if OUT:OUT.mkdir(parents=True,exist_ok=True)
fails=[]
def check(ok,name,detail=None):
    print(('ok   ' if ok else 'FAIL ')+name,'' if ok else detail,flush=True)
    if not ok:fails.append(name)
ledger=json.loads((ROOT/'docs/portraits/PHASE4_PROVISIONAL_20C.json').read_text());A=ledger['assets']
check(len(A)==43 and sum(a['kind']=='expression' for a in A)==19 and sum(a['kind']=='blink' for a in A)==24,'exact19 expression +24blink ledger')
check(all(a['adoption_status']=='PROVISIONAL_ANDROID_QA' and a['source_commit']=='b8517c2cf74445362ce1a557cf7c4ecd280d94fe' and hashlib.sha256((ROOT/a['file']).read_bytes()).hexdigest()==a['sha256'] for a in A),'all43 revised20C SHA/provisional status/source commit exact')
for c in ['fiona','lou','emma']:
    normal=Image.open(ROOT/f'assets/images/characters/portraits/{c}/{c}_normal.png').convert('RGBA')
    check(all(Image.open(ROOT/a['file']).size==normal.size and ImageChops.difference(Image.open(ROOT/a['file']).getchannel('A'),normal.getchannel('A')).getbbox() is None for a in A if a['character']==c and a['kind']=='expression'),c+': revised expressions share normal dimensions/alpha; no geometric shift')
URL='http://localhost:%s/index.html?title=0'%os.environ.get('PORT','8765')
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},has_touch=True)
    pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
    pg.goto(URL);pg.wait_for_function("LoadCoordinator.phase==='READY'");pg.evaluate('closeDialogue()')
    saved=pg.evaluate('JSON.stringify({talk:FieldTalk.serialize(),stage:storyStage,storage:{...localStorage}})')
    pg.locator('#devBtn').tap();pg.locator('#devPortraitTest').tap()
    def ready(c,face='normal'):
        pg.wait_for_function("([c,f])=>TalkPortrait.status.visible&&TalkPortrait.status.char===c&&TalkPortrait.status.face===f",arg=[c,face]);pg.wait_for_timeout(100)
    def unfold():
        if pg.locator('#devPortraitStage').evaluate("e=>e.classList.contains('folded')"):pg.locator('#devPortraitToggle').tap()
    pix="()=>document.querySelector('#talkPortrait canvas').toDataURL()"
    for c in ['fiona','lou','emma']:
        pg.locator('[data-char='+c+']').tap();ready(c)
        expected=['normal','smile','angry','sad','surprised','worried','determined','relieved'] if c!='lou' else ['normal','angry','sad','surprised','worried','determined']
        check(pg.locator('#devPortraitFaces button').evaluate_all('(bs)=>bs.map(b=>b.dataset.face)')==expected,c+': exact authorized face list; Lou closed-eye faces excluded')
        geometries=[];images=[]
        for f in expected:
            pg.locator('[data-face='+f+']').tap();ready(c,f)
            g=pg.locator('#talkPortrait').bounding_box();geometries.append(g);images.append(pg.evaluate(pix))
            check(('QA候補' in pg.locator('[data-face='+f+']').inner_text())==(f!='normal'),c+' '+f+': provisional expression label, formal normal preserved')
            if f!='normal':check('未実装・静止画' in pg.locator('#devPortraitStatus').inner_text() and pg.locator('#devPortraitBlink').is_disabled() and pg.evaluate('TalkPortrait.status.blink===null'),c+' '+f+': no nonexistent expression blink')
            if OUT:pg.screenshot(path=str(OUT/f'20d_{c}_{f}.png'))
        check(all(g==geometries[0] for g in geometries) and len(set(images))==len(expected),c+': every actual expression differs; exact same screen position/size')
        pg.locator('[data-face=normal]').tap();ready(c);pg.wait_for_function('TalkPortrait.status.blinkReady')
        frames=[]
        for s in range(5):
            pg.locator('#devPortraitFrames button').nth(s).tap();frames.append(pg.evaluate(pix))
        both=True
        crop=pg.evaluate('PortraitRegistry.get(TalkPortrait.status.char).crop');boxes=pg.evaluate("PortraitRegistry.blinkOf(TalkPortrait.status.char,'normal').eyes")
        decoded=[Image.open(io.BytesIO(base64.b64decode(f.split(',')[1]))).convert('RGB') for f in frames]
        for e in boxes.values():
            a=e['box'];r=(a[0]-crop['x'],a[1]-crop['y'],a[2]-crop['x'],a[3]-crop['y'])
            both &= len({im.crop(r).tobytes() for im in decoded})==5
        check(both and len(set(frames))==5,c+': frame0–4 actually change BOTH eye pixels')
        if OUT:
            # Enlarged source-resolution eye strips from the REAL displayed canvas.
            for eye,e in boxes.items():
                a=e['box'];r=(a[0]-crop['x'],a[1]-crop['y'],a[2]-crop['x'],a[3]-crop['y']);w=r[2]-r[0];h=r[3]-r[1]
                strip=Image.new('RGB',(w*5,h))
                for i,im in enumerate(decoded):strip.paste(im.crop(r),(i*w,0))
                strip.resize((w*15,h*3)).save(OUT/f'20d_{c}_{eye}_actual_strip.png')
        pg.evaluate("window.changes=[];window.devObserver?.disconnect();window.devObserver=new MutationObserver(()=>changes.push(document.querySelector('#talkPortrait canvas').toDataURL()));devObserver.observe(document.querySelector('#talkPortrait'),{attributes:true,attributeFilter:['data-eye']})")
        for control,count,timeout in [('Blink',8,2500),('Auto',8,7500),('Loop',24,5000)]:
            pg.evaluate('changes=[]');pg.locator('#devPortrait'+control).tap();pg.wait_for_function('n=>changes.length>=n',arg=count,timeout=timeout)
            check(len(set(pg.evaluate('changes')))==5,c+': '+control+' changes displayed pixels through five frames')
        pg.locator('#devPortraitStop').tap();check(pg.evaluate(pix)==frames[0] and pg.evaluate('TalkPortrait.status.blink===null'),c+': stop opens exact original pixels and clears timer')
        for w,h in [(390,844),(360,800),(412,915),(844,390),(915,412),(1920,1080)]:
            pg.set_viewport_size({'width':w,'height':h});pg.wait_for_timeout(100)
            for side in ['Right','Left']:
                unfold();pg.locator('#devPortrait'+side).tap();ready(c)
                g=pg.evaluate("""()=>{const a=document.querySelector('#talkPortrait').getBoundingClientRect(),z=document.querySelector('#devPortraitControls').getBoundingClientRect();return{inside:a.top>=0&&a.left>=0&&a.right<=innerWidth+1&&a.bottom<=innerHeight+1,overlap:a.left<z.right&&a.right>z.left&&a.top<z.bottom&&a.bottom>z.top}}""")
                check(g['inside'] and not g['overlap'],f'{c} {w}x{h} {side}: viewport/controls clear',g)
            if OUT:pg.screenshot(path=str(OUT/f'20d_{c}_{w}x{h}.png'))
        pg.set_viewport_size({'width':390,'height':844});pg.emulate_media(reduced_motion='reduce')
        for control in ['Blink','Auto','Loop']:
            pg.locator('#devPortrait'+control).tap();pg.wait_for_timeout(330)
            check(pg.evaluate('TalkPortrait.status.eye===0&&TalkPortrait.status.blink===null&&TalkPortrait.status.reduced'),c+': '+control+' respects reduced-motion')
        pg.emulate_media(reduced_motion='no-preference');pg.locator('#devPortraitStop').tap()
    pg.locator('[data-char=aidan]').tap();pg.wait_for_function("TalkPortrait.status.char==='aidan'&&TalkPortrait.status.blinkReady")
    check(pg.locator('#devPortraitFaces button').count()==6 and not pg.locator('#devPortraitBlink').is_disabled() and 'QA候補' not in pg.locator('#devPortraitStatus').inner_text(),'Aidan existing formally adopted six faces/blink unaffected')
    pg.locator('#devPortraitClose').tap();pg.wait_for_timeout(150)
    check(pg.evaluate('!TalkPortrait.status.visible&&TalkPortrait.status.blink===null&&DevPortraitTest.timers===0'),'DEV close clears all timers')
    check(pg.evaluate('JSON.stringify({talk:FieldTalk.serialize(),stage:storyStage,storage:{...localStorage}})')==saved,'DEV leaves story flags/stage/save intact')
    check(not errors,'no page errors',errors);ctx.close();b.close()
print('FAILS',len(fails));raise SystemExit(1 if fails else 0)
