# M6 ③ inventory: key items from chests, 大事なもの tab, v30 save, legacy (M5.5-era) save reconciliation. needs http.server 8765
import sys, json
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(500)
    # A1 hollow via real click path
    t=pg.evaluate("MossForest.map.treasurePoints.find(t=>t.id==='tr_a1_hollow')")
    pg.evaluate("MossForest.teleportFeet(%d,%d)"%(t['x'],t['y']+30)); pg.wait_for_timeout(200); pg.evaluate("MossForest.goFeet(%d,%d)"%(t['x'],t['y']+8)); pg.wait_for_timeout(2500)
    n=pg.query_selector('.forest-treasure'); bx=n.bounding_box(); pg.mouse.click(bx['x']+bx['width']/2,bx['y']+bx['height']/2); pg.wait_for_timeout(600)
    check(pg.evaluate("battleItems.potion")==6,'consumable chest still grants (potion 4 -> 6)')
    # key-item chests through the same hook the runtime uses
    r=pg.evaluate("(()=>{const got=Inventory.openTreasure('tr_a2_overlook');return [Inventory.describe(got),Inventory.count('charm_windward'),Inventory.count('ether')]})()")
    check(r[1]==1 and '風よけの護符' in r[0] and r[2]==3,'overlook chest -> 護符 x1 (+ ether) %s'%r)
    check(pg.evaluate("Inventory.openTreasure('tr_a2_overlook').length")==0 and pg.evaluate("Inventory.count('charm_windward')")==1,'second open grants nothing')
    pg.evaluate("Inventory.openTreasure('tr_a3_shrine')"); check(pg.evaluate("Inventory.count('rune_shard_old')")==1,'shrine chest -> 古びたルーン片')
    # ITEMS tab
    pg.evaluate("document.querySelector('#menuOpen').click()"); pg.evaluate("renderSystemTab('items')")
    body=pg.evaluate("document.querySelector('#systemBody').textContent")
    check('大事なもの' in body and '風よけの護符' in body and '古びたルーン片' in body and 'きずぐすり' in body,'ITEMS tab lists consumables and 大事なもの')
    # save payload + roundtrip
    payload=pg.evaluate("(()=>{return {version:30,inventory:Inventory.serialize(),prologue:PrologueProgress.serialize(),members:PartyManager.members,active:PartyManager.active,reserve:PartyManager.reserve,squads:PartyManager.squads,support:PartyManager.support,gold,battleItems}})()")
    check(payload['inventory']['key'].get('charm_windward')==1 and 'tr_a2_overlook' in payload['inventory']['claimed'],'save v30 carries key items + claimed %s'%json.dumps(payload['inventory'])[:90])
    def load(d):
        pg.evaluate("(d)=>{localStorage.setItem(SAVE_KEY,JSON.stringify(d));Inventory.reset();return loadGrowthData()}",d)
        pg.wait_for_function("MossForest.busy===false",timeout=20000); pg.wait_for_timeout(500)
        return pg.evaluate("({ch:Inventory.count('charm_windward'),ru:Inventory.count('rune_shard_old'),po:battleItems.potion,et:battleItems.ether})")
    r=load(payload); check(r['ch']==1 and r['ru']==1,'v30 save restores key items (no double grant) %s'%r)
    # legacy M5.5 save: opened the two chests, no inventory block
    legacy=json.loads(json.dumps(payload)); del legacy['inventory']; legacy['version']=29
    legacy['prologue']['moss']['opened']=['tr_a1_hollow','tr_a2_overlook','tr_a3_shrine']; legacy['battleItems']={'potion':9,'ether':5}
    r=load(legacy); check(r['ch']==1 and r['ru']==1,'legacy v29 save: 大事なもの granted once for already-opened chests %s'%r)
    check(r['po']==9 and r['et']==5,'legacy補正 does not touch consumables (potion %s, ether %s)'%(r['po'],r['et']))
    r2=pg.evaluate("(()=>{const s=Inventory.serialize();Inventory.reconcile(['tr_a2_overlook','tr_a3_shrine']);return [Inventory.count('charm_windward'),s.claimed.length]})()")
    check(r2[0]==1,'reconcile is idempotent')
    # legacy v29 with no chests opened -> nothing
    legacy2=json.loads(json.dumps(legacy)); legacy2['prologue']['moss']['opened']=[]
    r=load(legacy2); check(r['ch']==0 and r['ru']==0,'legacy save without opened chests gets nothing %s'%r)
    # hostile inventory block
    bad=json.loads(json.dumps(payload)); bad['inventory']={'key':{'charm_windward':-5,'evil':3,'rune_shard_old':'x'},'claimed':[1,'nope']}
    r=load(bad); check(r['ch']==0 and r['ru']==0,'hostile inventory block is sanitised')
    check(not errs,'0 console errors %s'%errs[:2]); b.close()
sys.exit(1 if fails else 0)
