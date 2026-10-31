"""24A: manual expressions on real production dialogue, immutable words/control-flow and actual canvas pixels."""
import os,json,hashlib,subprocess,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=Path(os.environ.get('QA_OUT','/tmp/24a'));OUT.mkdir(parents=True,exist_ok=True);fails=[]
def check(ok,label,detail=None):
 print(('ok   ' if ok else 'FAIL ')+label,'' if ok else detail,flush=True)
 if not ok:fails.append(label)
S=json.loads(subprocess.check_output(['node','tools/qa/story_expression_snapshot.cjs'],cwd=ROOT));A=json.loads((ROOT/'docs/qa/evidence/directive-24a/dialogue-audit.json').read_text());names={'エイダン':'aidan','フィオナ':'fiona','ルー':'lou','エマ':'emma'}
check(S['behavior_sha256']==A['behavior_sha256']=='4d9c203b00d45ac245a369350b8fe910bf4e2a1164e5cb492aa82bf7b1c10114','all original words/page counts/order/choices/conditions/flags/rewards equal main')
check(S['index_logic_sha256']=='49479618b91079b9fcb423125f9938f1d7a793d17ef62959b125718fb3013bd5','all index HTML/control logic unchanged except explicit presentation bridge/metadata/cache')
allpages=[dict(key=c['key'],page=i,**p) for c in S['conversations'] for i,p in enumerate(c['pages'])]+S['cinematic']+S['training']+S['inspection'];actual={(p['key'],p['page']):p for p in allpages if p.get('char')};expected={(p['key'],p['page']):p for p in A['assignments']}
check(len(allpages)==388 and len(actual)==len(expected)==115 and set(actual)==set(expected),'388 audited display-path pages;115 authored targets, no missing target')
check(all(all(actual[k].get(f)==p[f] for f in ['speaker','text','char','face','side']) for k,p in expected.items()),'manual audited face mapping exactly equals production data')
check(all(names[p['speaker']]==p['char'] and (p['char']!='lou' or p['face'] not in ['smile','relieved']) for p in actual.values()),'correct speaker/character; excluded Lou faces never assigned')
check(len(A['exclusions'])==25 and not A['unhandled'] and all(not next(p for p in allpages if (p['key'],p['page'])==(e['key'],e['page'])).get('char') for e in A['exclusions']),'CG22 and mixed3 intentionally hidden; eligible unhandled0')
for name in ['PHASE4_FORMAL_ADOPTION_21A.json','PHASE4_EXPRESSION_BLINK_FORMAL_22A.json','PHASE4_FIONA_22BR4.json']:
 l=json.loads((ROOT/'docs/portraits'/name).read_text());check(all(hashlib.sha256((ROOT/a['file']).read_bytes()).hexdigest()==a['sha256'] for a in l['assets']+l.get('other_protected_pngs',[])),'protected official PNG SHA '+name)
