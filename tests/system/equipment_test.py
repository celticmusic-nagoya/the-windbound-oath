# (404s are the fake wooden frames the stub manifest points at.)
# Equipment: equip/unequip <-> inventory bag, final stats, weapon motionVariant switching (BattleMotion), save round-trip. needs http.server 8765
import json, sys
from playwright.sync_api import sync_playwright
fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
# a fake manifest: aidan base attack 6 frames + 'aidan:wooden' attack 6 frames with a different hit frame
MAN={"base":"img/battle/characters/","motions":{
  "aidan":{"attack":{"dir":"aidan/motion/","pattern":"aidan_attack_{n}.png","frames":6,"ms":80,"hitFrame":4}},
  "aidan:wooden":{"attack":{"dir":"aidan/motion/","pattern":"aidan_wooden_attack_{n}.png","frames":4,"ms":100,"hitFrame":2}}}}
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and '404' not in m.text and errs.append(m.text))
    pg.route('**/img/battle/motion-manifest.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(MAN)))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
    ev=lambda s: pg.evaluate(s)
    ev("Inventory.reset();EquipmentManager.reset();localStorage.removeItem(SAVE_KEY)")
    base=ev("charStats('aidan')"); fbase=ev("charStats('fiona')")
    check(ev("Object.keys(EquipmentManager.get('aidan')).length")==0,'nobody wears anything at the start (old balance untouched)')
    check(ev("EquipmentManager.apply('aidan',charStats('aidan'))")==base,'no equipment -> stats identical')
    # bag
    check(ev("Inventory.add('wooden_sword')&&Inventory.add('iron_sword')&&Inventory.add('emma_charm')"),'equipment can be added to the inventory')
    check(ev("Inventory.count('wooden_sword')")==1 and [x['id'] for x in ev("Inventory.list('equip')")]==['wooden_sword','iron_sword','emma_charm'],'bag lists equipment (kind equip), separate from consumables/key items')
    check(ev("Inventory.list('consumable').every(x=>x.kind==='consumable')"),'consumable list unaffected')
    # equip
    r=ev("EquipmentManager.equip('aidan','wooden_sword')")
    s=ev("charStats('aidan')")
    check(r['ok'] and s['atk']==base['atk'] and ev("Inventory.count('wooden_sword')")==0,'equip wooden sword: no stat change (balance), bag count -1')
    check(s['def']==base['def'] and s['maxHp']==base['maxHp'],'other stats unchanged')
    check(ev("BattleMotion.info('aidan','attack')")['frames']==4 and ev("BattleMotion.hitDelay('aidan','attack')")==100,'weapon motionVariant "wooden" -> aidan:wooden motion (4 frames, hit at 100ms)')
    # swap
    r=ev("EquipmentManager.equip('aidan','iron_sword')"); s=ev("charStats('aidan')")
    check(r['ok'] and r['prev']=='wooden_sword' and s['atk']==base['atk']+5 and ev("Inventory.count('wooden_sword')")==1 and ev("Inventory.count('iron_sword')")==0,'swap: iron sword in, wooden sword back to the bag')
    check(ev("BattleMotion.info('aidan','attack')")['frames']==6,'iron variant has no frames -> falls back to base aidan motion (6 frames, hit 4)')
    # accessory + max HP
    ev("EquipmentManager.equip('aidan','emma_charm')"); s=ev("charStats('aidan')")
    check(s['def']==base['def']+2 and s['maxHp']==base['maxHp']+8 and s['atk']==base['atk']+5,'accessory adds DEF+2 / maxHP+8, stacks with weapon')
    # restrictions
    check(ev("EquipmentManager.equip('fiona','wooden_sword')")['reason']=='not_allowed','wearer restriction (equipBy) enforced')
    check(ev("EquipmentManager.equip('aidan','wooden_sword','head')")['reason']=='wrong_slot','slot mismatch refused')
    check(ev("EquipmentManager.equip('aidan','iron_sword')")['reason']=='not_in_bag','cannot equip what is not in the bag (already worn)')
    check(ev("EquipmentManager.equip('aidan','nonsense')")['reason']=='unknown_item','unknown id refused')
    check(ev("charStats('fiona')")==fbase,"another member's stats are untouched")
    # save / load
    ev("renderSystemTab('save');saveGrowthData()"); sv=json.loads(ev("localStorage.getItem(SAVE_KEY)"))
    check(sv['version']==30 and sv['equipment']['state']['aidan']=={'weapon':'iron_sword','accessory':'emma_charm'} and sv['inventory']['gear'].get('wooden_sword')==1,'save: ids only, bag and slots both stored (save version unchanged)')
    ev("EquipmentManager.reset();Inventory.reset()")
    check(ev("charStats('aidan')")==base and ev("BattleMotion.info('aidan','attack')")['frames']==6,'after reset: base stats')
    ev("loadGrowthData()"); s=ev("charStats('aidan')")
    check(s['atk']==base['atk']+5 and s['maxHp']==base['maxHp']+8 and ev("Inventory.count('wooden_sword')")==1 and ev("Inventory.count('iron_sword')")==0,'load restores worn pieces and the bag without duplicating')
    ev("EquipmentManager.unequip('aidan','weapon');EquipmentManager.equip('aidan','wooden_sword');renderSystemTab('save');saveGrowthData();EquipmentManager.reset();loadGrowthData()")
    check(ev("BattleMotion.info('aidan','attack')")['frames']==4,'load re-applies the weapon motion variant')
    r=ev("EquipmentManager.unequip('aidan','weapon')")
    check(r['ok'] and ev("charStats('aidan')")['atk']==base['atk'] and ev("BattleMotion.info('aidan','attack')")['frames']==6 and ev("Inventory.count('wooden_sword')")==1,'unequip: stats, bag and motion go back')
    # robustness
    ev("EquipmentManager.load({v:1,state:{aidan:{weapon:'emma_charm',head:'iron_sword',body:'zzz'},fiona:{weapon:'wooden_sword',accessory:'emma_charm'},ghost:5}})")
    check(ev("EquipmentManager.get('aidan')")=={} and ev("EquipmentManager.get('fiona')")=={'accessory':'emma_charm'},'corrupt/invalid save entries are dropped, valid ones kept')
    # old save without equipment
    sv.pop('equipment'); ev("EquipmentManager.reset()"); pg.evaluate("s=>localStorage.setItem(SAVE_KEY,s)",json.dumps(sv)); ev("loadGrowthData()")
    check(ev("Object.keys(EquipmentManager.get('aidan')).length")==0,'older save (no equipment field) loads with nothing worn')
    ev("localStorage.removeItem(SAVE_KEY)")
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)
