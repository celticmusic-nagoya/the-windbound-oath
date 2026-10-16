"""INT-02: the 14 command routes of ui_command_safety (same probe list), but against the REAL BattleLoading + BattleOpening + BattleAdmissionAdapter instead of a
test-only provider. Normal and boss battle, PC / portrait / landscape. Each probe must leave the battle state untouched while Loading is frozen and while the real
Opening holds the input; after the verified start, COMMAND works (a guard is queued and its effect is measured)."""
import os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail,flush=True)
    if not ok:fails.append(name)
START={'normal':"startAttackBattle('fieldGob3',100)",'raider':'startRaiderBattle()'}
SETUP="""b=>{window.__b=b;window.__wrong=0;window.__choose=b==='normal'?chooseNormalAct:choosePartyAct;
window.__open=b==='normal'?openNormalItems:openRaiderItems;window.__toggle=b==='normal'?setNormalCommandDrawer:setRaiderCommandDrawer;
window.__snap=()=>JSON.stringify({actor:b==='normal'?normalActor:rbActor,acts:b==='normal'?normalActs:rbActs,hp:[aahp,normalFHP,rbHP,rbFHP],mp:[normalFMP,rbFMP],tp:[aatp,rbTP],rune:rbRune,items:battleItems,pose:BattleActorState.get(b),html:document.querySelector('#normalItems').innerHTML});}"""
OPS="""()=>{
 const b=__b,g=BattleCommandGate,e=((PrologueCombat.targets(b)||[])[0]||{}).id;
 return [
 ['COMMAND',()=>__toggle(true)],['attack',()=>__choose('atk',e)],['skill',()=>__choose('skill',e)],
 ['magic-heal',()=>__choose('heal','aidan')],['magic-prayer',()=>__choose(b==='normal'?'prayer':'rune',null)],
 ['magic-windbloom',()=>__choose('windbloom',e)],['magic-winddance',()=>__choose('winddance',null)],
 ['item-open',()=>__open()],['guard',()=>__choose('guard','aidan')],
 ['target-open',()=>BattleTargetSelector.open({type:'none',battle:b,onConfirm:()=>__wrong++})],
 ['target-confirm',()=>BattleTargetSelector.confirm(e)],
 ['direct-commit-no-receipt',()=>g.commit(null,{who:'aidan',kind:'guard',target:'aidan'})],
 ['direct-commit-forged-receipt',()=>g.commit(Object.freeze({}),{who:'aidan',kind:'guard',target:'aidan'})],
 ['synthetic-button',()=>document.querySelector(b==='normal'?'#nGuard':'#rbGuard').click()]
 ].map(([route,fn])=>{const before=__snap();let threw=false;try{fn()}catch(x){threw=true}return {route,unchanged:before===__snap()&&__wrong===0&&!threw,detail:threw?'threw':''}});
}"""
def run_ops(pg):return pg.evaluate(OPS)
EXE=os.getenv('PW_CHROMIUM_EXECUTABLE') or None
with server(8833) as base,sync_playwright() as pw:
    br=pw.chromium.launch(executable_path=EXE)
    for view,w,h in [('pc',1280,720),('portrait',390,844),('landscape',844,390)]:
        for b in ['normal','raider']:
            c=br.new_context(viewport={'width':w,'height':h});pg=c.new_page();errs=[]
            pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None)
            pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.BattleAdmissionAdapter&&window.BattleLoading&&BattleMotion.loaded&&window.BattleUIState');pg.wait_for_timeout(1200)
            pg.evaluate('closeDialogue()');pg.evaluate(SETUP,b);pg.evaluate('BattleLoading.setLimits({minMs:1500})')
            tag='%s/%s'%(view,b)
            pg.evaluate(START[b]);pg.wait_for_timeout(300)
            ok=pg.evaluate('BattleLoading.frozen')
            rows=run_ops(pg) if ok else []
            check(ok and len(rows)==14 and all(r['unchanged'] for r in rows),'%s: Loading frozen - all 14 routes refused, state untouched'%tag,[r['route'] for r in rows if not r['unchanged']])
            # wait for the real Opening: Loading finished, Presentation still holding input
            t=time.time();seen=False
            while time.time()-t<9:
                if pg.evaluate('!BattleLoading.active&&BattlePresentation.busy&&document.body.classList.contains("battleMode")&&BattleAdmissionAdapter.request&&BattleAdmissionAdapter.request.gen!==null'):seen=True;break
                pg.wait_for_timeout(30)
            rows=run_ops(pg) if seen else []
            ph=pg.evaluate('BattleAdmissionAdapter.provider().phase') if seen else None
            check(seen and len(rows)==14 and all(r['unchanged'] for r in rows),'%s: real Opening holds input (adapter phase %s) - all 14 routes refused'%(tag,ph),[r['route'] for r in rows if not r['unchanged']])
            # verified start + Opening over: COMMAND opens; a guard is accepted and measured
            t=time.time()
            while time.time()-t<12 and not pg.evaluate("BattleCommandGate.canInteract(__b)"):pg.wait_for_timeout(40)
            can=pg.evaluate("BattleCommandGate.canInteract(__b)");pg.wait_for_timeout(300)
            check(can and pg.evaluate('BattleAdmissionAdapter.provider().phase')=='input','%s: admitted only at adapter phase input'%tag)
            s0=pg.evaluate('JSON.parse(__snap())');pg.evaluate("__choose('guard','aidan')");pg.wait_for_timeout(300);s1=pg.evaluate('JSON.parse(__snap())')
            eff=(s0['actor']=='aidan' and s1['actor']=='fiona') and (b=='normal' or len(s1['acts'])==len(s0['acts'])+1)
            check(eff,'%s: a real guard command is accepted after the verified start (effect measured)'%tag,(s0['actor'],s1['actor']))
            check(not errs,'%s: no browser errors'%tag,errs[:2]);c.close()
    br.close()
print('FAILS',fails);sys.exit(1 if fails else 0)
