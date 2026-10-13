#!/usr/bin/env python3
"""DD: production engine, browser-only parameter fixtures, serial seeded policies."""
import argparse,base64,copy,itertools,json,os,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.qa.browser_support import server
from tools.sim.engine_wind_dance_bench import INIT
DATA=(ROOT/'js/data/support-magic-data.js').read_text()
def run(page,base,battle,policy,regen,eva,cost,seed):
 fixture=DATA.replace('amount: 0.15','amount: '+str(eva/100)).replace('mp: 10','mp: '+str(cost)).replace('amount: 3, provisional','amount: '+str(regen)+', provisional')
 page.route('**/js/data/support-magic-data.js*',lambda r:r.fulfill(status=200,content_type='application/javascript',body=fixture))
 page.goto(base+'/index.html?dev=1&feature=windDanceCommand&boltMana=hit',wait_until='domcontentloaded');page.wait_for_function('window.PrologueCombat && window.WindDance')
 assert page.evaluate('([r,e,c])=>SupportMagicData.fiona_bolt_mana.amount===r&&SupportMagicData.wind_dance.effect.amount===e/100&&SupportMagicData.wind_dance.mp===c',[regen,eva,cost]), 'parameter fixture was not applied'
 page.evaluate('closeDialogue();PrologueProgress.seed(3);WindDance.learn();BattleCutinManager.setMode("OFF")');page.clock.install();page.evaluate(INIT,seed)
 page.evaluate("b=>{window.__benchBattle=b;if(b==='normal')startAttackBattle('fieldGob1',100);else startRaiderBattle()}",battle);page.clock.fast_forward(2000)
 trace=[];outcome='round_limit'
 for turn in range(1,61):
  s=page.evaluate("b=>({hp:b==='normal'?[aahp,normalFHP]:[rbHP,rbFHP],mp:b==='normal'?normalFMP:rbFMP,tp:b==='normal'?aatp:rbTP,rune:b==='normal'?PrologueCombat.normalRune:rbRune,queued:b==='raider'&&rbQueued,eva:BattleStatus.evasion(b,'fiona'),targets:PrologueCombat.enemies[b].filter(e=>e.hp>0).map(e=>({id:e.id,hp:e.hp,extra:e.extra}))})",battle)
  if not s['targets']:outcome='victory';break
  target=next((x for x in s['targets'] if x['extra']),s['targets'][0]);ftarget=target['id']
  if target['hp']<=28 and len(s['targets'])>1:ftarget=next(x['id'] for x in s['targets'] if x['id']!=target['id'])
  ak='wind' if battle=='raider' and s['rune']>=100 else ('skill' if s['tp']>=30 else 'atk')
  threshold={'attack':.2,'heal':.65,'dance':.3,'mixed':.5}[policy];ratios=[s['hp'][0]/(120 if battle=='raider'else 100),s['hp'][1]/(105 if battle=='raider'else 90)]
  fk='atk'
  if min(ratios)<threshold and s['mp']>=8:fk='heal';ftarget=['aidan','fiona'][ratios.index(min(ratios))]
  elif policy in ('dance','mixed') and s['eva']==0 and s['mp']>=cost and (policy=='dance' or s['queued'] or turn==1):fk='winddance'
  elif policy in ('attack','mixed') and s['mp']>=16 and not s['queued']:fk='windbloom'
  acts=[{'who':'aidan','kind':ak,'target':target['id']},{'who':'fiona','kind':fk,'target':ftarget}]
  page.evaluate("v=>{window.__roundDone=false;PrologueCombat.round(v.b,v.a).then(()=>window.__roundDone=true)}",{'b':battle,'a':acts})
  for _ in range(100):
   page.clock.fast_forward(1000)
   if page.evaluate('__roundDone||!!__bench.terminal'):break
  else:raise RuntimeError('round timeout')
  trace.append({'turn':turn,'acts':acts})
  if page.evaluate('!!__bench.terminal'):outcome='defeat_rewind';break
  if page.evaluate("b=>b==='raider'?rbBoss<=0:!PrologueCombat.enemies[b].some(e=>e.hp>0)",battle):outcome='victory';break
 q=page.evaluate('__bench');mp=page.evaluate('b=>b==="normal"?normalFMP:rbFMP',battle)
 return dict(battle=battle,policy=policy,regen=regen,evasion_points=eva,cost=cost,seed=seed,outcome=outcome,rounds=len(trace),damage=q['damage'],dodges=q['dodges'],recoveries=q['normal_recoveries'],end_mp=q['terminal']['mp']if q['terminal']else mp,clean_victory=outcome=='victory'and q['normal_recoveries']==0,trace=trace)
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--seeds',type=int,default=8);a.add_argument('--out',type=Path,required=True);a.add_argument('--smoke',action='store_true');args=a.parse_args();rows=[];errors=[]
 if args.out.exists():
  prev=json.loads(args.out.read_text());rows=prev['results'];errors=prev['errors']
 done={(r['battle'],r['policy'],r['regen'],r['evasion_points'],r['cost'],r['seed'])for r in rows}
 combos=list(itertools.product(('normal','raider'),('attack','heal','dance','mixed'),(0,3,4),(10,15,20),(8,10,12)))
 if args.smoke:combos=[('normal','mixed',3,15,10),('raider','mixed',3,15,10)]
 with server(8799) as base,sync_playwright() as p:
  b=p.chromium.launch(executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE')or None)
  for i,c in enumerate(combos):
   for seed in range(20261013,20261013+args.seeds):
    if (*c,seed)in done:continue
    if c[1] in ('attack','heal'):
     controls=[r for r in rows if(r['battle'],r['policy'],r['regen'],r['seed'])==(c[0],c[1],c[2],seed) and 'reused_from'not in r]
     keys=('outcome','rounds','damage','dodges','recoveries','end_mp','clean_victory','trace')
     if controls and all(all(r[k]==controls[0][k]for k in keys)for r in controls):
      src=controls[0];assert not any(a['kind']=='winddance'for t in src['trace']for a in t['acts'])
      row=copy.deepcopy(src);row['evasion_points']=c[3];row['cost']=c[4];row['reused_from']={'evasion_points':src['evasion_points'],'cost':src['cost'],'reason':'policy never casts winddance; support amount/cost have no executed math path'};rows.append(row);continue
    pg=b.new_page();pg.route('**/*.png*',lambda r:r.fulfill(status=200,content_type='image/png',body=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==')));pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('console',lambda m:errors.append(m.text)if m.type=='error'else None)
    rows.append(run(pg,base,*c,seed));pg.close()
   print(i+1,len(combos),c,rows[-1]['outcome'],flush=True)
   args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps({'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'fixture':'numeric SupportMagicData browser response; PNG responses1px; production code and adopted files unchanged','results':rows,'errors':errors,'complete':i+1==len(combos)},ensure_ascii=False))
  b.close()
 print('FAILS',len(errors));raise SystemExit(bool(errors))
if __name__=='__main__':main()
