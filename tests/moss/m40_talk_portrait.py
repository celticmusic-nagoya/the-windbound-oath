# TalkPortrait (common system, Phase 3): Aidan portraits through FieldTalk, expressions, side precedence, fallbacks, hide, exact compositing, layouts.
# Ported from tests/moss/m30_talk_portrait.py (feature/asset-emma-01 @ f4456a82) and adapted to the registry + canvas renderer. needs http.server 8765.
import os, json, hashlib
from playwright.sync_api import sync_playwright
URL = 'http://localhost:%s/index.html' % os.environ.get('PORT', '8765')
SHOTS = os.environ.get('QA_OUT')
errs = []; fails = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
FACES = ['normal', 'smile', 'angry', 'worried', 'sad', 'surprised']
# test-only second character: the same adopted images under another URL (query) so switching / failures can be observed; side defaults to right
TEST2 = """PortraitRegistry.has('test2')||PortraitRegistry.define('test2',{name:'T2',src:{w:1024,h:1536},base:'assets/images/characters/portraits/aidan/',file:f=>'aidan_'+f+'.png?t2',
  crop:{x:290,y:0,w:700,h:700},faces:['normal','smile','angry','worried','sad','surprised']})"""
TABLE = {"npc": "t_por", "entries": [{"id": "t_p1", "priority": 10, "when": {}, "mode": "cycle", "lines": [{"char": "aidan", "face": "smile", "pages": [
    "エイダン「行こう。」",
    {"speaker": "エイダン", "text": "「……困ったな。」", "face": "worried"},
    {"speaker": "T2", "text": "「交代。」", "char": "test2", "face": "surprised"},
    {"speaker": "", "text": "（沈黙）", "face": "sad"},
    {"speaker": "", "text": "（ナレーション）", "char": None},
    {"speaker": "エイダン", "text": "「左右指定。」", "char": "aidan", "side": "right"},
    {"speaker": "エイダン", "text": "「不明表情。」", "face": "no_such_face"},
    {"speaker": "エイダン", "text": "「ID指定。」", "face": "06"},
    {"speaker": "？", "text": "「不明キャラ。」", "char": "nobody", "face": "smile"}]}]}]}
