"""EE: real hero wind-dance and enemy normal/smash paths, forced combat rolls."""
import json,os,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.qa.browser_support import server
fails=[];errors=[]
def ck(c,m):
 print(('ok   'if c else'FAIL ')+m,flush=True)
 if not c:fails.append(m)
with server(8800) as base,sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE')or None)
 for kind in ('normal_aidan','normal_fiona','smash'):
  for dodge in ((False,True) if kind!='smash' else ((False,False),(True,True),(False,True),(True,False))):
   pg=b.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('console',lambda m:errors.append(m.text)if m.type=='error'else None)
   pg.goto(base+'/index.html?dev=1&feature=windDanceCommand');pg.wait_for_function('window.PrologueCombat&&window.WindDance');pg.evaluate('closeDialogue();PrologueProgress.seed(3);WindDance.learn();BattleCutinManager.setMode("OFF");startRaiderBattle()');pg.clock.install();pg.clock.fast_forward(2000)
   pg.evaluate("window.__origRandom=Math.random;Math.random=()=>/battle-status\\.js/.test(new Error().stack)?.99:__origRandom();window.__castDone=false;PrologueCombat.round('raider',[{who:'aidan',kind:'guard'},{who:'fiona',kind:'winddance'}]).then(()=>__castDone=true)")
   for _ in range(100):
    pg.clock.fast_forward(1000)
    if pg.evaluate('__castDone'):break
   ck(pg.evaluate("BattleStatus.evasion('raider','aidan')===.15&&BattleStatus.evasion('raider','fiona')===.15"),kind+' real hero action applies wind dance')
   hp=[80,105]if kind=='normal_aidan'else[120,80]
   if kind=='smash':hp=[120,105]
   pg.evaluate("v=>{rbHP=v.hp[0];rbFHP=v.hp[1];rbBoss=1250;rbRound=1;rbAdds=0;rbQueued=v.smash;rbGuardA=rbGuardF=false;window.__poses=[];const names=['aidan','fiona'];const imgs=[document.querySelector('#rbAidan img'),document.querySelector('#rbFiona img')];for(let i=0;i<imgs.length;i++)if(imgs[i])new MutationObserver(()=>__poses.push({who:names[i],src:imgs[i].getAttribute('src')})).observe(imgs[i],{attributes:true,attributeFilter:['src']});window.__rolls=v.rolls;Math.random=()=>/battle-status\\.js/.test(new Error().stack)?(__rolls.shift()??.99):__origRandom();window.__enemyDone=false;PrologueCombat.enemyRound('raider').then(()=>__enemyDone=true)}",{'hp':hp,'smash':kind=='smash','rolls':([0 if x else .99 for x in dodge] if kind=='smash' else [0 if dodge else .99])})
   for _ in range(100):
    pg.clock.fast_forward(100)
    if pg.evaluate('__enemyDone'):break
   ck(pg.evaluate('__enemyDone'),kind+' enemy phase completes')
   after=pg.evaluate('[rbHP,rbFHP]');expected=[42,36]if kind=='smash'else([21,0]if kind=='normal_aidan'else[0,21]);loss=[hp[i]-after[i]for i in range(2)];ck(loss==([0 if dodge[i] else expected[i] for i in range(2)] if kind=='smash' else ([0,0]if dodge else expected)),kind+(' dodge'if dodge else' hit')+' HP loss '+str(loss))
   poses=pg.evaluate('__poses');targets=['aidan','fiona']if kind=='smash'else[kind.split('_')[1]]
   for who in targets:
    wanted=dodge[['aidan','fiona'].index(who)] if kind=='smash' else dodge
    ck(any(x['who']==who and who+'_evade' in(x['src']or'')for x in poses)==wanted,kind+' '+who+' evade asset matches rolled outcome '+str(poses))
   print('OBSERVED '+json.dumps({'kind':kind,'dodge':dodge,'hp_loss':loss,'poses':poses}));pg.close()
 b.close()
ck(not errors,'no console/page errors '+str(errors[:3]));print('FAILS',len(fails));sys.exit(bool(fails))
