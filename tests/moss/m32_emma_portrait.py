# ASSET-EMMA-01: Emma's conversation portrait (normal only; expression01..04 are NOT registered yet -> fallback). needs a static server on $PORT (default 8765).
# Uses Emma's REAL conversation data (talk-data.js / talk-data-quests.js). EMMA-002/003/004 (expression display / no jump / return) are NOT_RUN for the expression images: they do not exist yet.
import os, sys, json, hashlib
from playwright.sync_api import sync_playwright
PORT = os.environ.get('PORT', '8765'); URL = 'http://localhost:%s/index.html' % PORT
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
errs = []; fails = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
STATE = """(()=>{const e=document.getElementById('talkPortrait'),c=window.TalkPortrait.current;const i=e&&e.querySelector('img');
  const m=document.getElementById('msg').getBoundingClientRect(),r=e?e.getBoundingClientRect():null;
  return {vis:!!e&&!e.hidden&&getComputedStyle(e).display!=='none'&&r.width>0&&!!i,cur:c?c.char+'/'+c.face:null,src:i?i.currentSrc.split('/').pop():null,nw:i?i.naturalWidth:0,nh:i?i.naturalHeight:0,
  box:r?[r.left,r.top,r.right,r.bottom]:null,msgTop:m.top,W:innerWidth,H:innerHeight,txt:document.querySelector('#msg .talkText')?document.querySelector('#msg .talkText').textContent:''}})()"""
def boot(b, w=1280, h=720, touch=False, route=None):
    ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=touch); pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    if route: pg.route('**/img/portraits/emma/**', route)
    pg.goto(URL); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()'); return ctx, pg
