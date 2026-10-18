# TalkPortrait: Fiona/Lou conversation portraits, expression switching, fallback, hide, layouts. needs http.server 8765
import json
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
FACES=['normal','smile','angry','sad','surprised','worried','determined','relieved']
TABLE={"npc":"t_por","entries":[
 {"id":"t_p1","priority":10,"when":{},"mode":"cycle","lines":[{"char":"fiona","face":"smile","pages":[
    "フィオナ「こんにちは。」",
    {"speaker":"フィオナ","text":"「ちょっと困ったな。」","face":"worried"},
    {"speaker":"ルー","text":"「わたしにまかせて！」","char":"lou","face":"surprised"},
    {"speaker":"","text":"（沈黙）","face":"sad"},
    {"speaker":"","text":"（ナレーション）","char":None},
    {"speaker":"ルー","text":"「ふふ。」","char":"lou"},
    {"speaker":"ルー","text":"「えっ。」","char":"lou","face":"no_such_face"},
    {"speaker":"ルー","text":"「ID指定。」","char":"lou","face":"06"},
    {"speaker":"？","text":"「不明キャラ。」","char":"nobody","face":"smile"}]}]}]}
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
    st=lambda: pg.evaluate("(()=>{const e=document.getElementById('talkPortrait');if(!e)return null;const cs=getComputedStyle(e);return {char:e.dataset.char||'',face:e.dataset.face||'',vis:cs.display!=='none'&&!e.hidden,src:(e.querySelector('img')||{}).src||''}})()")
    wait=lambda: pg.wait_for_timeout(350)
    # assets: 16 files load, RGBA size
    r=pg.evaluate("""async()=>{const o={};for(const c of ['fiona','lou'])for(const f of TalkPortrait.FACES){const u=TalkPortrait.url(c,f);o[c+'_'+f]=await new Promise(r=>{const i=new Image();i.onload=()=>r([i.naturalWidth,i.naturalHeight]);i.onerror=()=>r(null);i.src=u})}return o}""")
    check(all(v for v in r.values()) and len(r)==16,'16 portrait PNGs load')
    check(len({tuple(v) for k,v in r.items() if k.startswith('fiona')})==1 and len({tuple(v) for k,v in r.items() if k.startswith('lou')})==1,'same canvas size across expressions per character: %s'%{k:v for k,v in r.items() if k.endswith('normal')})
    pg.evaluate("(t)=>FieldTalk.loadTable(t)",TABLE)
    check(st() is None or not st()['vis'],'no portrait before any conversation')
    pg.evaluate("FieldTalk.talk('t_por')"); wait()
    s=st(); check(s['vis'] and s['char']=='fiona' and s['face']=='smile' and s['src'].endswith('img/portraits/fiona/fiona_smile.png'),'conversation default char/face: %s'%s)
    seq=[('fiona','worried'),('lou','surprised'),('lou','sad'),None,('lou','normal'),('lou','normal'),('lou','worried')]
    for i,exp in enumerate(seq):
        pg.click('#msg'); wait(); s=st()
        if exp is None: check(not s['vis'],'page %d char:null hides the portrait'%(i+2))
        else: check(s['vis'] and (s['char'],s['face'])==exp,'page %d -> %s (got %s)'%(i+2,exp,(s['char'],s['face'])))
    pg.click('#msg'); wait(); s=st(); check(not s['vis'],'unknown character id -> no portrait, dialogue continues: %s'%s)
    check('不明キャラ' in pg.evaluate("document.querySelector('#msg').textContent"),'text still shown for unknown char')
    pg.click('#msg'); wait(); check(not st()['vis'] and not pg.evaluate("getComputedStyle(document.querySelector('#msg')).display!=='none'"),'conversation end hides portrait and box')
    # existing plain conversations show no portrait
    pg.evaluate("FieldTalk.talk('elder')"); wait(); check(not st()['vis'],'existing NPC conversation (no char) shows no portrait'); pg.evaluate("closeDialogue()")
    # all 16 via direct API, and missing-image fallback
    for c in ['fiona','lou']:
        for f in FACES:
            pg.evaluate("document.body.classList.add('dialogueOpen');document.getElementById('msg').style.display='block'")
            pg.evaluate("([c,f])=>TalkPortrait.show(c,f)",[c,f]); wait(); s=st()
            check(s['vis'] and s['char']==c and s['face']==f,'show %s/%s'%(c,f))
    pg.route('**/img/portraits/lou/lou_angry.png',lambda r:r.abort()); pg.reload(); pg.wait_for_timeout(2000); pg.evaluate('closeDialogue()')
    pg.evaluate("document.body.classList.add('dialogueOpen');document.getElementById('msg').style.display='block'")
    pg.evaluate("TalkPortrait.show('lou','angry')"); wait(); s=st(); check(s['vis'] and s['face']=='normal','missing expression image falls back to normal: %s'%s)
    pg.route('**/img/portraits/lou/lou_normal.png',lambda r:r.abort()); pg.reload(); pg.wait_for_timeout(2000); pg.evaluate('closeDialogue()')
    pg.evaluate("document.body.classList.add('dialogueOpen');document.getElementById('msg').style.display='block'")
    pg.evaluate("TalkPortrait.show('lou','angry')"); wait(); check(not st()['vis'],'missing normal too -> no portrait, no exception')
    pg.unroute('**/img/portraits/lou/lou_normal.png'); pg.unroute('**/img/portraits/lou/lou_angry.png'); pg.reload(); pg.wait_for_timeout(2000); pg.evaluate('closeDialogue()'); pg.evaluate('(t)=>FieldTalk.loadTable(t)',TABLE)
    # battle mode hides it
    pg.evaluate("TalkPortrait.show('fiona','normal')"); wait(); pg.evaluate("document.body.classList.add('battleMode')"); check(not st()['vis'],'battleMode hides portrait'); pg.evaluate("document.body.classList.remove('battleMode')")
    # layouts: portrait stays inside the viewport, does not overlap #msg, pointer-events none
    for name,(w,h) in {'pc':(1280,720),'tablet':(1024,768),'tablet_portrait':(768,1024),'phone_landscape':(844,390),'phone_portrait':(390,844),'small_phone':(360,640)}.items():
        pg.set_viewport_size({'width':w,'height':h}); pg.evaluate("FieldTalk.talk('t_por')"); wait(); wait()
        g=pg.evaluate("(()=>{const a=document.getElementById('talkPortrait').getBoundingClientRect(),m=document.getElementById('msg').getBoundingClientRect();return {a:[a.left,a.top,a.right,a.bottom,a.width,a.height],m:[m.left,m.top,m.right,m.bottom],pe:getComputedStyle(document.getElementById('talkPortrait')).pointerEvents,iw:innerWidth,ih:innerHeight}})()")
        a,m=g['a'],g['m']
        check(a[0]>=-1 and a[2]<=g['iw']+1 and a[1]>=-1 and a[3]<=g['ih']+1,'%s: inside viewport %s'%(name,[round(x) for x in a]))
        check(a[3]<=m[1]+6,'%s: above the dialogue box (portrait bottom %d <= msg top %d)'%(name,a[3],m[1]))
        check(a[5]>=min(g['ih']*0.2,150) and g['pe']=='none','%s: reasonable size (h=%d) and pointer-events none'%(name,a[5]))
        pg.screenshot(path='/tmp/tp_%s.png'%name); pg.evaluate("closeDialogue()")
    errs=[e for e in errs if 'ERR_FAILED' not in e]   # the aborted requests of the missing-image tests are induced on purpose
    check(not errs,'no page errors / console errors: %s'%errs[:3])
    b.close()
print('FAILS',len(fails)); raise SystemExit(1 if fails else 0)
