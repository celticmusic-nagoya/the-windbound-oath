"""21C: exact120candidate bytes and real DEV/FieldTalk canvas pixels for15 expression blinks."""
import os,json,hashlib,base64,io
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=Path(os.environ['QA_OUT']) if os.getenv('QA_OUT') else None
if OUT:OUT.mkdir(parents=True,exist_ok=True)
fails=[]
def check(ok,label,detail=None):
 print(('ok   ' if ok else 'FAIL ')+label,'' if ok else detail,flush=True)
 if not ok:fails.append(label)
L=json.loads((ROOT/'docs/portraits/PHASE4_EXPRESSION_BLINK_21C.json').read_text());A=L['assets'];F=json.loads((ROOT/'docs/portraits/PHASE4_FORMAL_ADOPTION_21A.json').read_text());formal={a['file']:a for a in F['assets']}
check(len(A)==120 and len({a['file'] for a in A})==120,'exact120 distinct PNGs')
check(all(a['adoption_status']=='PROVISIONAL_ANDROID_QA' and a['source_commit']=='883624694e73a0839fc0db684ca76067765e7338' and hashlib.sha256((ROOT/a['file']).read_bytes()).hexdigest()==a['sha256'] for a in A),'all120 exactsource SHA and provisional status; no silent regeneration')
registry=json.loads((ROOT/'docs/assets/ASSET_REGISTRY.json').read_text())['assets'];newpaths={a['file']:a for a in A};registered={a['source_path']:a for a in registry if a['source_path'] in newpaths}
check(set(registered)==set(newpaths) and all(a['approval_status']=='PROVISIONAL_ANDROID_QA' and a['source_sha256']==newpaths[f]['sha256'] for f,a in registered.items()),'central registry registers exactly120newcandidate files, no formal promotion')
check(hashlib.sha256((ROOT/'docs/portraits/PHASE4_ADOPTED_SHA256SUMS').read_bytes()).hexdigest()==L['formal_lock_sha256'],'21A formal lock remains unchanged')
check(len(L['source_parent_assets'])==43 and all(a['file'] in formal and a['sha256']==formal[a['file']]['sha256'] and hashlib.sha256((ROOT/a['file']).read_bytes()).hexdigest()==a['sha256'] for a in L['source_parent_assets']),'19parent expressions +24normalblink match formal21A bytes')
for c in ['fiona','lou','emma']:
 check({p.name for p in (ROOT/f'assets/images/characters/portraits/{c}/provisional-21b/blink').glob('*.png')}=={Path(a['file']).name for a in A if a['character']==c},c+': only authorized40overlay files, no static/excluded face mixing')
 revision='provisional-20c' if c=='emma' else 'provisional-20e';folder=ROOT/f'assets/images/characters/portraits/{c}';normal=Image.open(folder/f'{c}_normal.png').convert('RGBA')
 for face in L['faces']:
  source=Image.open(folder/revision/'expressions'/f'{c}_{face}.png').convert('RGBA')
  for eye in ['L','R']:
   records=sorted([a for a in A if a['character']==c and a['expression']==face and a['eye']==eye],key=lambda a:a['stage']);check([a['stage'] for a in records]==[1,2,3,4],f'{c}/{face}/{eye}: exactly4stages')
   box=tuple(records[0]['box']);src=source.crop(box);norm=normal.crop(box);ns=list(norm.getdata());sp=list(src.getdata());union=[False]*len(ns);target=list(ns)
   for stage in range(1,5):
    p=Image.open(folder/revision/'blink'/f'normal_{eye}_s{stage}.png').convert('RGBA');px=list(p.getdata())
    union=[a or v[3]>0 for a,v in zip(union,px)]
    if stage==4:target=[v if v[3] else old for old,v in zip(ns,px)]
   valid=True;closed=None
   for a in records:
    im=Image.open(ROOT/a['file']).convert('RGBA');px=list(im.getdata());valid &= im.size==src.size and all(v[3] in (0,255) and (not v[3] or v[:3]!=old[:3]) for v,old in zip(px,sp))
    if a['stage']==4:closed=[v if v[3] else old for v,old in zip(px,sp)]
   check(valid,f'{c}/{face}/{eye}: source-sized binary-alpha patches change only opaque pixels')
   check(all(not area or a[:3]==b[:3] for area,a,b in zip(union,closed,target)),f'{c}/{face}/{eye}: s4equals formalnormal closed in normalblink area')
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
 b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},has_touch=True);pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(URL);pg.wait_for_function("LoadCoordinator.phase==='READY'");pg.wait_for_timeout(300);pg.evaluate('closeDialogue()')
 saved=pg.evaluate('JSON.stringify({talk:FieldTalk.serialize(),stage:storyStage,storage:{...localStorage}})')
 pg.locator('#devBtn').tap();pg.locator('#devPortraitTest').tap()
 def ready(c,f):pg.wait_for_function("([c,f])=>TalkPortrait.status.visible&&TalkPortrait.status.char===c&&TalkPortrait.status.face===f&&TalkPortrait.status.blinkReady",arg=[c,f])
 def unfold():
  if pg.locator('#devPortraitStage').evaluate("e=>e.classList.contains('folded')"):pg.locator('#devPortraitToggle').tap()
 for c in ['fiona','lou','emma']:
  pg.locator('#devPortraitChars [data-char='+c+']').tap()
  for face in L['faces']:
   pg.locator('#devPortraitFaces [data-face='+face+']').tap();ready(c,face);check(pg.evaluate(PREP),c+'/'+face+': exact formal expression at open')
   captures=[];states=[]
   for state in range(5):
    pg.locator('#devPortraitFrames button').nth(state).tap();r=pg.evaluate('inspectEye()');states.append(r)
    if OUT:captures.append(pg.evaluate('eyePNGs()'))
    if OUT and face=='surprised' and state in [1,4]:pg.screenshot(path=str(OUT/f'21c_{c}_surprised_frame{state}.png'))
   check(all(r['ok'] for r in states) and states[4]['bothChanged'],c+'/'+face+': all5 actual eye states match source; BOTH eyes visibly close')
   if OUT:
    for eye in ['L','R']:
     ims=[Image.open(io.BytesIO(base64.b64decode(a[eye].split(',')[1]))).convert('RGB') for a in captures];w,h=ims[0].size;strip=Image.new('RGB',(w*5,h))
     for i,im in enumerate(ims):strip.paste(im,(i*w,0))
     strip.resize((w*15,h*3)).save(OUT/f'21c_{c}_{face}_{eye}_actual.png')
   pg.locator('#devPortraitStop').tap();check(pg.evaluate("document.querySelector('#talkPortrait canvas').toDataURL()===exprBasePNG&&TalkPortrait.status.blink===null"),c+'/'+face+': stop restores exact full-canvas formal pixels')
   for control,timeout in [('Blink',2500),('Auto',7500)]:
    pg.evaluate('beginEyeSamples()');pg.locator('#devPortrait'+control).tap()
    if control=='Auto':
     gap=pg.evaluate('TalkPortrait.status.blink.nextAt-Date.now()');check(2900<=gap<=6000,c+'/'+face+': natural3–6second nextblink')
    pg.wait_for_function('exprSamples.some(s=>s.state===4)&&exprSamples.at(-1).state===0',timeout=timeout)
    sample=pg.evaluate('exprSamples');pg.evaluate('exprObserver.disconnect()')
    check(all(x['ok'] for x in sample) and any(x['state']==4 and x['bothChanged'] for x in sample) and [x['state'] for x in sample][-8:]==[1,2,3,4,3,2,1,0],c+'/'+face+': '+control+' actual source pixels close and return, including expected identical early frames')
    pg.locator('#devPortraitStop').tap()
   if face=='surprised':
    pg.evaluate('beginEyeSamples()');pg.locator('#devPortraitLoop').tap();pg.wait_for_function('exprSamples.filter(s=>s.state===4).length>=3',timeout=5000);sample=pg.evaluate('exprSamples');pg.evaluate('exprObserver.disconnect()');check(all(x['ok'] for x in sample),c+': surprised continuous3cycles actualpixels coherent');pg.locator('#devPortraitStop').tap()
   for w,h in [(390,844),(844,390)]:
    pg.set_viewport_size({'width':w,'height':h});pg.wait_for_timeout(60)
    for side in ['Left','Right']:
     unfold();pg.locator('#devPortrait'+side).tap();ready(c,face)
     g=pg.evaluate("""()=>{const a=document.querySelector('#talkPortrait').getBoundingClientRect(),z=document.querySelector('#devPortraitControls').getBoundingClientRect();return{inside:a.top>=0&&a.left>=0&&a.right<=innerWidth+1&&a.bottom<=innerHeight+1,overlap:a.left<z.right&&a.right>z.left&&a.top<z.bottom&&a.bottom>z.top}}""")
     check(g['inside'] and not g['overlap'],f'{c}/{face} {w}x{h} {side}: UI geometry',g)
   pg.set_viewport_size({'width':390,'height':844});pg.emulate_media(reduced_motion='reduce')
   for action in ['Auto','Blink','Loop']:
    pg.locator('#devPortrait'+action).tap();pg.wait_for_timeout(30)
    check(pg.evaluate('TalkPortrait.status.eye===0&&TalkPortrait.status.blink===null'),c+'/'+face+': '+action+' respects reducedmotion')
   pg.emulate_media(reduced_motion='no-preference');pg.locator('#devPortraitStop').tap()
  if c!='lou':
   for face in ['smile','relieved']:
    pg.locator('#devPortraitFaces [data-face='+face+']').tap();pg.wait_for_function('f=>TalkPortrait.status.face===f',arg=face);pg.wait_for_timeout(80)
    check(pg.evaluate('!TalkPortrait.status.blinkReady&&TalkPortrait.status.blink===null') and pg.locator('#devPortraitBlink').is_disabled(),c+'/'+face+': static, NO blink/unsupported overlays')
 pg.locator('#devPortraitClose').tap();check(pg.evaluate('!TalkPortrait.status.visible&&TalkPortrait.status.blink===null&&DevPortraitTest.timers===0'),'DEV exit clears all timers')
 check(pg.evaluate('JSON.stringify({talk:FieldTalk.serialize(),stage:storyStage,storage:{...localStorage}})')==saved,'DEV left actual story/save/flags unchanged')
 # Production FieldTalk API, test-only table: no committed scenario or progression data is altered.
 for c in ['fiona','lou','emma']:
  for face in L['faces']:
   table={'npc':'qa21c','entries':[{'id':'qa21c_entry','priority':100,'when':{},'mode':'cycle','lines':[{'char':c,'face':face,'pages':['QA21C']}]}]}
   pg.evaluate('t=>{FieldTalk.loadTable(t);FieldTalk.talk(t.npc)}',table);ready(c,face);check(pg.evaluate(PREP),c+'/'+face+': production FieldTalk metadata selects formal base')
   pg.evaluate('beginEyeSamples();TalkPortrait.blinkNow()');pg.wait_for_function('exprSamples.some(s=>s.state===4)&&exprSamples.at(-1).state===0',timeout=2500)
   check(pg.evaluate('exprSamples.every(s=>s.ok)&&exprSamples.some(s=>s.state===4&&s.bothChanged)'),c+'/'+face+': production dialogue canvas really blinks')
   pg.evaluate('exprObserver.disconnect()');pg.locator('#msg').tap();pg.wait_for_timeout(40)
   check(pg.evaluate('!TalkPortrait.status.visible&&TalkPortrait.status.blink===null'),c+'/'+face+': production conversation end clears timer')
 # Reuse the final test-only provider for explicit cancellation/load/CG cases.
 for action in ['FieldTalk.cancel()','FieldTalk.load(FieldTalk.serialize())',"document.body.classList.add('battleMode')",'devResetScreens();closeDialogue();startLouIntro()']:
  pg.evaluate("document.body.classList.remove('battleMode');devResetScreens();closeDialogue();FieldTalk.talk('qa21c')");ready('emma','determined');pg.evaluate('TalkPortrait.blinkNow()');pg.evaluate(action);pg.wait_for_timeout(100)
  check(pg.evaluate('!TalkPortrait.status.visible&&TalkPortrait.status.blink===null'),'new expression lifecycle '+action)
 check(not errors,'no page errors',errors);ctx.close();b.close()
print('FAILS',len(fails));raise SystemExit(1 if fails else 0)
