"""24B DEV display must agree with formal files and actual unchanged portrait/blink behavior."""
import os,json,hashlib,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=Path(os.environ.get('QA_OUT','/tmp/24b'));OUT.mkdir(parents=True,exist_ok=True);fails=[]
def check(ok,label,detail=None):
 print(('ok   ' if ok else 'FAIL ')+label,'' if ok else detail,flush=True)
 if not ok:fails.append(label)
formal={}
for f in ['PHASE4_FORMAL_ADOPTION_21A.json','PHASE4_EXPRESSION_BLINK_FORMAL_22A.json','PHASE4_FIONA_22BR4.json']:
 L=json.loads((ROOT/'docs/portraits'/f).read_text());formal.update({a['file']:a['sha256'] for a in L['assets']+L.get('other_protected_pngs',[])})
check(len(formal)==259 and all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in formal.items()),'all259 formal PNG match unchanged adoption SHA')
reg={a['source_path']:a for a in json.loads((ROOT/'docs/assets/ASSET_REGISTRY.json').read_text())['assets']}
faces={'aidan':['normal','smile','angry','worried','sad','surprised'],'fiona':['normal','smile','angry','sad','surprised','worried','determined','relieved'],'lou':['normal','angry','sad','surprised','worried','determined'],'emma':['normal','smile','angry','sad','surprised','worried','determined','relieved']}
labels={'normal':'通常','smile':'微笑み','angry':'怒り','sad':'悲しみ','surprised':'驚き','worried':'心配','determined':'決意','relieved':'安堵'}
with sync_playwright() as p:
 b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},has_touch=True);pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto('http://localhost:%s/index.html?title=0'%os.environ.get('PORT','8765'));pg.wait_for_function("LoadCoordinator.phase==='READY'");pg.evaluate('closeDialogue()');saved=pg.evaluate('JSON.stringify({talk:FieldTalk.serialize(),stage:storyStage,storage:{...localStorage}})');pg.locator('#devBtn').tap();pg.locator('#devPortraitTest').tap()
 def unfold():
  if pg.locator('#devPortraitStage').evaluate("e=>e.classList.contains('folded')"):pg.locator('#devPortraitToggle').tap()
 for width,height in [(390,844),(360,800),(844,390),(915,412)]:
  pg.set_viewport_size({'width':width,'height':height})
  for c,expected in faces.items():
   unfold();pg.locator('#devPortraitChars [data-char='+c+']').tap();pg.wait_for_function('c=>TalkPortrait.status.char===c&&TalkPortrait.status.visible',arg=c)
   check(pg.locator('#devPortraitFaces button').evaluate_all('(bs)=>bs.map(b=>b.dataset.face)')==expected,c+': selectable face list equals formal ledger')
   for f in expected:
    pg.locator('#devPortraitFaces [data-face='+f+']').tap();pg.wait_for_function('f=>TalkPortrait.status.face===f',arg=f);pg.wait_for_timeout(40)
    text=pg.locator('#devPortraitFaces [data-face='+f+']').inner_text();status=pg.locator('#devPortraitStatus').inner_text();blink=pg.evaluate('([c,f])=>PortraitRegistry.blinkOf(c,f)',[c,f]);url=pg.evaluate('([c,f])=>PortraitRegistry.imageUrl(c,f)',[c,f])
    paths=[url]+([u for e in blink['eyes'].values() for u in e['urls']] if blink else [])
    check(all(u in formal and reg[u]['approval_status']=='APPROVED' and reg[u]['source_sha256']==formal[u] for u in paths),c+'/'+f+': actual base/overlays all formally adopted')
    check(labels[f] in text and '('+f+')' in text and '正式採用' in text and '正式採用' in status and 'QA候補' not in text+status and 'PROVISIONAL' not in text+status,c+'/'+f+': unified exact formal label; no stale candidate warning')
    check(('瞬き対応' in text)==bool(blink) and ('静止表示' in text)==(not blink) and pg.locator('#devPortraitBlink').is_disabled()==(not blink),c+'/'+f+': label and actual controls agree')
    if not blink:check(pg.evaluate('!TalkPortrait.status.blinkReady&&TalkPortrait.status.blink===null'),'static expression no timer '+c+'/'+f)
    g=pg.locator('#devPortraitFaces [data-face='+f+']').evaluate('e=>{const p=document.querySelector("#devPortraitControls").getBoundingClientRect(),r=e.getBoundingClientRect();return{fits:e.scrollWidth<=e.clientWidth+1,left:r.left>=p.left,right:r.right<=p.right}}')
    check(g['fits'] and g['left'] and g['right'],c+'/'+f+': wrapped label stays inside control panel '+str(width),g)
   if c=='fiona':pg.screenshot(path=str(OUT/f'24b_formal_{width}x{height}.png'))
 pg.locator('#devPortraitClose').tap();check(pg.evaluate('DevPortraitTest.timers===0&&TalkPortrait.status.blink===null&&!TalkPortrait.status.visible'),'DEV close stops timers')
 check(pg.evaluate('JSON.stringify({talk:FieldTalk.serialize(),stage:storyStage,storage:{...localStorage}})')==saved,'DEV labels/selection leave story and save unchanged')
 # Existing generic discovery of aliases of approved art remains functional; unknown image references cannot masquerade as adopted.
 pg.evaluate("PortraitRegistry.define('approved_alias',{...PortraitRegistry.get('aidan'),name:'Approved alias'});PortraitRegistry.define('unapproved_fixture',{...PortraitRegistry.get('lou'),name:'Unapproved fixture',base:'unapproved-fixture/'})")
 pg.evaluate('DevPortraitTest.open()');check(pg.locator('#devPortraitChars [data-char=unapproved_fixture]').is_disabled(),'unapproved registered image sources excluded')
 pg.locator('#devPortraitChars [data-char=approved_alias]').tap();pg.wait_for_function("TalkPortrait.status.char==='approved_alias'");check('正式採用' in pg.locator('#devPortraitStatus').inner_text(),'generic approved-image alias remains selectable')
 pg.locator('#devPortraitClose').tap()
 # Existing Aidan preview uses the same Japanese terms/adoption status.
 pg.goto('http://localhost:%s/dev/talk-portrait-preview.html'%os.environ.get('PORT','8765'));pg.wait_for_function("TalkPortrait.status.visible");text=pg.locator('#panel').inner_text();check('心配 (worried)・正式採用' in text and '悲しみ (sad)・正式採用' in text,'preview nomenclature matches DEV')
 check(not errors,'no application errors',errors);ctx.close();b.close()
print('FAILS',len(fails));raise SystemExit(1 if fails else 0)
