#!/usr/bin/env python3
"""Read-only independent sword/story audit; requires owned HTTP server at PORT."""
import json
import os
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

PORT = os.environ.get('PORT', '8783')
OUT = Path(os.environ.get('NIGHT_OUT', '/tmp/night-independent'))
OUT.mkdir(parents=True, exist_ok=True)
SHOTS = OUT/'independent-screenshots'; SHOTS.mkdir(exist_ok=True)
results = {'source_commit': 'be6af1f', 'views': {}, 'saves': [], 'checks': [], 'errors': []}


def check(condition, message, expected=True):
    results['checks'].append({'pass': bool(condition), 'message': message, 'expected': expected})
    print(('ok   ' if condition else 'FAIL ')+message, flush=True)


METRICS = '''selector=>{
 const el=document.querySelector(selector),r=el.getBoundingClientRect(),style=getComputedStyle(el);
 const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let node,tops=[],glyphs=[];
 while(node=walker.nextNode())for(let i=0;i<node.textContent.length;i++){
  const range=document.createRange();range.setStart(node,i);range.setEnd(node,i+1);
  for(const box of range.getClientRects()){if(box.width>.1){tops.push(Math.round(box.top*10)/10);glyphs.push([box.left,box.top,box.right,box.bottom]);}}
 }
 const lines=[...new Set(tops)];
 return {text:el.textContent,box:[r.left,r.top,r.right,r.bottom],viewport:[innerWidth,innerHeight],
 font:style.fontSize,lineHeight:style.lineHeight,lines:lines.length,
 boxInside:r.left>=0&&r.top>=0&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1,
 glyphsInside:glyphs.every(g=>g[0]>=0&&g[1]>=0&&g[2]<=innerWidth+1&&g[3]<=innerHeight+1),
 scrollOverflow:[el.scrollWidth-el.clientWidth,el.scrollHeight-el.clientHeight]};}'''

SNAPSHOT = '''()=>({stage:storyStage,weapon:EquipmentManager.get('aidan').weapon||null,
 slots:EquipmentManager.get('aidan'),unlocked:EquipmentManager.isUnlocked(),tabHidden:document.querySelector('[data-stab=equip]').hidden,
 inventory:Inventory.serialize(),learned:WindDance.learned(),visible:WindDance.commandVisible(),members:JSON.parse(JSON.stringify(PartyManager.members)),
 equipment:EquipmentManager.serialize(),gearCounts:Object.fromEntries(STARTER_GEAR.map(i=>[i,EquipmentManager.owned(i)]))})'''


