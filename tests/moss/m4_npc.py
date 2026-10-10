# Elder / Emma warning lines (peaceful vs seal-open branch). needs http.server 8765.
import sys
from playwright.sync_api import sync_playwright
errs=[];fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    # elder house interior (peaceful stage)
    pg.evaluate("storyStage=1;room='elder';ipx=485;ipy=330;document.querySelector('#inside').style.display='block';dressRoom();inCamera()"); pg.wait_for_timeout(200)
    check(pg.evaluate("!!document.querySelector('#elderNpc')"),'elder NPC exists in 長老の家')
    pg.evaluate("document.querySelector('#elderNpc').click()"); pg.wait_for_timeout(100)
    t=pg.evaluate("document.querySelector('#msg').textContent"); check('輝きが弱まっておる' in t,'elder closed line 1: '+t)
    pg.evaluate("document.querySelector('#elderNpc').click()"); t=pg.evaluate("document.querySelector('#msg').textContent"); check('近付くでないぞ' in t,'elder closed line 2 (cycles)')
    # Emma (review-mode interaction event)
    pg.evaluate("window.dispatchEvent(new CustomEvent('lind-field-interaction',{detail:{id:'emma',type:'field_npc'}}))")
    t=pg.evaluate("document.querySelector('#msg').textContent"); check('背負い込んで' in t,'emma closed line: '+t)
    # seal-open branch
    pg.evaluate("PrologueProgress.seed(3)"); 
    pg.evaluate("document.querySelector('#elderNpc').click()"); t=pg.evaluate("document.querySelector('#msg').textContent"); check('邪気が晴れ' in t,'elder open line: '+t)
    pg.evaluate("FieldTalk.load(null)")   # draft quest offer (talk-data-quests.js) outranks the plain lines once she has been heard
    pg.evaluate("window.dispatchEvent(new CustomEvent('lind-field-interaction',{detail:{id:'emma'}}))")
    t=pg.evaluate("document.querySelector('#msg').textContent"); check('風がようやく' in t,'emma open line')
    pg.evaluate("window.dispatchEvent(new CustomEvent('lind-field-interaction',{detail:{id:'elder_man'}}))")
    check(pg.evaluate("document.querySelector('#msg').textContent")==t,'other NPC ids ignored')
    # village NPC lines (children / prayer / well / hill)
    pg.evaluate("PrologueProgress.seed(0)")
    def talk(i): pg.evaluate("(i)=>window.dispatchEvent(new CustomEvent('lind-field-interaction',{detail:{id:i}}))",i); return pg.evaluate("document.querySelector('#msg').textContent")
    check('風みたいに速い' in talk('boy'),'child A (boy)'); check('木彫りの剣' in talk('boy'),'child C (boy, 2nd)')
    check('エイダンお兄ちゃん、助けて' in talk('girl'),'child B (girl)'); check('道に迷いそう' in talk('girl'),'child D (girl, 2nd)')
    check('邪魔してごめん' in talk('young_woman'),'praying villager'); check('シチュー' in talk('elder_woman'),'well villager')
    pg.evaluate("document.querySelector('#hillOld').click()"); h1=pg.evaluate("document.querySelector('#msg').textContent")
    pg.evaluate("document.querySelector('#hillOld').click()"); h2=pg.evaluate("document.querySelector('#msg').textContent")
    check('風がよく通る' in h1 and 'お母さん譲り' in h2,'hill villager 2 lines')
    check(talk('elder_man')==pg.evaluate("document.querySelector('#msg').textContent") ,'NPC without text leaves dialogue untouched')
    for i,k in [('farmer_male','いい風が吹いている'),('caretaker','牛たち'),('young_man','木人'),('innkeeper','シチュー'),('inn_traveler','静かでいい所'),('merchant','傷薬'),('fisherman','邪魔するな')]:
        check(k in talk(i),'village line: '+i)
    # interiors: shop keeper / innkeeper / traveler through the real room UI
    pg.evaluate("room='shop';ipx=499;ipy=325;document.querySelector('#inside').style.display='block';dressRoom();inCamera()"); pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#shopKeeper').click()"); check('傷薬は多め' in pg.evaluate("document.querySelector('#msg').textContent"),'shop keeper (room UI)')
    pg.evaluate("room='inn';dressRoom();ipx=300;ipy=330;inCamera()"); pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#innKeeper').click()"); check('シチュー' in pg.evaluate("document.querySelector('#msg').textContent") or '近づいて' in pg.evaluate("document.querySelector('#msg').textContent"),'innkeeper click handled')
    check(pg.evaluate("!!document.querySelector('#innTraveler')"),'inn traveler exists')
    print('errors',errs[:5]); b.close()
sys.exit(1 if (fails or errs) else 0)
