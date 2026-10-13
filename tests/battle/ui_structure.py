"""Battle layout audit: specification differences are findings, not test failures."""
import json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path(os.getenv('QA_OUTPUT','docs/qa/battle-ui-structure-20261013'));OUT.mkdir(parents=True,exist_ok=True)
SNAP="""kind=>{const normal=kind==='normal';const selectors={stage:normal?'#battleField':'#raiderBattle',log:normal?'#battleMsg2':'#rbMsg',toggle:normal?'#normalCommandToggle':'#rbCommandToggle',commands:normal?'#normalBattleCmd':'#rbCmd',items:'#normalItems',hud:normal?'#normalPartyHud':'#rbParty',aidan:normal?'#bAidan2':'#rbAidan',fiona:normal?'#bFiona2':'#rbFiona',enemy:normal?'#bGob':'#raiderSprite',nearA:normal?'#hudAidan':'.rbNearA',nearF:normal?'#hudFiona':'.rbNearF'};const out={classes:document.body.className,viewport:{w:innerWidth,h:innerHeight},regions:{},idle:BattleIdleMotion.status};
for(const [name,sel] of Object.entries(selectors)){let e=document.querySelector(sel);if(!e){out.regions[name]=null;continue}let r=e.getBoundingClientRect(),opacity=1,visible=true;for(let n=e;n;n=n.parentElement){let c=getComputedStyle(n);opacity*=Number(c.opacity);if(c.display==='none'||c.visibility==='hidden')visible=false}out.regions[name]={selector:sel,x:r.x,y:r.y,w:r.width,h:r.height,visible:visible&&opacity>.01&&r.width>0&&r.height>0,text:e.textContent.trim().slice(0,160)};}return out}"""
rows=[];findings=[];errors=[]
def overlaps(a,b):
 if not a or not b or not a['visible'] or not b['visible']:return 0
 return max(0,min(a['x']+a['w'],b['x']+b['w'])-max(a['x'],b['x']))*max(0,min(a['y']+a['h'],b['y']+b['h'])-max(a['y'],b['y']))
def record(view,kind,phase,snap):
 rows.append(dict(view=view,kind=kind,phase=phase,**snap))
 for key in ['commands','items']:
  q=snap['regions'][key]
  if q and q['visible'] and (q['x']<-.5 or q['y']<-.5 or q['x']+q['w']>snap['viewport']['w']+.5 or q['y']+q['h']>snap['viewport']['h']+.5):findings.append(dict(view=view,kind=kind,phase=phase,type='out_of_view',region=key,rect=q))
 for one,two in [('log','commands'),('log','aidan'),('log','fiona'),('log','enemy'),('commands','aidan'),('commands','fiona'),('items','aidan'),('items','fiona')]:
  area=overlaps(snap['regions'].get(one),snap['regions'].get(two))
  if area>.5:
   q=snap['regions'][two];findings.append(dict(view=view,kind=kind,phase=phase,type='overlap',regions=[one,two],area=area,pctOfSecond=100*area/(q['w']*q['h'])))
with server(8831) as base,sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':os.environ.get('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium')} if os.environ.get('PW_CHROMIUM_EXECUTABLE') or Path('/usr/bin/chromium').exists() else {}))
 for view,(w,h) in [('pc',(1280,720)),('pc-large',(1920,1080)),('portrait',(390,844)),('landscape',(844,390)),('small',(360,640))]:
  for kind in ['normal','raider']:
   ctx=b.new_context(viewport={'width':w,'height':h},is_mobile=view not in ('pc','pc-large'),has_touch=view not in ('pc','pc-large'));pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(base+'/index.html');pg.wait_for_function('window.MossForest && MossForest.active && !MossForest.busy',timeout=30000)
   if kind=='normal':
    pg.evaluate("devJump('forest')");pg.wait_for_function("MossForest.active && MossForest.mapId==='moss_forest_01_sunlit_path'",timeout=30000);pg.wait_for_timeout(600);pg.evaluate("closeDialogue();FieldMonsters.removeAll();startAttackBattle('forestGob1',112)")
   else:pg.evaluate("closeDialogue();devJump('raider')")
   pg.wait_for_function("InputManager.state()==='BATTLE_COMMAND'",timeout=30000);pg.wait_for_timeout(1600)
   for phase,cmd in [('initial',''),('open',('setNormalCommandDrawer' if kind=='normal' else 'setRaiderCommandDrawer')+'(true)'),('items',('openNormalItems' if kind=='normal' else 'openRaiderItems')+'()')]:
    if cmd:pg.evaluate(cmd)
    pg.wait_for_timeout(200);s=pg.evaluate(SNAP,kind);record(view,kind,phase,s);pg.screenshot(path=str(OUT/(view+'-'+kind+'-'+phase+'.png')))
   pg.evaluate("document.querySelector('#normalItems').classList.remove('isOpen');document.querySelector('#normalItems').style.display='none';"+('setNormalCommandDrawer' if kind=='normal' else 'setRaiderCommandDrawer')+'(true)')
   # Real engine round: skill -> defend -> enemy turn. No synthetic damage/cinematic.
   pg.evaluate("""kind=>{if(kind==='normal')aatp=60;else rbTP=60;window.qaTrace=[];window.qaInterval=setInterval(()=>qaTrace.push({t:performance.now(),classes:document.body.className}),25);window.qaDone=false;const target=PrologueCombat.targets(kind)[0].id;void PrologueCombat.round(kind,[{who:'aidan',kind:'skill',target},{who:'fiona',kind:'guard',target:'fiona'}]).finally(()=>qaDone=true)}""",kind)
   pg.wait_for_function("document.body.classList.contains('battlePresentationBusy') || document.body.classList.contains('actionCinematic')",timeout=10000);s=pg.evaluate(SNAP,kind);record(view,kind,'real-busy',s);pg.screenshot(path=str(OUT/(view+'-'+kind+'-busy.png')))
   for key in ['toggle','commands','items','log','hud','nearA','nearF']:
    q=s['regions'].get(key)
    if q and q['visible']:findings.append(dict(view=view,kind=kind,phase='real-busy',type='ui_visible_during_presentation',region=key))
   pg.wait_for_function('qaDone && !BattlePresentation.busy',timeout=30000);pg.evaluate('clearInterval(qaInterval)');s=pg.evaluate(SNAP,kind);s['trace']=pg.evaluate('qaTrace');record(view,kind,'restored',s)
   if not s['regions']['toggle']['visible'] and not s['regions']['commands']['visible']:findings.append(dict(view=view,kind=kind,phase='restored',type='command_not_restored'))
   # CSS gate probe is marked separately if actionCinematic did not occur naturally.
   pg.evaluate("document.body.classList.add('actionCinematic')");record(view,kind,'css-actionCinematic-probe',pg.evaluate(SNAP,kind));pg.evaluate("document.body.classList.remove('actionCinematic')")
   print('ok   measured',view,kind,flush=True);ctx.close()
 b.close()
(OUT/'results.json').write_text(json.dumps(dict(base='f0fe968',rows=rows,specDifferences=findings,errors=errors),ensure_ascii=False,indent=2));print('SPEC_DIFFS',len(findings));print('FAILS',int(bool(errors)));sys.exit(bool(errors))
