# Acquire -> bag -> EQUIP tab -> stats. Training sword, Emma quest reward, cliff chest (stage-gated), UI click + keyboard. needs http.server 8765
import json, sys
from playwright.sync_api import sync_playwright
fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
    ev=lambda s: pg.evaluate(s)
    ev("PrologueProgress.seed(0);Quest.reset();FieldTalk.load(null);Inventory.reset();EquipmentManager.reset();MossForest.reset();localStorage.removeItem(SAVE_KEY)")
    base=ev("charStats('aidan')")
    # --- training
    ev("storyStage=1;startTraining()")
    check(ev("EquipmentManager.get('aidan').weapon")=='wooden_sword' and ev("Inventory.count('wooden_sword')")==0,'training start: Aidan takes up and wears the wooden sword (once)')
    check(ev("charStats('aidan')")==base,'wooden sword changes no stats (Raider/boss balance protected)')
    ev("storyStage=1;startTraining()"); check(ev("EquipmentManager.get('aidan').weapon")=='wooden_sword' and ev("Inventory.count('wooden_sword')")==0,'a second training start gives nothing more')
    ev("$('#battle').style.display='none';storyStage=3")
    # --- Emma reward
    ev("Quest.accept('q_emma_charm');Inventory.add('charm_windward')")
    got=ev("Quest.report('q_emma_charm')")
    check(any(g['id']=='emma_charm' for g in got) and ev("Inventory.count('emma_charm')")==1,'Emma quest report grants the Emma charm into the bag')
    check(ev("charStats('aidan')")==base,'just owning it changes nothing until equipped')
    # --- cliff chest gate
    ev("closeDialogue();storyStage=3"); ev("document.querySelector('#hillExit').click()"); pg.wait_for_timeout(1500)
    t=[x for x in ev("MossForest.map.treasurePoints") if x['id']=='tr_c1_cairn'][0]
    def click_chest():
        pg.evaluate("([x,y])=>MossForest.teleportFeet(x-60,y+40)",[t['x'],t['y']]); pg.wait_for_timeout(800)
        pt=pg.evaluate("([x,y])=>{const r=document.querySelector('#forestWorld').getBoundingClientRect(),s=FieldCamera.scale;return [r.left+x*s,r.top+(y-14)*s]}",[t['x'],t['y']])
        pg.mouse.click(pt[0],pt[1]); pg.wait_for_timeout(600)
    ev("storyStage=3"); click_chest()
    check(ev("Inventory.count('iron_sword')")==0 and 'tr_c1_cairn' not in ev("MossForest.opened"),'stage 3: the cairn chest stays shut (and unclaimed)')
    ev("storyStage=15"); click_chest()
    check(ev("Inventory.count('iron_sword')")==1 and ev("Inventory.count('potion')")>=1,'stage 15: chest opens and gives the iron sword (+ its other contents)')
    # --- UI
    ev("MossForest.hide&&0;document.querySelector('#menuOpen').click()"); 
    ev("renderSystemTab('equip')")
    check(pg.locator('#systemBody [data-eq-char]').count()>=1 and pg.locator('#systemBody [data-eq-slot]').count()==4,'EQUIP tab: character picker + 4 slots')
    check('木剣' in pg.inner_text('#systemBody'),'weapon slot shows the worn wooden sword')
    pg.click('[data-eq-slot="weapon"]'); txt=pg.inner_text('#systemBody')
    check('鉄の剣' in txt and 'ATK' in txt and '▲+5' in txt,'candidate list shows the iron sword with an ATK ▲+5 preview')
    before=int(pg.inner_text('[data-stat="atk"]'))
    pg.click('[data-eq-on="iron_sword"]')
    after=int(pg.inner_text('[data-stat="atk"]'))
    check(after==before+5 and ev("EquipmentManager.get('aidan').weapon")=='iron_sword' and ev("Inventory.count('wooden_sword')")==1,'clicking 装備: ATK %d -> %d, wooden sword back in the bag'%(before,after))
    pg.click('[data-eq-slot="accessory"]'); txt=pg.inner_text('#systemBody')
    check('エマの護符' in txt and 'DEF' in txt and 'HP' in txt,'accessory candidates show DEF/HP preview')
    # keyboard: focus the accessory slot, move with arrows, activate with Enter
    pg.focus('[data-eq-slot="accessory"]'); pg.keyboard.press('ArrowDown')
    check(pg.evaluate("document.activeElement.dataset.eqOn||document.activeElement.dataset.eqSlot||document.activeElement.dataset.eqOff||''")!='accessory','ArrowDown moves focus to the next control')
    pg.focus('[data-eq-on="emma_charm"]'); pg.keyboard.press('Enter'); pg.wait_for_timeout(100)
    check(ev("EquipmentManager.get('aidan').accessory")=='emma_charm' and ev("charStats('aidan')")['def']==base['def']+2,'Enter on a candidate equips it (DEF +2)')
    check(pg.evaluate("document.activeElement&&document.activeElement.closest('#systemBody')!==null"),'focus stays inside the menu after re-render')
    pg.click('[data-eq-off="accessory"]'); check(ev("charStats('aidan')")['def']==base['def'] and ev("Inventory.count('emma_charm')")==1,'外す restores DEF and returns the charm')
    pg.click('[data-eq-char="fiona"]'); txt=pg.inner_text('#systemBody')
    check('エマの護符' in txt and 'エイダン' not in pg.inner_text('.eqSlots') and pg.locator('[data-eq-on="iron_sword"]').count()==0,'Fiona: charm is offered, the iron sword (Aidan/Liam only) is not')
    # --- phone viewport: no horizontal overflow
    pg.set_viewport_size({'width':390,'height':760}); pg.wait_for_timeout(200)
    ov=pg.evaluate("(()=>{const m=document.querySelector('#systemMenu');return m.scrollWidth-m.clientWidth})()")
    check(ov<=1,'390px wide: no horizontal overflow (%d)'%ov)
    pg.screenshot(path='/tmp/claude-0/equip_mobile.png')
    # --- save round-trip with worn gear
    pg.set_viewport_size({'width':1280,'height':720})
    ev("EquipmentManager.equip('aidan','emma_charm');renderSystemTab('save');saveGrowthData();EquipmentManager.reset();Inventory.reset();loadGrowthData()")
    check(ev("EquipmentManager.get('aidan').accessory")=='emma_charm' and ev("Inventory.count('wooden_sword')")==1,'save/load keeps worn gear and the bag')
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)