def open_page(browser, viewport=(844, 390), flag=False):
    ctx = browser.new_context(viewport={'width':viewport[0], 'height':viewport[1]}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    page.on('pageerror', lambda e: results['errors'].append('PAGEERR '+str(e)))
    page.on('console', lambda m: results['errors'].append(m.text) if m.type == 'error' else None)
    page.goto(f'http://127.0.0.1:{PORT}/index.html?dev=1'+('&feature=windDanceCommand' if flag else ''))
    page.wait_for_timeout(1600)
    page.evaluate('closeDialogue();PrologueCombat.cancel();devResetScreens();MossForest.reset();document.body.classList.remove("battleMode","normalBattleMode","raiderBattleMode")')
    return ctx, page


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE', '/usr/bin/chromium'))
    for view, viewport in [('portrait',(390,844)),('landscape',(844,390))]:
        ctx, page = open_page(browser, viewport)
        ev = page.evaluate
        ev("PrologueProgress.seed(3);Inventory.reset();EquipmentManager.reset();storyStage=11;oathBound=false;delete PartyManager.members.fiona.learned;giveStarterSword();syncEquipTab();startAltarScene()")
        lines = ev('altarLines')
        ordered_prefixes = ['突然、光が黒紫に濁る', '森の奥から、地面を震わせる角笛', 'エイダンは父の剣で奇襲', 'だが次の瞬間、乾いた音とともに', '二撃目が迫る', '風の舞――', 'ルー「今だよ！', '古代石の表面を', 'エイダン「……もう、目の前で誰かを失うのは嫌だ。」', 'エイダンが柄を握る', 'レイダーが風の拘束を']
        order = [next((i for i,s in enumerate(lines) if s.startswith(prefix)), -1) for prefix in ordered_prefixes]
        check(all(i>=0 for i in order) and order==sorted(order) and len(set(order))==len(order),view+' fixed altar order')
        check(lines.count('エイダン「……もう、目の前で誰かを失うのは嫌だ。」')==1,view+' exact oath text once')
        check(max(map(len,lines))<=60,view+' all altar pages <=60 characters')
        check(not any('裂け目' in s or '落ちて' in s for s in lines),view+' old sword-rift beat absent from active altar')
        records = []
        for i, text in enumerate(lines):
            if i: ev("document.querySelector('#altarScene').click()")
            page.wait_for_timeout(80)
            metric = ev(METRICS, '#altarText')
            metric.update({'index':i,'chars':len(text),'weapon':ev("EquipmentManager.get('aidan').weapon||null"),'learned':ev('WindDance.learned()'),
                           'swordVisible':ev("getComputedStyle(document.querySelector('#oathSword')).display!=='none'"),
                           'goblinsVisible':ev("[...document.querySelectorAll('.altarGob')].map(e=>({id:e.id,display:getComputedStyle(e).display,opacity:getComputedStyle(e).opacity}))")})
            metric['actorOverlaps'] = ev('''()=>{const t=document.querySelector('#altarText').getBoundingClientRect();return ['altarAidan','altarFiona','altarLou','ag3','ag4'].filter(id=>{const r=document.getElementById(id).getBoundingClientRect();return r.left<t.right&&r.right>t.left&&r.top<t.bottom&&r.bottom>t.top})}''')
            metric['screenshot'] = f'{view}_altar_{i+1:02d}.png'
            page.screenshot(path=str(SHOTS/metric['screenshot']))
            records.append(metric)
        check(all(r['boxInside'] and r['glyphsInside'] for r in records),view+' every altar text box/glyph within viewport')
        brk, dance, contract = order[3], order[5], order[9]
        check(all(r['weapon']=='father_sword' for r in records[:brk]) and all(r['weapon'] is None for r in records[brk:contract]) and all(r['weapon']=='oath_sword' for r in records[contract:]),view+' weapon switches only at break and contract')
        check(all(not r['learned'] for r in records[:dance]) and all(r['learned'] for r in records[dance:]),view+' wind dance learned on first-cast page')
        ev("document.querySelector('#altarScene').click()")
        check(ev("document.body.classList.contains('raiderBattleMode')&&rbBoss===1250&&rbRune===25"),view+' final altar click starts unchanged Raider baseline')
        ev('PrologueCombat.cancel();devResetScreens();startFortFinale()')
        fort_records = []
        for i, text in enumerate(ev('fortLines')):
            if i: ev("document.querySelector('#fortScene').click()")
            page.wait_for_timeout(60)
            metric = ev(METRICS, '#fortText'); metric.update({'index':i,'chars':len(text),'unlocked':ev('EquipmentManager.isUnlocked()'),'screenshot':f'{view}_fort_{i+1:02d}.png'})
            if i==6: page.screenshot(path=str(SHOTS/metric['screenshot']))
            fort_records.append(metric)
        check(all(not r['unlocked'] for r in fort_records[:6]) and all(r['unlocked'] for r in fort_records[6:]),view+' EQUIP unlock only on supply page')
        check(all(r['boxInside'] and r['glyphsInside'] for r in fort_records),view+' all fort text fits viewport')
        before = ev('Object.fromEntries(STARTER_GEAR.map(i=>[i,EquipmentManager.owned(i)]))')
        ev('grantStarterGear(true);syncStoryEquipment()')
        check(ev('Object.fromEntries(STARTER_GEAR.map(i=>[i,EquipmentManager.owned(i)]))')==before,view+' supply repeat does not add gear')
        ev("document.querySelector('#fortScene').style.display='none';document.querySelector('#systemMenu').style.display='block';renderSystemTab('equip')")
        equip = ev('''()=>{const m=document.querySelector('#systemMenu'),b=document.querySelector('#systemBody');return {menuOverflow:m.scrollWidth-m.clientWidth,bodyOverflow:b.scrollWidth-b.clientWidth,slotCount:b.querySelectorAll('[data-eq-slot]').length,text:b.textContent,scrollHeight:b.scrollHeight,clientHeight:b.clientHeight}}''')
        page.screenshot(path=str(SHOTS/f'{view}_equip.png'))
        # Verify scroll access to lower candidates/controls in landscape as well as initial frame.
        ev("document.querySelector('#systemMenu').scrollTop=99999")
        equip['afterScroll'] = ev("(()=>{const m=document.querySelector('#systemMenu');return {top:m.scrollTop,height:m.scrollHeight,client:m.clientHeight}})()")
        check(equip['afterScroll']['height']<=equip['afterScroll']['client'] or equip['afterScroll']['top']>0,view+' EQUIP vertical scroll reaches lower content')
        page.screenshot(path=str(SHOTS/f'{view}_equip_scrolled.png'))
        check(equip['slotCount']==5 and equip['menuOverflow']<=1 and equip['bodyOverflow']<=1,view+' EQUIP five sockets and no horizontal overflow')
        results['views'][view] = {'viewport':viewport,'altar_order':order,'altar':records,'fort':fort_records,'equip':equip}
        ctx.close()

    # Build genuine v30-shaped old saves; each case has its own browser storage/member state.
    for stage in (0, 12, 15, 18):
        ctx, page = open_page(browser)
        ev = page.evaluate
        ev('storyStage=0;Inventory.reset();EquipmentManager.reset();PrologueProgress.seed(3);renderSystemTab("save");saveGrowthData()')
        saved = json.loads(ev('localStorage.getItem(SAVE_KEY)'))
        saved['equipment'] = {'v':1,'state':{'aidan':{'weapon':'wooden_sword','accessory':'emma_charm'}}}
        saved['inventory']['gear'] = {'wooden_sword':2,'iron_sword':1,'bronze_ring':1}
        saved['members']['fiona'].pop('learned',None)
        saved['prologue']['storyStage'] = stage
        page.evaluate('s=>localStorage.setItem(SAVE_KEY,JSON.stringify(s))',saved)
        result = ev('loadGrowthData()'); page.wait_for_timeout(300)
        state = ev(SNAPSHOT)
        results['saves'].append({'fixture_stage':stage,'fixture':saved,'load_result':result,'first':state})
        check(result is True,f'legacy stage{stage} load succeeds')
        check(state['slots'].get('accessory1')=='emma_charm' and 'accessory' not in state['slots'],f'legacy stage{stage} accessory -> accessory1')
        check(state['weapon']==('oath_sword' if stage>=13 else 'father_sword'),f'legacy stage{stage} story weapon')
        check(state['inventory']['gear'].get('father_sword')==2 and state['inventory']['gear'].get('iron_sword')==1 and 'wooden_sword' not in state['inventory']['gear'],f'legacy stage{stage} bag conversion preserves quantities/other weapons')
        check(state['unlocked']==(stage>=15) and state['learned']==(stage>=13),f'legacy stage{stage} unlock/learning restored')
        check(json.loads(ev('localStorage.getItem(SAVE_KEY)'))==saved,f'legacy stage{stage} original storage untouched by load')
        first_counts = state['gearCounts']
        ev('loadGrowthData()'); page.wait_for_timeout(100)
        check(ev(SNAPSHOT)['gearCounts']==first_counts,f'legacy stage{stage} repeated load has no double supply')
        ev('renderSystemTab("save");saveGrowthData()')
        resaved = json.loads(ev('localStorage.getItem(SAVE_KEY)'))
        ev('loadGrowthData()'); page.wait_for_timeout(100)
        check(ev(SNAPSHOT)['gearCounts']==first_counts and resaved['version']==30,f'legacy stage{stage} v30 resave/reload stable')
        results['saves'][-1]['resaved']=resaved
        # Detect learning carried from a later save into an earlier legacy save in the SAME session.
        if stage==15:
            early=json.loads(json.dumps(saved)); early['prologue']['storyStage']=0
            early['members']['fiona'].pop('learned',None)
            page.evaluate('s=>localStorage.setItem(SAVE_KEY,JSON.stringify(s))',early)
            ev('loadGrowthData()'); page.wait_for_timeout(100)
            results['cross_load']=ev(SNAPSHOT)
            check(not ev('WindDance.learned()'),'late-save -> early legacy-save clears wind dance learned state')
        ctx.close()
    # In the old main, Aidan could equip iron/steel swords. Verify that the new wearer restriction preserves them.
    for weapon in ('iron_sword','steel_sword'):
        ctx,page=open_page(browser);ev=page.evaluate
        ev('storyStage=15;PrologueProgress.seed(3);Inventory.reset();EquipmentManager.reset();renderSystemTab("save");saveGrowthData()')
        old=json.loads(ev('localStorage.getItem(SAVE_KEY)'));old['equipment']={'v':1,'state':{'aidan':{'weapon':weapon}}};old['inventory']['gear']={};old['members']['fiona'].pop('learned',None)
        page.evaluate('s=>localStorage.setItem(SAVE_KEY,JSON.stringify(s))',old)
        loaded=ev('loadGrowthData()');state=ev(SNAPSHOT)
        results.setdefault('old_shop_weapons',[]).append({'fixture':old,'load_result':loaded,'state':state,'owned':ev('id=>EquipmentManager.owned(id)',weapon)})
        check(loaded is True and ev('id=>EquipmentManager.owned(id)',weapon)==1,'legacy Aidan '+weapon+' remains owned after story-weapon migration')
        ctx.close()
    browser.close()
check(not results['errors'],'independent audit console/page errors zero')
(OUT/'independent-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
fails = sum(not r['pass'] for r in results['checks'])
print('FAILS',fails,flush=True)
sys.exit(1 if fails else 0)
