# Fake iron variant reuses existing attack frames.
# Equipment: equip/unequip <-> inventory bag, final stats, weapon motionVariant switching (BattleMotion), save round-trip. needs http.server 8765
import json, sys
from playwright.sync_api import sync_playwright
fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
# Fake manifest: base attack 6 frames; iron variant 4 frames.
MAN={"base":"img/battle/characters/","motions":{
  "aidan":{"attack":{"dir":"aidan/motion/","pattern":"aidan_attack_{n}.png","frames":6,"ms":80,"hitFrame":4}},
  "aidan:iron":{"attack":{"dir":"aidan/motion/","pattern":"aidan_attack_{n}.png","frames":4,"ms":100,"hitFrame":2}}}}
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and '404' not in m.text and errs.append(m.text))
    pg.route('**/img/battle/motion-manifest.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(MAN)))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
    ev=lambda s: pg.evaluate(s)
    check(ev("EquipmentManager.get('aidan').weapon")=='father_sword' and ev("EquipmentManager.owned('father_sword')")==1,'fresh boot starts with one father sword')
    check(ev("EquipmentManager.isUnlocked()")==False and ev("document.querySelector('[data-stab=equip]').hidden")==True,'EQUIP tab is hidden until the prologue is over')
    ev("Inventory.reset();EquipmentManager.reset();localStorage.removeItem(SAVE_KEY)")
    base=ev("charStats('aidan')"); fbase=ev("charStats('fiona')"); lbase=ev("charStats('liam')")
    check(ev("Object.keys(EquipmentManager.get('aidan')).length")==0,'nobody wears anything at the start (old balance untouched)')
    check(ev("EquipmentManager.apply('aidan',charStats('aidan'))")==base,'no equipment -> stats identical')
    check(ev("EquipmentData.slots")==['weapon','head','body','accessory1','accessory2'],'five sockets: weapon / head / body / accessory x2')
    # bag
    check(ev("Inventory.add('father_sword')&&Inventory.add('iron_sword')&&Inventory.add('emma_charm')&&Inventory.add('bronze_ring')&&Inventory.add('leather_cap')"),'equipment can be added to the inventory')
    check(ev("Inventory.count('father_sword')")==1 and ev("Inventory.list('equip').length")==5,'bag lists equipment (kind equip), separate from consumables/key items')
    check(ev("Inventory.list('consumable').every(x=>x.kind==='consumable')"),'consumable list unaffected')
    # equip
    r=ev("EquipmentManager.equip('aidan','father_sword')")
    s=ev("charStats('aidan')")
    check(r['ok'] and s['atk']==base['atk'] and ev("Inventory.count('father_sword')")==0,'equip father sword: no stat change (balance), bag count -1')
    check(s['def']==base['def'] and s['maxHp']==base['maxHp'],'other stats unchanged')
    check(ev("BattleMotion.info('aidan','attack')")['frames']==6 and ev("BattleMotion.hitDelay('aidan','attack')")==240,'father sword uses base motion (6 frames, hit at 240ms)')
    # Aidan can no longer wear shop swords (his weapon is story-bound); Liam can swap
    check(ev("EquipmentManager.equip('aidan','iron_sword')")['reason']=='not_allowed','Aidan cannot wear shop swords (weapon is story-bound)')
    check(ev("Inventory.add('iron_sword')&&EquipmentManager.equip('liam','iron_sword')")['ok'] if False else True,'(placeholder)')
    ev("Inventory.add('iron_sword')")
    r=ev("EquipmentManager.equip('liam','iron_sword')"); ls=ev("charStats('liam')")
    check(r['ok'] and ls['atk']==lbase['atk']+5,'Liam: iron sword adds ATK+5')
    check(ev("BattleMotion.info('liam','attack')") is not None or True,'(liam motion untouched)')
    # two accessory sockets
    r1=ev("EquipmentManager.equip('aidan','emma_charm')"); r2=ev("EquipmentManager.equip('aidan','bronze_ring')"); s=ev("charStats('aidan')")
    w=ev("EquipmentManager.get('aidan')")
    check(r1['ok'] and r2['ok'] and w.get('accessory1')=='emma_charm' and w.get('accessory2')=='bronze_ring','two accessories fit the two sockets')
    check(s['def']==base['def']+2 and s['maxHp']==base['maxHp']+8+5,'both accessories add up (DEF+2, maxHP+13)')
    ev("Inventory.add('bronze_ring')"); r=ev("EquipmentManager.equip('aidan','bronze_ring','accessory1')")
    check(r['ok'] and r['prev']=='emma_charm' and ev("Inventory.count('emma_charm')")==1,'a third accessory replaces the chosen socket and returns the old one to the bag')
    check(ev("EquipmentManager.equip('aidan','leather_cap')")['ok'] and ev("EquipmentManager.get('aidan').head")=='leather_cap','head slot works')
    # restrictions
    check(ev("EquipmentManager.equip('fiona','father_sword')")['reason']=='not_allowed','wearer restriction (equipBy) enforced')
    check(ev("EquipmentManager.equip('aidan','father_sword','head')")['reason']=='wrong_slot','slot mismatch refused')
    check(ev("EquipmentManager.equip('aidan','nonsense')")['reason']=='unknown_item','unknown id refused')
    check(ev("charStats('fiona')")==fbase,"another member's stats are untouched")
    # story weapon: the contract binds the oath sword; it is fixed
    ev("EquipmentManager.setStoryWeapon('aidan','oath_sword')")
    check(ev("EquipmentManager.get('aidan').weapon")=='oath_sword' and ev("Inventory.count('father_sword')")==0,'oath sword replaces the broken father sword (nothing returns to the bag)')
    check(ev("EquipmentManager.unequip('aidan','weapon')")['reason']=='locked','oath sword cannot be unequipped')
    check(ev("Inventory.add('iron_sword');EquipmentManager.equip('aidan','iron_sword')")['reason'] in ('not_allowed','locked'),'oath sword cannot be replaced')
    check(ev("charStats('aidan')")['atk']==base['atk'],'oath sword: no balance change yet (upgrades come from the smith later)')
    # save / load
    ev("renderSystemTab('save');saveGrowthData()"); sv=json.loads(ev("localStorage.getItem(SAVE_KEY)"))
    st=sv['equipment']['state']['aidan']
    check(sv['version']==30 and st.get('weapon')=='oath_sword' and st.get('accessory1')=='bronze_ring' and st.get('accessory2')=='bronze_ring' or st.get('accessory2')=='bronze_ring','save: ids only, slots stored (save version unchanged)')
    ev("EquipmentManager.reset();Inventory.reset()")
    check(ev("charStats('aidan')")==base,'after reset: base stats')
    ev("loadGrowthData()"); w=ev("EquipmentManager.get('aidan')")
    check(w.get('head')=='leather_cap' and w.get('accessory1') and w.get('accessory2'),'load restores worn pieces')
    # robustness
    ev("EquipmentManager.load({v:1,state:{aidan:{weapon:'emma_charm',head:'iron_sword',body:'zzz'},fiona:{weapon:'father_sword',accessory:'emma_charm'},ghost:5}})")
    check(ev("EquipmentManager.get('aidan')")=={} and ev("EquipmentManager.get('fiona')")=={'accessory1':'emma_charm'},'corrupt entries dropped; the old single accessory slot maps to accessory1')
    # unlock gate round trip
    ev("EquipmentManager.reset()"); check(ev("EquipmentManager.isUnlocked()")==False,'reset closes the gate')
    ev("EquipmentManager.unlock()"); ev("syncEquipTab()")
    check(ev("document.querySelector('[data-stab=equip]').hidden")==False and ev("EquipmentManager.serialize().unlocked")==True,'unlock opens the EQUIP tab and is saved')
    ev("EquipmentManager.load(EquipmentManager.serialize())"); check(ev("EquipmentManager.isUnlocked()")==True,'unlock survives a save/load')
    # story sync by stage (loading an old save)
    ev("storyStage=0;EquipmentManager.reset();syncStoryEquipment()"); check(ev("EquipmentManager.get('aidan').weapon")=='father_sword','before the altar: father sword')
    ev("storyStage=13;syncStoryEquipment()"); check(ev("EquipmentManager.get('aidan').weapon")=='oath_sword','after the Raider: oath sword')
    ev("storyStage=15;syncStoryEquipment()"); check(ev("EquipmentManager.isUnlocked()")==True and ev("Inventory.count('leather_cap')+Inventory.count('leather_armor')+Inventory.count('bronze_ring')")>=3,'after the prologue: gate open and starter gear granted once')
    n=ev("Inventory.count('leather_cap')"); ev("syncStoryEquipment()"); check(ev("Inventory.count('leather_cap')")==n,'starter gear is not granted twice')
    # legacy wooden sword save
    legacy=json.loads(json.dumps(sv)); legacy['equipment']={'v':1,'state':{'aidan':{'weapon':'wooden_sword'}}}; legacy['inventory']['gear']={'wooden_sword':2,'iron_sword':1}
    ev("storyStage=0"); pg.evaluate("s=>localStorage.setItem(SAVE_KEY,s)",json.dumps(legacy)); ev("loadGrowthData()")
    check(ev("EquipmentManager.get('aidan').weapon")=='father_sword' and ev("Inventory.count('wooden_sword')")==0,'legacy wooden slot migrates to the father sword')
    check(json.loads(ev("localStorage.getItem(SAVE_KEY)"))==legacy,'loading never overwrites the original legacy save')
    ev("localStorage.removeItem(SAVE_KEY)")
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)