ST = """(()=>{const e=document.getElementById('talkPortrait');if(!e)return null;const cs=getComputedStyle(e),s=TalkPortrait.status;
  return {char:s.char||'',face:s.face||'',side:s.side||'',vis:cs.display!=='none'&&!e.hidden&&e.getBoundingClientRect().width>0}})()"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1280, 'height': 720})
    pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    pg.goto(URL); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()'); pg.evaluate(TEST2)
    st = lambda: pg.evaluate(ST); wait = lambda: pg.wait_for_timeout(450)
    r = pg.evaluate("""async()=>{const o={};const L=u=>new Promise(r=>{const i=new Image();i.onload=()=>r([i.naturalWidth,i.naturalHeight]);i.onerror=()=>r(null);i.src=u});
      for(const f of PortraitRegistry.get('aidan').faces){o[f]=await L(PortraitRegistry.imageUrl('aidan',f));const b=PortraitRegistry.blinkOf('aidan',f);for(const [e,x] of Object.entries(b.eyes))for(let i=0;i<4;i++)o[f+e+i]=await L(x.urls[i]);}return o}""")
    check(all(r.values()) and len(r) == 54, '6 portraits + 48 blink overlays load (%d)' % len(r))
    check(all(r[f] == [1024, 1536] for f in FACES), 'all six expressions share the 1024x1536 canvas')
    pg.evaluate("(t)=>FieldTalk.loadTable(t)", TABLE)
    check(st() is None or not st()['vis'], 'no portrait before any conversation')
    pg.evaluate("FieldTalk.talk('t_por')"); wait()
    s = st(); check(s['vis'] and (s['char'], s['face'], s['side']) == ('aidan', 'smile', 'left'), 'conversation default char/face, registry side left: %s' % s)
    seq = [('aidan', 'worried', 'left'), ('test2', 'surprised', 'right'), ('test2', 'sad', 'right'), None, ('aidan', 'normal', 'right'), ('aidan', 'normal', 'left'), ('aidan', 'worried', 'left')]
    for i, exp in enumerate(seq):
        pg.click('#msg'); wait(); s = st()
        if exp is None: check(not s['vis'], 'page %d char:null hides the portrait' % (i + 2))
        else: check(s['vis'] and (s['char'], s['face'], s['side']) == exp, 'page %d -> %s (got %s)' % (i + 2, exp, (s['char'], s['face'], s['side'])))
    pg.click('#msg'); wait(); s = st(); check(not s['vis'], 'unknown character id -> no portrait, dialogue continues: %s' % s)
    check('不明キャラ' in pg.evaluate("document.querySelector('#msg').textContent"), 'text still shown for unknown char')
    pg.click('#msg'); wait(); check(not st()['vis'] and not pg.evaluate("getComputedStyle(document.querySelector('#msg')).display!=='none'"), 'conversation end hides portrait and box')
    pg.evaluate("FieldTalk.talk('elder')"); wait(); check(not st()['vis'], 'existing NPC conversation (no char) shows no portrait'); pg.evaluate("closeDialogue()")
    # exact compositing: open eyes = the adopted image crop, pixel for pixel; each blink state differs only inside the overlay boxes
    pg.evaluate("document.body.classList.add('dialogueOpen');document.getElementById('msg').style.display='block'")
    for f in FACES:
        pg.evaluate("(f)=>TalkPortrait.show('aidan',f)", f); wait()
        res = pg.evaluate("""async(f)=>{const R=PortraitRegistry,k=R.get('aidan').crop,cv=document.querySelector('#talkPortrait canvas');
          const im=await new Promise(r=>{const i=new Image();i.onload=()=>r(i);i.src=R.imageUrl('aidan',f)});
          const ref=document.createElement('canvas');ref.width=k.w;ref.height=k.h;const rc=ref.getContext('2d');rc.drawImage(im,k.x,k.y,k.w,k.h,0,0,k.w,k.h);
          const a=cv.getContext('2d').getImageData(0,0,k.w,k.h).data,b=rc.getImageData(0,0,k.w,k.h).data;let d=0;for(let i=0;i<a.length;i++)if(a[i]!==b[i])d++;
          return {w:cv.width,h:cv.height,diff:d,eye:TalkPortrait.status.eye}}""", f)
        check(res['w'] == 700 and res['h'] == 700 and res['diff'] == 0 and res['eye'] == 0, '%s: canvas = 700x700 source-resolution crop, open eyes identical to the adopted image (diff %d)' % (f, res['diff']))
    for f in FACES:
        pg.evaluate("(f)=>TalkPortrait.show('aidan',f)", f); wait()
        res = pg.evaluate("""(f)=>{const R=PortraitRegistry,k=R.get('aidan').crop,W=k.w,H=k.h,boxes=Object.values(R.blinkOf('aidan',f).eyes).map(e=>[e.box[0]-k.x,e.box[1]-k.y,e.box[2]-k.x,e.box[3]-k.y]);
          const px=s=>TalkPortrait.frame(s).getContext('2d').getImageData(0,0,W,H).data,o=px(0),inside=(x,y)=>boxes.some(b=>x>=b[0]&&x<b[2]&&y>=b[1]&&y<b[3]);const r=[];
          for(const s of [1,2,3,4]){const d=px(s);let ins=0,out=0;for(let i=0;i<d.length;i+=4){if(d[i]!==o[i]||d[i+1]!==o[i+1]||d[i+2]!==o[i+2]||d[i+3]!==o[i+3]){const q=i/4;inside(q%W,(q/W)|0)?ins++:out++}}r.push([ins,out])}
          return {r,eye:TalkPortrait.status.eye}}""", f)
        check(all(o == 0 and i > 500 for i, o in res['r']) and res['eye'] == 0, '%s: blink states 1-4 change only pixels inside the eye boxes %s; open again after' % (f, res['r']))
    pg.evaluate("TalkPortrait.show('aidan','normal')"); wait(); pg.evaluate("TalkPortrait.blinkNow()"); pg.wait_for_timeout(110)
    check(pg.evaluate("TalkPortrait.status.eye") in (3, 4), 'a real blink through the renderer is in progress at ~100 ms')
    pg.wait_for_timeout(400); check(pg.evaluate("TalkPortrait.status.eye") == 0, 'eyes open again after the 260 ms blink')
    # missing expression image -> normal; missing normal too -> no portrait, no exception
    pg.route('**/aidan_angry.png?t2', lambda r: r.abort())
    pg.evaluate("TalkPortrait.show('test2','angry')"); wait(); s = st(); check(s['vis'] and s['face'] == 'normal', 'missing expression image falls back to normal: %s' % s)
    pg.route('**/*.png?t3', lambda r: r.abort())   # a fresh character whose every image fails (nothing cached)
    pg.evaluate("PortraitRegistry.define('test3',{name:'T3',src:{w:1024,h:1536},base:'assets/images/characters/portraits/aidan/',file:f=>'aidan_'+f+'.png?t3',crop:{x:290,y:0,w:700,h:700}})")
    pg.evaluate("TalkPortrait.show('test3','sad')"); wait(); check(not st()['vis'], 'missing normal too -> no portrait, no exception')
    pg.unroute('**/aidan_angry.png?t2'); pg.unroute('**/*.png?t3')
    # missing blink overlay -> that face is a still portrait (image shown, no blinking)
    pg.route('**/blink/smile_L_s3.png', lambda r: r.abort()); pg.reload(); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()'); pg.evaluate(TEST2)
    pg.evaluate("document.body.classList.add('dialogueOpen');document.getElementById('msg').style.display='block'")
    pg.evaluate("TalkPortrait.show('aidan','smile')"); wait(); s = pg.evaluate("TalkPortrait.status")
    check(s['visible'] and s['face'] == 'smile' and not s['blinkReady'] and s['blink'] is None, 'missing blink overlay -> smile shown as a still portrait, no timer: %s' % s)
    pg.evaluate("TalkPortrait.show('aidan','normal')"); wait(); s = pg.evaluate("TalkPortrait.status"); check(s['blinkReady'] and s['blink'] and s['blink']['timers'] == 1, 'other faces still blink: %s' % s)
    pg.unroute('**/blink/smile_L_s3.png'); pg.evaluate("TalkPortrait.hide();closeDialogue()")
    pg.evaluate("(t)=>FieldTalk.loadTable(t)", TABLE)
    # battle mode hides it
    pg.evaluate("FieldTalk.talk('t_por')"); wait(); pg.evaluate("document.body.classList.add('battleMode')"); wait(); check(not st()['vis'], 'battleMode hides portrait'); pg.evaluate("document.body.classList.remove('battleMode');closeDialogue()")
    # layouts: inside the viewport, above #msg, pointer-events none; screenshots
    for name, (w, h) in {'pc_1920x1080': (1920, 1080), 'pc_1280x720': (1280, 720), 'tablet_portrait_768x1024': (768, 1024), 'phone_landscape_844x390': (844, 390), 'phone_portrait_390x844': (390, 844), 'phone_portrait_360x800': (360, 800)}.items():
        pg.set_viewport_size({'width': w, 'height': h}); pg.evaluate("FieldTalk.talk('t_por')"); wait(); wait()
        g = pg.evaluate("(()=>{const a=document.getElementById('talkPortrait').getBoundingClientRect(),m=document.getElementById('msg').getBoundingClientRect();return {a:[a.left,a.top,a.right,a.bottom,a.width,a.height],m:[m.left,m.top,m.right,m.bottom],pe:getComputedStyle(document.getElementById('talkPortrait')).pointerEvents,iw:innerWidth,ih:innerHeight}})()")
        a, m = g['a'], g['m']
        check(a[0] >= -1 and a[2] <= g['iw'] + 1 and a[1] >= -1 and a[3] <= g['ih'] + 1, '%s: inside viewport %s' % (name, [round(x) for x in a]))
        check(a[3] <= m[1] + 6, '%s: above the dialogue box (portrait bottom %d <= msg top %d)' % (name, a[3], m[1]))
        check(a[5] >= min(g['ih'] * 0.2, 150) and g['pe'] == 'none', '%s: reasonable size (h=%d) and pointer-events none' % (name, a[5]))
        if SHOTS: pg.screenshot(path=os.path.join(SHOTS, 'talk_portrait_%s.png' % name))
        pg.click('#msg'); wait(); wait()
        if SHOTS: pg.screenshot(path=os.path.join(SHOTS, 'talk_portrait_%s_right.png' % name)) if False else None
        pg.evaluate("closeDialogue()")
    errs[:] = [e for e in errs if 'ERR_FAILED' not in e and 'Failed to load resource' not in e]
    check(not errs, 'no page errors / console errors: %s' % errs[:3])
    b.close()
print('FAILS', len(fails)); raise SystemExit(1 if fails else 0)