PIX=r'''async()=>{const s=TalkPortrait.status,r=PortraitRegistry,c=r.get(s.char),k=c.crop,b=r.blinkOf(s.char,s.face);const got=document.querySelector('#talkPortrait canvas').getContext('2d').getImageData(0,0,k.w,k.h).data;const load=u=>new Promise((ok,no)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=no;im.src=u});const cv=document.createElement('canvas');cv.width=k.w;cv.height=k.h;const x=cv.getContext('2d');x.drawImage(await load(r.imageUrl(s.char,s.face)),k.x,k.y,k.w,k.h,0,0,k.w,k.h);if(s.eye&&b)for(const e of Object.values(b.eyes))x.drawImage(await load(e.urls[s.eye-1]),e.box[0]-k.x,e.box[1]-k.y);const want=x.getImageData(0,0,k.w,k.h).data;return got.every((v,i)=>v===want[i])}'''
with sync_playwright() as p:
 b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},has_touch=True);pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto('http://localhost:%s/index.html?title=0'%os.environ.get('PORT','8765'));pg.wait_for_function("LoadCoordinator.phase==='READY'");pg.evaluate('closeDialogue()')
 def status(e,label,anchor='#msg'):
  if not e.get('char'):
   pg.wait_for_timeout(35);check(pg.evaluate('!TalkPortrait.status.visible&&TalkPortrait.status.blink===null'),label+': no sticky portrait on narration/other speaker');return
  pg.wait_for_function("e=>TalkPortrait.status.visible&&TalkPortrait.status.char===e.char&&TalkPortrait.status.face===e.face&&TalkPortrait.status.side===e.side",arg=e,timeout=10000)
  pg.wait_for_timeout(35);check(pg.evaluate(PIX),label+': real canvas exact approved expression/eye pixels')
  g=pg.evaluate("""anchor=>{const a=document.querySelector('#talkPortrait').getBoundingClientRect(),z=document.querySelector(anchor).getBoundingClientRect(),s=TalkPortrait.status;return{inside:a.left>=-1&&a.top>=-1&&a.right<=innerWidth+1&&a.bottom<=z.top+1,input:getComputedStyle(document.querySelector('#talkPortrait')).pointerEvents==='none',one:!s.blink||s.blink.timers===1}}""",anchor)
  check(g['inside'] and g['input'] and g['one'],label+': above text, inside viewport, input unobstructed, one timer',g)
  if e['char'] in ['fiona','emma'] and e['face'] in ['smile','relieved']:check(pg.evaluate('!TalkPortrait.status.blinkReady&&TalkPortrait.status.blink===null'),label+': closed-eye expression stays static')
 def setup(key,index):
  stage=6 if key.startswith('atk_') else 15 if key=='liam_intro' else 3
  q={'emma_q_found_early':'unaccepted','emma_q_report':'complete','emma_q_active':'active','emma_q_offer':'unaccepted','emma_q_thanks':'reported'}.get(key,'__blocked__');seen=['emma_closed'] if key=='emma_q_offer' else []
  pg.evaluate("""a=>{FieldTalk.cancel();devResetScreens();closeDialogue();Quest.reset();Inventory.reset();PrologueProgress.seed(a.open?3:0);storyStage=a.stage;FieldTalk.load({seen:a.seen,cycle:{[a.key]:a.index},flags:{}});FieldTalk.setQuestProvider(()=>a.quest);if(a.key==='emma_q_found_early')Inventory.add('charm_windward');}""",dict(key=key,index=index,stage=stage,quest=q,seen=seen,open=key=='emma_open'))
 def inspect_pages(c):
  for i,e in enumerate(c['pages']):
   check(pg.locator('#msg .talkText').text_content()==re.sub(r'　(?=[^\s「」　]{1,10}「)', '\n', e['text']),c['key']+'/'+str(i)+': original text/page order')
   status(e,c['key']+'/'+str(i))
   if i<len(c['pages'])-1:
    same=e.get('char') and e.get('char')==c['pages'][i+1].get('char')
    if same:pg.evaluate("window.hiddenFrames=[];window.hObs=new MutationObserver(()=>hiddenFrames.push(document.querySelector('#talkPortrait').hidden));hObs.observe(document.querySelector('#talkPortrait'),{attributes:true,attributeFilter:['hidden']})")
    pg.locator('#msg').tap()
    if same:
     pg.wait_for_timeout(35);check(pg.evaluate('hiddenFrames.every(v=>!v)'),c['key']+': same-character expression switch has no blank frame');pg.evaluate('hObs.disconnect()')
 # Actual registered tables, never preview/test-injected tables. Seed only ordinary quest/stage state to select each real entry.
 cases=[c for c in S['conversations'] if any(p.get('char') for p in c['pages'])]
 for width,height in [(390,844),(844,390)]:
  pg.set_viewport_size({'width':width,'height':height})
  for c in cases:
   basekey=c['key'].split('/reply')[0];entry,index=basekey.rsplit('/',1);setup(entry,int(index));check(pg.evaluate('id=>FieldTalk.pick(id)?.id',c['npc'])==entry,c['key']+': actual production condition selects original entry')
   check(pg.evaluate('id=>FieldTalk.talk(id)',c['npc']),c['key']+': production talk starts')
   if '/reply' in c['key']:
    parent=next(x for x in S['conversations'] if x['key']==basekey)
    for _ in range(len(parent['pages'])-1):pg.locator('#msg').tap()
    pg.locator('.talkChoices button').nth(int(c['key'].split('/reply')[1])).tap()
   inspect_pages(c);FieldTalkActive=pg.evaluate('FieldTalk.active');pg.evaluate('FieldTalk.cancel()')
  # Legacy training data reaches the same real owner/renderer without replacing say's original text handling.
  pg.evaluate("devResetScreens();closeDialogue();storyStage=0;document.querySelector('#fiona').onclick()")
  status(S['training'][0],'training stage0');check(pg.evaluate('storyStage===1'),'original training first-talk stage remains1')
  pg.evaluate("closeDialogue();document.querySelector('#fiona').onclick()");status(S['training'][1],'training stage1')
  pg.evaluate("closeDialogue();startTraining();winTraining()");pg.wait_for_function('storyStage===3',timeout=5000);status(S['training'][3],'training real victory')
  pg.evaluate("closeDialogue();document.querySelector('#fiona').onclick()");status(S['training'][2],'training stage>=2')
  pg.evaluate("FieldTalk.cancel();devResetScreens();closeDialogue();RildeVillage.force('peace');RildeVillage.hook({hook:'rilde_wind_stone'},null)");status(S['inspection'][0],'actual peaceful wind-stone inspection')
  pg.evaluate("closeDialogue();RildeVillage.force('ruin');RildeVillage.hook({hook:'rilde_wind_stone'},null)");status(S['inspection'][1],'actual ruin wind-stone narration');pg.evaluate('RildeVillage.force(null)')
  # Actual owning scene click handlers; text and page-order unchanged.
  for key,scene,anchor,start,index in [('hillLines','cinema','#cinemaText','startHillScene()','hillIndex'),('returnLines','returnScene','#returnText','startReturnScene()','returnIndex'),('escapeLines','escapeScene','#escapeText','startEscapeScene()','escapeIndex'),('aftermathLines','aftermathScene','#aftermathText','startRaiderAftermath()','aftermathIndex'),('fortLines','fortScene','#fortText','startFortFinale()','fortIndex')]:
   pg.evaluate('FieldTalk.cancel();devResetScreens();closeDialogue();'+start)
   expected_pages=[x for x in S['cinematic'] if x['key']==key]
   for i,e in enumerate(expected_pages):
    check(pg.locator(anchor).text_content()==S['behavior']['arrays'][key][i],key+'/'+str(i)+': exact original cinematic text')
    status(e,key+'/'+str(i),anchor)
    if i<len(expected_pages)-1:pg.locator('#'+scene).tap()
   pg.locator('#'+scene).tap();pg.wait_for_timeout(100)
   if key=='aftermathLines':check(pg.evaluate('storyStage===14&&PartyManager.support.joined'),'real aftermath end keeps stage/support join')
   if key=='fortLines':check(pg.evaluate('storyStage===15&&!TalkPortrait.status.visible'),'fort completion keeps original progression and cleanup')
  pg.screenshot(path=str(OUT/f'24a_finished_{width}x{height}.png'))
 # Real first target dialogue with manual blink verifies actual canvas changes and clears on takeover/LOAD/battle/CG.
 setup('scene_cliff_night_1',0);pg.evaluate("FieldTalk.talk('scene_cliff_night')");pg.locator('#msg').tap();pg.wait_for_function("TalkPortrait.status.char==='fiona'");pg.locator('#msg').tap();pg.wait_for_function("TalkPortrait.status.char==='aidan'")
 pg.evaluate("window.samples=[];window.eyeObs=new MutationObserver(()=>samples.push(TalkPortrait.status.eye));eyeObs.observe(document.querySelector('#talkPortrait'),{attributes:true,attributeFilter:['data-eye']});TalkPortrait.blinkNow()")
 pg.wait_for_function('samples.includes(4)&&samples.at(-1)===0',timeout=2500);check(pg.evaluate(PIX),'production assigned expression exact full canvas after real blink');pg.evaluate('eyeObs.disconnect()')
 for action in ['FieldTalk.cancel()','FieldTalk.load(FieldTalk.serialize())',"document.body.classList.add('battleMode')",'devResetScreens();startLouIntro()']:
  pg.evaluate("FieldTalk.cancel();devResetScreens();closeDialogue();storyStage=0;document.querySelector('#fiona').onclick();"+action);pg.wait_for_timeout(250);check(pg.evaluate('!TalkPortrait.status.visible&&TalkPortrait.status.blink===null'),'newlegacy owner late-load cleanup '+action)
 check(not errors,'no application errors',errors);ctx.close();b.close()
print('FAILS',len(fails));raise SystemExit(1 if fails else 0)
