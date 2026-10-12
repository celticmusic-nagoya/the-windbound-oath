# Sword setting + equipment unlock: altar (Raider -> sword breaks -> Lou/Fiona stall -> oath contract), fort supply + EQUIP unlock, save round trip.
# Views: 390x844 and 844x390 (env OUT = screenshot dir, PORT). needs http.server
import os, sys, json
from playwright.sync_api import sync_playwright
PORT=os.environ.get('PORT','8765'); OUT=os.environ.get('OUT','docs/qa/sword-setting'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def ck(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
VIEWS={'portrait':(390,844),'landscape':(844,390)}
with sync_playwright() as p:
    b=p.chromium.launch()
    for view,(w,h) in VIEWS.items():
        ctx=b.new_context(viewport={'width':w,'height':h},is_mobile=True,has_touch=True); pg=ctx.new_page(); ev=pg.evaluate
        pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and '404' not in m.text and errs.append(m.text))
        pg.goto('http://localhost:%s/index.html?dev=1'%PORT); pg.wait_for_timeout(1800); ev('closeDialogue()')
        ev("PrologueProgress.seed(3);Quest.reset();Inventory.reset();EquipmentManager.reset();localStorage.removeItem(SAVE_KEY);giveStarterSword();syncEquipTab()")
        ck(ev("EquipmentManager.get('aidan').weapon")=='father_sword','[%s] start: Aidan holds the father sword'%view)
        ck(ev("document.querySelector('[data-stab=equip]').hidden")==True,'[%s] EQUIP tab hidden during the prologue'%view)
        # ---- altar
        ev("document.querySelector('#forestScene').style.display='none';startAltarScene()")
        A=ev("altarLines"); shots={13:'01_sword_breaks',17:'02_wind_dance_stall',20:'03_stone_reacts',27:'04_contract'}
        for i in range(1,28):
            ev("document.querySelector('#altarScene').click()")
            if i in shots:
                pg.wait_for_timeout(150)
                box=pg.evaluate("(()=>{const r=document.querySelector('#altarText').getBoundingClientRect();return [r.left,r.top,r.right,r.bottom,innerWidth,innerHeight]})()")
                ck(box[0]>=0 and box[2]<=box[4]+1 and box[1]>=0 and box[3]<=box[5]+1,'[%s] line %d text box inside the screen %s'%(view,i,[round(x) for x in box]))
                pg.screenshot(path='%s/%s_%s.png'%(OUT,view,shots[i]))
        ck(ev("EquipmentManager.get('aidan').weapon")=='oath_sword' and ev("Inventory.count('father_sword')")==0,'[%s] contract: oath sword equipped, father sword gone'%view)
        ck(ev("EquipmentManager.unequip('aidan','weapon')")['reason']=='locked','[%s] oath sword is locked'%view)
        ev("document.querySelector('#altarScene').style.display='none'")
        # ---- fort supply + unlock
        ev("storyStage=13;startFortFinale()"); F=ev("fortLines")
        gi=[i for i,l in enumerate(F) if '支給品' in l]; ck(gi==[6],'[%s] supply line index 6 (%s)'%(view,gi))
        for i in range(1,7): ev("document.querySelector('#fortScene').click()")
        ck(ev("EquipmentManager.isUnlocked()")==True and ev("Inventory.count('leather_cap')+Inventory.count('leather_armor')+Inventory.count('bronze_ring')")==3,'[%s] fort: gear granted, equipment unlocked'%view)
        pg.screenshot(path='%s/%s_05_fort_supply.png'%(OUT,view))
        ev("document.querySelector('#fortScene').style.display='none';storyStage=15")
        ev("document.querySelector('#menuOpen')&&document.querySelector('#menuOpen').click();renderSystemTab('equip')")
        ck(pg.locator('#systemBody [data-eq-slot]').count()==5,'[%s] EQUIP tab: 5 sockets'%view)
        ov=ev("(()=>{const m=document.querySelector('#systemMenu');return m?m.scrollWidth-m.clientWidth:0})()"); ck(ov<=1,'[%s] equip menu: no horizontal overflow (%s)'%(view,ov))
        pg.screenshot(path='%s/%s_06_equip_menu.png'%(OUT,view))
        # ---- save round trip
        ev("EquipmentManager.equip('aidan','leather_cap');renderSystemTab('save');saveGrowthData();EquipmentManager.reset();Inventory.reset();loadGrowthData()")
        ck(ev("EquipmentManager.get('aidan').weapon")=='oath_sword' and ev("EquipmentManager.get('aidan').head")=='leather_cap' and ev("EquipmentManager.isUnlocked()")==True,'[%s] save/load keeps oath sword, cap and unlock'%view)
        ctx.close()
    b.close()
print('errors',errs[:4]); print('FAILS',len(fails))
sys.exit(1 if (fails or errs) else 0)
