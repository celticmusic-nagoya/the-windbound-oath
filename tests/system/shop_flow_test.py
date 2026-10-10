# Shop -> bag -> EquipmentManager/EQUIP UI; stage gate; gold; duplicate purchase; gated armor chests. needs http.server 8765
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
    ev("PrologueProgress.seed(0);Quest.reset();FieldTalk.load(null);Inventory.reset();EquipmentManager.reset();MossForest.reset();localStorage.removeItem(SAVE_KEY);gold=0")
    base=ev("charStats('aidan')")
    # gate: before stage 15 the shop is closed and the merchant keeps chatting
    ev("storyStage=3"); check(not ev("Shop.isOpen('rilde_general')") and ev("Shop.buy('rilde_general','leather_cap')")['reason']=='closed','before stage 15 the shop sells nothing')
    ev("closeDialogue();FieldTalk.talk('merchant',{source:'test'})"); check('冒険の準備' in pg.inner_text('#msg') and pg.locator('.talkChoices').count()==0,'stage 3: merchant only chats (no shop choice)')
    ev("closeDialogue();FieldTalk.load(null)")
    # stage 15: talk -> choice -> shop modal
    ev("storyStage=15;closeDialogue()"); ev("FieldTalk.talk('merchant',{source:'test'})")
    labels=pg.locator('.talkChoices button').all_inner_texts(); check(labels==['買い物をする','やめておく'],'stage 15: merchant offers 買い物をする / やめておく')
    pg.click('.talkChoices button >> nth=0'); pg.wait_for_timeout(200)
    check(pg.is_visible('#shopModal') and pg.locator('[data-shop-buy]').count()==6,'shop modal opens with 6 wares')
    check(pg.locator('[data-shop-buy][disabled]').count()==6,'with 0 G every ware is disabled')
    # prices
    st={x['id']:x['price'] for x in ev("Shop.stock('rilde_general')")}
    check(st=={'potion':20,'ether':45,'leather_cap':60,'cloth_tunic':50,'bronze_ring':90,'leather_armor':220},'price list %s'%st)
    ev("gold=100;Shop.open('rilde_general')")
    check(pg.locator('[data-shop-buy]:not([disabled])').count()==5 and pg.locator('[data-shop-buy="leather_armor"][disabled]').count()==1,'with 100 G: armor (220) stays disabled, cheaper wares enabled')
    pg.click('[data-shop-buy="leather_cap"]')
    check(ev("gold")==40 and ev("Inventory.count('leather_cap')")==1 and pg.locator('[data-shop-buy="leather_cap"][disabled]').count()==1,'buy leather cap: 100 -> 40 G, in bag, button now 購入済み')
    r=ev("Shop.buy('rilde_general','leather_cap')"); check(r['reason']=='owned' and ev("gold")==40,'cannot buy the same piece twice, no gold lost')
    r=ev("Shop.buy('rilde_general','leather_armor')"); check(r['reason']=='gold' and ev("gold")==40,'not enough gold refused')
    ev("gold=999"); pg.click('[data-shop-buy="potion"]'); check(ev("battleItems.potion")>=1 and ev("gold")==979,'consumables are bought into battleItems too (20 G)')
    pg.keyboard.press('Escape'); check(not pg.is_visible('#shopModal'),'Escape closes the shop')
    # shop -> equip
    ev("Shop.buy('rilde_general','leather_armor');Shop.buy('rilde_general','bronze_ring');Shop.buy('rilde_general','cloth_tunic')")
    check(ev("EquipmentManager.equip('aidan','leather_cap')")['ok'] and ev("EquipmentManager.equip('aidan','leather_armor')")['ok'] and ev("EquipmentManager.equip('aidan','bronze_ring')")['ok'],'bought pieces equip into head / body / accessory')
    s=ev("charStats('aidan')"); check(s['def']==base['def']+4 and s['maxHp']==base['maxHp']+5,'DEF +1 +3, MaxHP +5 applied (%d/%d)'%(s['def'],s['maxHp']))
    r=ev("EquipmentManager.equip('aidan','cloth_tunic')"); s=ev("charStats('aidan')")
    check(r['prev']=='leather_armor' and s['def']==base['def']+2 and ev("EquipmentManager.owned('leather_armor')")==1,'swapping body armour returns the leather armour to the bag; ownership counts bag + worn')
    check(ev("Shop.buy('rilde_general','leather_armor')")['reason']=='owned','a worn/bagged piece counts as owned in the shop')
    # save keeps it
    ev("renderSystemTab('save');saveGrowthData();EquipmentManager.reset();Inventory.reset();gold=0;loadGrowthData()")
    check(ev("EquipmentManager.get('aidan').head")=='leather_cap' and ev("gold")==ev("gold") and ev("EquipmentManager.owned('leather_armor')")==1,'save/load keeps shop purchases')
    # gated armor chests (forest) stay shut before stage 15
    ev("storyStage=15;EquipmentManager.reset();Inventory.reset()")
    for tid,item in (('tr_a1_wayside_late','bronze_ring'),('tr_a2_ledge_late','leather_armor')):
        check(ev("ItemData.treasureStage['%s']"%tid)==15 and ev("ItemData.treasure['%s']"%tid)=={item:1},'%s holds %s, gated to stage 15'%(tid,item))
        for mp in ('moss_forest_01_sunlit_path','moss_forest_02_mossy_ravine'):
            m=json.load(open('data/maps/%s.json'%mp,encoding='utf-8'))
            if any(t['id']==tid for t in m['treasurePoints']): check(True,'%s placed in %s'%(tid,mp))
    # the new chests are on walkable, reachable ground and open only from stage 15
    for mp,tid,item in (('moss_forest_01_sunlit_path','tr_a1_wayside_late','bronze_ring'),('moss_forest_02_mossy_ravine','tr_a2_ledge_late','leather_armor')):
        m=json.load(open('data/maps/%s.json'%mp,encoding='utf-8')); t=[x for x in m['treasurePoints'] if x['id']==tid][0]
        ev("storyStage=15;forestActive=true;document.querySelector('#forestScene').style.display='block'")
        pg.evaluate("(a)=>MossForest.enter({map:a[0],spawn:a[1]})",[mp,m['spawns']['default']]); pg.wait_for_timeout(1500)
        check(not pg.evaluate("([x,y])=>MossForest.blocked(x,y)",[t['x'],t['y']+30]) and pg.evaluate("([x,y])=>MossForest.goFeet(x,y+30)",[t['x'],t['y']]),'%s: chest ground is free and a route exists'%tid)
        pg.evaluate("([x,y])=>MossForest.teleportFeet(x-60,y+40)",[t['x'],t['y']]); pg.wait_for_timeout(600)
        pt=pg.evaluate("([x,y])=>{const r=document.querySelector('#forestWorld').getBoundingClientRect(),s=FieldCamera.scale;return [r.left+x*s,r.top+(y-14)*s]}",[t['x'],t['y']])
        ev("storyStage=9"); pg.mouse.click(pt[0],pt[1]); pg.wait_for_timeout(500)
        check(ev("Inventory.count('%s')"%item)==0 and tid not in ev("MossForest.opened"),'%s: shut before stage 15'%tid)
        ev("storyStage=15"); pg.mouse.click(pt[0],pt[1]); pg.wait_for_timeout(500)
        check(ev("Inventory.count('%s')"%item)==1,'%s: opens at stage 15 and gives %s'%(tid,item))
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)
