"""22B-R4: exact R4/R3/R2 routing, protected originals and actual rendered brow/blink pixels."""
import os,json,hashlib,subprocess,io,base64
from pathlib import Path
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=Path(os.environ.get('QA_OUT','/tmp/22br4'));OUT.mkdir(parents=True,exist_ok=True);fails=[]
def check(ok,label,detail=None):
 print(('ok   ' if ok else 'FAIL ')+label,'' if ok else detail,flush=True)
 if not ok:fails.append(label)
L=json.loads((ROOT/'docs/portraits/PHASE4_FIONA_22BR4.json').read_text());A=L['assets'];manifest=(ROOT/L['manifest']).read_bytes()
check(hashlib.sha256(manifest).hexdigest()==L['manifest_sha256']=='afde3b64e9f396e1efc4df99547e086f40b15dec05eb71c2e9f9d8a2dc9baa60','pinned exact29file source manifest (R4 3,R3 2,R2 24)')
locked={f:h for h,f in [line.split(maxsplit=1) for line in manifest.decode().splitlines()]}
check(len(locked)==29 and len({a['file'] for a in A})==29 and {a['file']:a['sha256'] for a in A}==locked,'candidate ledger exact pinned29path/SHA set; no independent ledger rebaselining')
check(len(A)==29 and all(a['adoption_status']=='PROVISIONAL_ANDROID_QA' and hashlib.sha256((ROOT/a['file']).read_bytes()).hexdigest()==a['sha256'] for a in A),'all29candidate SHA exact; NOT formally adopted')
rev={'R4':('0849e3fff948c5f27e57549bba5e638c42269423',3),'R3':('1bbcaa28e2a7f8785b85dfb9df64a6e3b152689c',2),'R2':('e91228b328bf382399d3bcbcf55ce4520ec058d8',24)}
check(all(sum(a['revision']==v for a in A)==n and all(a['source_commit']==sha for a in A if a['revision']==v) for v,(sha,n) in rev.items()),'R4/R3/R2 exactsource commits/counts; no mixed older candidates')
reg={a['source_path']:a for a in json.loads((ROOT/'docs/assets/ASSET_REGISTRY.json').read_text())['assets']}
check(all(reg[a['file']]['approval_status']=='PROVISIONAL_ANDROID_QA' and reg[a['file']]['android_status']=='NOT_RUN' and reg[a['file']]['source_sha256']==a['sha256'] for a in A),'central candidateledger exactSHA/provisional/AndroidNOT_RUN')
script="const fs=require('node:fs'),vm=require('node:vm'),c={window:{}};vm.runInNewContext(fs.readFileSync('js/field/portrait-registry.js','utf8'),c);const r=c.window.PortraitRegistry;console.log(JSON.stringify(Object.fromEntries(r.get('fiona').faces.map(f=>[f,{base:r.imageUrl('fiona',f),blink:r.blinkOf('fiona',f)}]))));"
routes=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT))
for a in A:
 f=a['expression'];check((a['file'] in [u for e in routes[f]['blink']['eyes'].values() for u in e['urls']]) if a['revision']=='R2' else routes[f]['base']==a['file'],'exact route '+a['file'].split('/fiona/')[-1])
for f in ['smile','relieved']:check(routes[f]['blink'] is None,f+' remains static')
# Original formal manifests stay independently protected in m49/m51. Also enforce candidate image geometry/alpha and no unrelated body edits.
for a in A:
 new=Image.open(ROOT/a['file']).convert('RGBA');old=Image.open(ROOT/a['replaces_runtime']).convert('RGBA');check(new.size==old.size,a['revision']+'/'+a['expression']+': original dimensions')
 if a['revision']!='R2':
  check(new.getchannel('A').tobytes()==old.getchannel('A').tobytes(),a['expression']+': full alpha unchanged')
  diff=ImageChops.difference(new,old).convert('RGB').getbbox();check(diff and diff[0]>=490 and diff[1]>=230 and diff[2]<=680 and diff[3]<=365,a['expression']+': only approved eye/brow area differs',diff)