st = lambda pg: pg.evaluate(STATE)
def wait_cur(pg, cur, ms=5000):
    for _ in range(ms // 100):
        s = st(pg)
        if s['vis'] and s['cur'] == cur: return s
        pg.wait_for_timeout(100)
    return st(pg)
def talk_n(pg, n):   # the n-th (1-based) emma conversation of the cycle
    for i in range(n):
        pg.evaluate("closeDialogue()"); pg.evaluate("FieldTalk.talk('emma')"); pg.wait_for_timeout(150)
with sync_playwright() as p:
    b = p.chromium.launch()
    # ---- registry / ids (EMMA-006 + id rules) ----
    ctx, pg = boot(b)
    r = pg.evaluate("""()=>({chars:TalkPortrait.chars(),faces:TalkPortrait.FACES,f1:TalkPortrait.faceOf('smile'),f2:TalkPortrait.faceOf('relieved','lou'),f3:TalkPortrait.faceOf('07','fiona'),
       e1:TalkPortrait.faceOf('expression01','emma'),e4:TalkPortrait.faceOf('expression04','emma'),e5:TalkPortrait.faceOf('expression05','emma'),eS:TalkPortrait.faceOf('smile','emma'),eD:TalkPortrait.faceOf('03','emma'),eN:TalkPortrait.faceOf('normal','emma'),eU:TalkPortrait.faceOf(undefined,'emma')})""")
    check(r['faces'] == ['normal','smile','angry','sad','surprised','worried','determined','relieved'], 'EMMA-006 Fiona/Lou 8-expression set unchanged')
    check(r['chars'] == ['fiona','lou','emma'] and r['f1'] == 'smile' and r['f2'] == 'relieved' and r['f3'] == 'determined', 'EMMA-006 Fiona/Lou face resolution unchanged %s' % r)
    check(r['e5'] == 'normal' and r['eS'] == 'normal' and r['eD'] == 'normal' and r['eN'] == 'normal' and r['eU'] == 'normal', 'EMMA-002 invalid / foreign ids fall back to normal for Emma %s' % r)
    check(r['e1'] == 'normal' and r['e4'] == 'normal', 'EMMA-002 expression01..04 have no image yet -> normal (NOT registered; expression display = NOT_RUN)')
    # ---- EMMA-001 normal portrait on the real conversation ----
    reqs = []; pg.on('request', lambda q: reqs.append(q.url))
    pg.evaluate("FieldTalk.talk('emma')"); s = wait_cur(pg, 'emma/normal')
    check(s['vis'] and s['cur'] == 'emma/normal' and s['src'] == 'emma_normal.png', 'EMMA-001 Emma conversation shows emma_normal %s' % {k: s[k] for k in ('vis','cur','src')})
    check(s['nw'] == 1024 and s['nh'] == 1536, 'EMMA-001 full 1024x1536 image decoded (aspect kept by the crop frame)')
    check(not [u for u in reqs if 'emma_expression' in u], 'EMMA-002 no request for a non-existent expression image')
    ctx.close()
    # ---- EMMA-005 conversation progress, ALL real Emma lines (cloned unchanged into scratch tables): the portrait follows the speaker plate page by page ----
    ctx, pg = boot(b)
    n = pg.evaluate("""()=>{const L=[];for(const src of [TalkData,window.TalkDataQuests])for(const t of src.tables)if(t.npc==='emma')for(const e of t.entries)for(const l of e.lines)if(!(typeof l==='object'&&l.choice))L.push(l);window.__EL=L;return L.length}""")
    check(n >= 8, 'EMMA-005 collected %d real Emma lines (without choices)' % n)
    bad = []; pages_seen = 0
    for k in range(n):
        pg.evaluate("closeDialogue()"); pg.evaluate("(k)=>{FieldTalk.loadTable({npc:'emma_real'+k,entries:[{id:'emma_real_e'+k,priority:5,when:{},mode:'cycle',lines:[window.__EL[k]]}]});FieldTalk.talk('emma_real'+k)}", k)
        pg.wait_for_timeout(450)
        for i in range(10):
            d = pg.evaluate("(()=>{const t=document.querySelector('#msg .talkText');const nm=document.querySelector('#msg .talkName');return t?[nm?nm.textContent:'',t.textContent]:null})()")
            if not d: break
            want = {'エマ': 'emma/normal', 'フィオナ': 'fiona/normal'}.get(d[0])
            cur = wait_cur(pg, want, 3000)['cur'] if want else st(pg)['cur']; pages_seen += 1
            if want and cur != want: bad.append((k, i, d[0], cur))
            pg.click('#msg'); pg.wait_for_timeout(350)
        s_ = st(pg)
        if s_['vis'] or s_['cur'] is not None: bad.append((k, 'end', s_['cur']))
    check(pages_seen >= n and not bad, 'EMMA-005 %d pages over %d real lines: the portrait follows the speaker (Emma/Fiona), removed at the end. mismatches=%s' % (pages_seen, n, bad[:4]))
    ctx.close()
    # the real quest-offer conversation (choices) with the portrait: first talk = emma_closed, second = emma_q_offer
    ctx, pg = boot(b)
    pg.evaluate("FieldTalk.talk('emma')"); pg.wait_for_timeout(300); pg.evaluate("closeDialogue()")
    pg.evaluate("FieldTalk.talk('emma')"); pg.wait_for_timeout(500)
    btn = []
    for _ in range(4):
        btn = pg.evaluate("[...document.querySelectorAll('#msg .talkChoices button')].map(b=>b.textContent)")
        if btn: break
        pg.click('#msg'); pg.wait_for_timeout(300)
    s = st(pg)
    check(btn == ['探してみるよ', '今は難しい'] and s['cur'] == 'emma/normal', 'EMMA-005 quest-offer choices still shown, Emma visible %s %s' % (btn, s['cur']))
    pg.click('#msg .talkChoices button[data-choice="0"]'); pg.wait_for_timeout(400); s = st(pg)
    check('ありがとうねぇ' in s['txt'] and s['cur'] == 'emma/normal', 'EMMA-005 choice reply plays with Emma still shown')
    check(pg.evaluate("Quest.list().some(q=>q.id==='q_emma_charm'&&q.state==='active')"), 'EMMA-005 quest effect unchanged (q_emma_charm active)')
    ctx.close()
    # ---- load failure must not stop the conversation ----
    ctx, pg = boot(b, route=lambda r: r.abort()); pg.evaluate("FieldTalk.talk('emma')"); pg.wait_for_timeout(900); s = st(pg)
    check(not s['vis'] and 'エマ' in pg.evaluate("document.querySelector('#msg').textContent"), 'EMMA-005 image load failure: no portrait, dialogue still shown')
    first = pg.evaluate("document.querySelector('#msg .talkText').textContent"); pg.click('#msg'); pg.wait_for_timeout(300)
    check(pg.evaluate("document.querySelector('#msg .talkText')?document.querySelector('#msg .talkText').textContent:''") != first or pg.evaluate("getComputedStyle(document.querySelector('#msg')).display")=='none', 'EMMA-005 dialogue can still be advanced although the image failed')
    ctx.close()
    # ---- EMMA-006: other characters still show ----
    ctx, pg = boot(b)
    pg.evaluate("FieldTalk.loadTable({npc:'x_f',entries:[{id:'x_f1',priority:5,when:{},mode:'cycle',lines:[{char:'fiona',face:'smile',pages:['フィオナ「やあ」']}]}]})")
    pg.evaluate("FieldTalk.loadTable({npc:'x_l',entries:[{id:'x_l1',priority:5,when:{},mode:'cycle',lines:[{char:'lou',face:'angry',pages:['ルー「むっ」']}]}]})")
    pg.evaluate("FieldTalk.talk('x_f')"); s1 = wait_cur(pg, 'fiona/smile'); pg.evaluate("closeDialogue()")
    pg.evaluate("FieldTalk.talk('x_l')"); s2 = wait_cur(pg, 'lou/angry')
    check(s1['cur'] == 'fiona/smile' and s2['cur'] == 'lou/angry', 'EMMA-006 Fiona and Lou conversations unchanged')
    pg.evaluate("closeDialogue()"); pg.evaluate("FieldTalk.talk('emma')"); s3 = wait_cur(pg, 'emma/normal')
    pg.evaluate("closeDialogue()"); pg.evaluate("FieldTalk.talk('x_f')"); s4 = wait_cur(pg, 'fiona/smile')
    check(s3['cur'] == 'emma/normal' and s4['cur'] == 'fiona/smile', 'EMMA-006 switching Emma <-> Fiona')
    ctx.close()
    # ---- EMMA-007 layout ----
    for name, w, h, t in [('pc 1440x900', 1440, 900, False), ('phone 390x844', 390, 844, True), ('phone 360x640', 360, 640, True), ('phone landscape 844x390', 844, 390, True), ('tablet 768x1024', 768, 1024, True), ('tablet 1024x768', 1024, 768, True)]:
        ctx, pg = boot(b, w, h, t); pg.evaluate("FieldTalk.talk('emma')"); s = wait_cur(pg, 'emma/normal'); bx = s['box'] or [0, 0, 0, 0]
        check(s['vis'] and bx[0] >= -1 and bx[2] <= s['W'] + 1 and bx[1] >= -1 and bx[3] <= s['msgTop'] + 6, 'EMMA-007 %s: portrait inside the viewport and above the dialogue box %s' % (name, [round(x) for x in bx]))
        ctx.close()
    # ---- asset ----
    d = open(os.path.join(ROOT, 'img/portraits/emma/emma_normal.png'), 'rb').read()
    from PIL import Image; import io
    im = Image.open(io.BytesIO(d)); a = im.split()[3]
    check(im.size == (1024, 1536) and im.mode == 'RGBA' and a.getextrema() == (0, 254), 'ASSET-001 emma_normal.png: 1024x1536 RGBA with the original alpha (0..254)')
    check(hashlib.sha256(d).hexdigest() == 'f4dfd09d08e3bd333743f677afbe84e4e1771b295863e92a96a3b4c0904114b2', 'ASSET-001 emma_normal.png byte-identical to the supplied master (sha256 f4dfd09d...)')
    check(not [e for e in errs if 'PAGEERR' in e], 'ASSET-002 no page errors: %s' % errs[:3])
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)
