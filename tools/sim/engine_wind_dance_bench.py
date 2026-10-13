#!/usr/bin/env python3
"""Execute the unmodified battle engine with seeded randomness and Playwright virtual time."""
import argparse, functools, http.server, json, os, subprocess, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
INIT=r'''seed=>{
let s=seed>>>0;const cosmeticRandom=Math.random;Math.random=()=>{if(!/battle-status\.js|battle-critical\.js/.test(new Error().stack))return cosmeticRandom();s=(1664525*s+1013904223)>>>0;return s/4294967296};
window.__bench={logs:[],damage:0,dodges:0,normal_recoveries:0,last:null,terminal:null};
const q=__bench,read=()=>window.__benchBattle==='normal'?{hp:[aahp,normalFHP],mp:normalFMP,round:PrologueCombat.roundNumber,boss:PrologueCombat.enemies.normal.reduce((n,e)=>n+e.hp,0)}:{hp:[rbHP,rbFHP],mp:rbFMP,round:rbRound,boss:rbBoss};
const sample=()=>{if(q.terminal||!window.__benchBattle)return;const n=read();if(q.last)for(let i=0;i<2;i++)q.damage+=Math.max(0,q.last.hp[i]-n.hp[i]);q.last=n};
for(const name of ['showBattleBanner','showRaiderBattleLog']){const orig=window[name];window[name]=function(t,...a){sample();q.logs.push(String(t));if(/回避(?!率)|身をかわした/.test(String(t)))q.dodges+=(String(t).match(/回避(?!率)/g)||[]).length||1;if(String(t).includes('態勢を立て直した'))q.normal_recoveries++;if(String(t).includes('時間を巻き戻す'))q.terminal={...read(),outcome:'defeat_rewind'};return orig.call(this,t,...a)}}
setInterval(sample,5);
}'''
def run(page,battle,condition,seed,max_rounds):
    query={'off':'','dance':'&feature=windDanceCommand','hit':'&feature=windDanceCommand&boltMana=hit','action':'&feature=windDanceCommand&boltMana=action'}[condition]
    page.goto(f'{page.base}/index.html?dev=1'+query)
    page.wait_for_function('window.PrologueCombat && window.WindDance')
    page.evaluate('closeDialogue();PrologueProgress.seed(3);WindDance.learn();BattleCutinManager.setMode("OFF")')
    page.clock.install()
    page.evaluate(INIT,seed)
    page.evaluate("b=>{window.__benchBattle=b;if(b==='normal')startAttackBattle('fieldGob1',100);else startRaiderBattle()}",battle)
    page.clock.fast_forward(2000)
    rows=[]; outcome='round_limit'; final=None
    for turn in range(1,max_rounds+1):
        state=page.evaluate("b=>({mp:b==='normal'?normalFMP:rbFMP,eva:BattleStatus.evasion(b,'fiona'),targets:PrologueCombat.enemies[b].filter(e=>e.hp>0).map(e=>({id:e.id,extra:e.extra}))})",battle)
        if not state['targets']:outcome='victory';break
        # Adds are prioritized, then boss; both allies select separately at execution.
        target=next((x['id'] for x in state['targets'] if x['extra']),state['targets'][0]['id'])
        kind='winddance' if condition!='off' and state['eva']==0 and state['mp']>=10 else 'atk'
        acts=[{'who':'aidan','kind':'atk','target':target},{'who':'fiona','kind':kind,'target':target}]
        page.evaluate("v=>{window.__roundDone=false;PrologueCombat.round(v.b,v.a).then(()=>window.__roundDone=true)}",{'b':battle,'a':acts})
        for _ in range(100):
            page.clock.fast_forward(1000)
            if page.evaluate('__roundDone || !!__bench.terminal'):break
        else:raise RuntimeError('round virtual-time timeout')
        row=page.evaluate("b=>({mp:b==='normal'?normalFMP:rbFMP,hp:b==='normal'?[aahp,normalFHP]:[rbHP,rbFHP],enemy:PrologueCombat.enemies[b].map(e=>({id:e.id,hp:e.hp})),terminal:__bench.terminal})",battle)
        rows.append({'turn':turn,'fiona_action':kind,**row})
        if row['terminal']:outcome='defeat_rewind';final=row['terminal'];break
        if not any(e['hp']>0 for e in row['enemy']):outcome='victory';final=row;break
    q=page.evaluate('__bench')
    return {'battle':battle,'condition':condition,'seed':seed,'outcome':outcome,'rounds':len(rows),'kill_round':len(rows) if outcome=='victory' else None,'end_mp':(final or rows[-1])['mp'],'support_actions_submitted':sum(x['fiona_action']=='winddance' for x in rows),'bolt_actions_submitted':sum(x['fiona_action']=='atk' for x in rows),'support_actions_executed':sum('フィオナの「風の舞」！' in t for t in q['logs']),'bolt_hits_executed':sum('フィオナの攻撃！' in t or 'フィオナが杖で応戦！' in t for t in q['logs']),'damage_sampled':q['damage'],'dodges_from_logs':q['dodges'],'normal_recoveries':q['normal_recoveries'],'logs':q['logs'],'round_trace':rows}
def main():
    a=argparse.ArgumentParser();a.add_argument('--port',type=int,default=8789);a.add_argument('--seeds',default='20261013');a.add_argument('--max-rounds',type=int,default=60);a.add_argument('--out',type=Path,required=True);args=a.parse_args()
    handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',args.port),handler);threading.Thread(target=server.serve_forever,daemon=True).start()
    rows=[];errors=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium'))
            for battle in ('normal','raider'):
                for condition in ('off','dance','hit','action'):
                    for seed in map(int,args.seeds.split(',')):
                        page=browser.new_page();page.base=f'http://127.0.0.1:{args.port}'
                        page.on('pageerror',lambda e:errors.append(str(e)))
                        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
                        r=run(page,battle,condition,seed,args.max_rounds);rows.append(r);print(battle,condition,r['outcome'],r['rounds'],r['end_mp'],flush=True);page.close()
            browser.close()
    finally:server.shutdown();server.server_close()
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps({'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'timing':'Playwright clock virtual time; cutins OFF via supported setting; damage sampled every5ms','results':rows,'errors':errors},ensure_ascii=False,indent=2))
    if errors:raise SystemExit('FAIL console/page errors '+str(errors[:3]))
if __name__=='__main__':main()