PREP=r'''async()=>{
 window.exprObserver?.disconnect();
 const s=TalkPortrait.status,R=PortraitRegistry,c=R.get(s.char),k=c.crop,b=R.blinkOf(s.char,s.face);
 const load=u=>new Promise((r,j)=>{const im=new Image();im.onload=()=>r(im);im.onerror=j;im.src=u});
 const base=await load(R.imageUrl(s.char,s.face)),expected={};
 for(const[eye,e]of Object.entries(b.eyes)){
  const imgs=await Promise.all(e.urls.map(load));expected[eye]=[];
  for(let state=0;state<5;state++){const cv=document.createElement('canvas');cv.width=e.box[2]-e.box[0];cv.height=e.box[3]-e.box[1];const x=cv.getContext('2d');x.drawImage(base,...e.box.slice(0,2),cv.width,cv.height,0,0,cv.width,cv.height);if(state)x.drawImage(imgs[state-1],0,0);expected[eye].push(x.getImageData(0,0,cv.width,cv.height).data)}
 }
 const full=document.createElement('canvas');full.width=k.w;full.height=k.h;full.getContext('2d').drawImage(base,k.x,k.y,k.w,k.h,0,0,k.w,k.h);
 window.exprBasePNG=full.toDataURL();window.exprExpected=expected;window.exprBlink=b;window.exprCrop=k;
 window.inspectEye=()=>{const state=TalkPortrait.status.eye,cv=document.querySelector('#talkPortrait canvas'),x=cv.getContext('2d');let ok=true,bothChanged=true;const pngs={};
  for(const[eye,e]of Object.entries(exprBlink.eyes)){const a=e.box,w=a[2]-a[0],h=a[3]-a[1],data=x.getImageData(a[0]-exprCrop.x,a[1]-exprCrop.y,w,h);const want=exprExpected[eye][state],original=exprExpected[eye][0];ok=ok&&data.data.every((v,i)=>v===want[i]);bothChanged=bothChanged&&data.data.some((v,i)=>v!==original[i]);}
  return{state,ok,bothChanged,t:Date.now()};};
 window.beginEyeSamples=()=>{window.exprSamples=[];window.exprObserver?.disconnect();window.exprObserver=new MutationObserver(()=>exprSamples.push(inspectEye()));exprObserver.observe(document.querySelector('#talkPortrait'),{attributes:true,attributeFilter:['data-eye']})};
 window.eyePNGs=()=>{const out={};const x=document.querySelector('#talkPortrait canvas').getContext('2d');for(const[eye,e]of Object.entries(exprBlink.eyes)){const a=e.box,cv=document.createElement('canvas');cv.width=a[2]-a[0];cv.height=a[3]-a[1];cv.getContext('2d').putImageData(x.getImageData(a[0]-exprCrop.x,a[1]-exprCrop.y,cv.width,cv.height),0,0);out[eye]=cv.toDataURL()}return out};
 return document.querySelector('#talkPortrait canvas').toDataURL()===exprBasePNG;
}'''
URL='http://localhost:%s/index.html?title=0'%os.environ.get('PORT','8765')
with sync_playwright() as p:
 browser=p.chromium.launch();ctx=browser.new_context(viewport={'width':390,'height':844},has_touch=True);pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(URL);pg.wait_for_function("LoadCoordinator.phase==='READY'");pg.evaluate('closeDialogue()');pg.locator('#devBtn').tap();pg.locator('#devPortraitTest').tap();pg.locator('#devPortraitChars [data-char=fiona]').tap()
 saved=pg.evaluate('JSON.stringify({stage:storyStage,storage:{...localStorage}})')
 def ready(f,blink=True):pg.wait_for_function("([f,b])=>TalkPortrait.status.visible&&TalkPortrait.status.char==='fiona'&&TalkPortrait.status.face===f&&(!b||TalkPortrait.status.blinkReady)",arg=[f,blink])
 def unfold():
  if pg.locator('#devPortraitStage').evaluate("e=>e.classList.contains('folded')"):pg.locator('#devPortraitToggle').tap()
 for f in ['angry','sad','worried','smile','relieved']:
  unfold();pg.locator('#devPortraitFaces [data-face='+f+']').tap();ready(f,f not in ['smile','relieved']);pg.wait_for_timeout(80)
  check('QA候補' in pg.locator('#devPortraitFaces [data-face='+f+']').inner_text(),f+': visible QA candidate label')
  if f in ['smile','relieved']:
   check(pg.locator('#devPortraitBlink').is_disabled() and pg.evaluate('TalkPortrait.status.blink===null&&!TalkPortrait.status.blinkReady'),f+': static in actual DEV')
   pg.screenshot(path=str(OUT/f'22br4_{f}_portrait.png'));continue
  check(pg.evaluate(PREP),f+': actual full open canvas equals corrected base')
  # Capture full face+fringe; exact compositor comparison includes brow pixels, not only data-eye.
  captures=[]
  for state in range(5):
   pg.locator('#devPortraitFrames button').nth(state).tap();check(pg.evaluate('inspectEye().ok'),f+': actual eye pixels state'+str(state))
   png=pg.locator('#talkPortrait canvas').evaluate("e=>e.toDataURL()");im=Image.open(io.BytesIO(base64.b64decode(png.split(',')[1]))).convert('RGBA')
   # Compare decoded pixels using browser canvas on both sides. Raw Pillow RGBA preserves invisible RGB and uses different alpha rounding.
   rendered=pg.evaluate(r"""async()=>{const s=TalkPortrait.status,r=PortraitRegistry,c=r.get(s.char),k=c.crop,b=r.blinkOf(s.char,s.face);const load=u=>new Promise((ok,no)=>{const i=new Image();i.onload=()=>ok(i);i.onerror=no;i.src=u});const v=document.createElement('canvas');v.width=k.w;v.height=k.h;const x=v.getContext('2d');x.drawImage(await load(r.imageUrl(s.char,s.face)),k.x,k.y,k.w,k.h,0,0,k.w,k.h);if(s.eye)for(const e of Object.values(b.eyes))x.drawImage(await load(e.urls[s.eye-1]),e.box[0]-k.x,e.box[1]-k.y);const actual=document.querySelector('#talkPortrait canvas').getContext('2d').getImageData(0,0,k.w,k.h).data,want=x.getImageData(0,0,k.w,k.h).data;return actual.every((a,i)=>a===want[i]);}""")
   check(rendered,f+': full canvas exact correctedbase+R2 state'+str(state)+' (no old brow restoration)')
   captures.append(im.crop((420,185,550,285)))
  strip=Image.new('RGBA',(130*5,100))
  for i,im in enumerate(captures):strip.paste(im,(130*i,0))
  strip.resize((1300,200)).save(OUT/f'22br4_{f}_actual_brow_states.png')
  pg.locator('#devPortraitStop').tap();check(pg.evaluate("document.querySelector('#talkPortrait canvas').toDataURL()===exprBasePNG&&TalkPortrait.status.blink===null"),f+': exact complete reopen')
  for action in ['Blink','Auto','Loop']:
   pg.evaluate('beginEyeSamples()');pg.locator('#devPortrait'+action).tap()
   if action=='Auto':check(pg.evaluate('TalkPortrait.status.blink.nextAt-Date.now()>=2900&&TalkPortrait.status.blink.nextAt-Date.now()<=6000'),f+': 3–6second interval')
   pg.wait_for_function('exprSamples.some(s=>s.state===4)&&exprSamples.at(-1).state===0',timeout=8000);check(pg.evaluate('exprSamples.every(s=>s.ok)&&exprSamples.some(s=>s.state===4&&s.bothChanged)'),f+': '+action+' real pixel change and restore');pg.evaluate('exprObserver.disconnect()');pg.locator('#devPortraitStop').tap()
  for w,h in [(390,844),(844,390)]:
   pg.set_viewport_size({'width':w,'height':h});pg.wait_for_timeout(80)
   for side in ['Left','Right']:
    unfold();pg.locator('#devPortrait'+side).tap();ready(f);pg.wait_for_timeout(50)
    check(pg.evaluate("()=>{const a=document.querySelector('#talkPortrait').getBoundingClientRect(),z=document.querySelector('#devPortraitControls').getBoundingClientRect();return a.top>=0&&a.left>=0&&a.right<=innerWidth+1&&a.bottom<=innerHeight+1&&!(a.left<z.right&&a.right>z.left&&a.top<z.bottom&&a.bottom>z.top)}"),f+': '+str(w)+'x'+str(h)+' '+side+' UI')
   pg.screenshot(path=str(OUT/f'22br4_{f}_{w}x{h}.png'))
  pg.set_viewport_size({'width':390,'height':844});unfold();pg.emulate_media(reduced_motion='reduce');pg.locator('#devPortraitAuto').tap();check(pg.evaluate('TalkPortrait.status.eye===0&&TalkPortrait.status.blink===null'),f+': reduced-motion respected');pg.emulate_media(reduced_motion='no-preference')
 pg.locator('#devPortraitClose').tap();check(pg.evaluate('!TalkPortrait.status.visible&&TalkPortrait.status.blink===null&&DevPortraitTest.timers===0'),'DEV exit clears timers')
 check(pg.evaluate('JSON.stringify({stage:storyStage,storage:{...localStorage}})')==saved,'DEV preserves story/save')
 # Production FieldTalk API uses exact same versioned routes; no scenario table edits.
 for f in ['angry','sad','worried','smile','relieved']:
  table={'npc':'qa22br4','entries':[{'id':'qa22br4','priority':100,'when':{},'mode':'cycle','lines':[{'char':'fiona','face':f,'pages':['QA22BR4']}]}]}
  pg.evaluate('t=>{FieldTalk.loadTable(t);FieldTalk.talk(t.npc)}',table);ready(f,f not in ['smile','relieved']);pg.wait_for_timeout(60)
  check(pg.evaluate("f=>document.querySelector('#talkPortrait').dataset.face===f",f),f+': production FieldTalk selects corrected expression')
  if f not in ['smile','relieved']:
   check(pg.evaluate(PREP),f+': production exact corrected canvas');pg.evaluate('beginEyeSamples();TalkPortrait.blinkNow()');pg.wait_for_function('exprSamples.some(s=>s.state===4)&&exprSamples.at(-1).state===0',timeout=2500);check(pg.evaluate('exprSamples.every(s=>s.ok)'),f+': production R2 blink pixels');pg.evaluate('exprObserver.disconnect()')
  pg.locator('#msg').tap();pg.wait_for_timeout(50);check(pg.evaluate('!TalkPortrait.status.visible&&TalkPortrait.status.blink===null'),f+': conversation end clears')
 for action in ['FieldTalk.cancel()','FieldTalk.load(FieldTalk.serialize())',"document.body.classList.add('battleMode')",'devResetScreens();closeDialogue();startLouIntro()']:
  pg.evaluate("document.body.classList.remove('battleMode');devResetScreens();closeDialogue();FieldTalk.loadTable({npc:'qa22cancel',entries:[{id:'c',priority:100,when:{},mode:'cycle',lines:[{char:'fiona',face:'angry',pages:['QA']}]}]});FieldTalk.talk('qa22cancel')");ready('angry');pg.evaluate('TalkPortrait.blinkNow()');pg.evaluate(action);pg.wait_for_timeout(100);check(pg.evaluate('!TalkPortrait.status.visible&&TalkPortrait.status.blink===null'),'corrected Fiona lifecycle '+action)
 check(not errors,'no application errors',errors);ctx.close();browser.close()
print('FAILS',len(fails));raise SystemExit(1 if fails else 0)
