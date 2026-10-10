# M6 ④ FieldTalk: speaker plate, paging, choices, conditions (flag / item / sealOpen / talked / once), effects, save. needs http.server 8765
import sys, json
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
TABLE={"npc":"t_guide","entries":[
 {"id":"t_intro","priority":50,"mode":"once","when":{},"lines":["案内人「はじめまして。」　エイダン「こちらこそ。」"]},
 {"id":"t_charm","priority":40,"mode":"cycle","when":{"item":"charm_windward"},"lines":["案内人「その護符……いい風を連れてくるね。」"]},
 {"id":"t_ask","priority":30,"mode":"cycle","when":{"talked":"t_intro","not":{"flag":"t_helped"}},
  "lines":[{"pages":["案内人「少し手伝ってくれないか？」"],"choice":{"options":[
     {"label":"はい","reply":"案内人「ありがとう！　これを。」","set":{"t_helped":True},"give":{"potion":1}},
     {"label":"いいえ","reply":"案内人「そうか、また今度。」"}]}}]},
 {"id":"t_after","priority":20,"mode":"cycle","when":{"flag":"t_helped"},"lines":["案内人「さっきは助かったよ。」"]},
 {"id":"t_default","priority":1,"when":{},"lines":["案内人「いい天気だね。」"]}]}
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    msgtxt=lambda: pg.evaluate("document.querySelector('#msg').textContent")
    name=lambda: pg.evaluate("(document.querySelector('#msg .talkName')||{}).textContent||''")
    shown=lambda: pg.evaluate("getComputedStyle(document.querySelector('#msg')).display!=='none'")
    pg.evaluate("(t)=>FieldTalk.loadTable(t)",TABLE)
    # speaker plate + paging by speaker
    pg.evaluate("FieldTalk.talk('t_guide')")
    check(name()=='案内人' and '「はじめまして。」' in msgtxt() and 'エイダン' not in msgtxt(),'speaker plate shows 案内人; page 1 only: %s'%msgtxt())
    pg.click('#msg'); check(name()=='エイダン' and 'こちらこそ' in msgtxt(),'tap -> page 2 with speaker エイダン')
    pg.click('#msg'); check(not shown(),'tap on last page closes the dialogue')
    # once entry is consumed; next highest matching entry = t_ask (talked t_intro, not helped) with choices
    pg.evaluate("FieldTalk.talk('t_guide')")
    btns=pg.evaluate("[...document.querySelectorAll('#msg .talkChoices button')].map(b=>b.textContent)")
    check(btns==['はい','いいえ'],'choice UI shows はい／いいえ %s'%btns)
    pg.click('#msg') ; check(shown() and len(pg.query_selector_all('#msg .talkChoices button'))==2,'tapping the box does not skip a pending choice')
    po0=pg.evaluate("battleItems.potion")
    pg.click('#msg .talkChoices button[data-choice="0"]')
    check('ありがとう' in msgtxt(),'choosing はい plays the reply: %s'%msgtxt())
    pg.click('#msg'); check('きずぐすり ×1 を手に入れた' in msgtxt() and pg.evaluate("battleItems.potion")==po0+1,'effect give: potion +1 shown as a page')
    pg.click('#msg'); check(not shown(),'closes after reply')
    # flag set by choice -> branch switches
    pg.evaluate("FieldTalk.talk('t_guide')"); check('助かった' in msgtxt(),'flag t_helped switches branch: %s'%msgtxt())
    # item condition (higher priority)
    pg.evaluate("Inventory.add('charm_windward',1)"); pg.evaluate("FieldTalk.talk('t_guide')"); check('護符' in msgtxt(),'item condition (風よけの護符) selects the higher-priority line')
    # keyboard: Enter advances, digits choose
    pg.evaluate("FieldTalk.load(null);Inventory.reset()"); pg.evaluate("FieldTalk.talk('t_guide')"); pg.keyboard.press('Enter'); check(name()=='エイダン','Enter advances a page'); pg.keyboard.press('Enter'); check(not shown(),'Enter closes')
    pg.evaluate("FieldTalk.talk('t_guide')"); check(pg.evaluate("document.querySelectorAll('#msg .talkChoices button').length")==2,'second talk after reset -> choice entry')
    pg.keyboard.press('2'); check('また今度' in msgtxt(),'key 2 selects いいえ'); pg.keyboard.press('Enter')
    check(pg.evaluate("FieldTalk.serialize().flags.t_helped")!=True,'いいえ sets nothing')
    # save / load
    pg.evaluate("FieldTalk.talk('t_guide')"); pg.click('#msg .talkChoices button[data-choice="0"]'); pg.click('#msg'); pg.click('#msg')
    s=pg.evaluate("FieldTalk.serialize()"); check('t_intro' in s['seen'] and s['flags'].get('t_helped'),'serialize carries seen + flags %s'%json.dumps(s)[:100])
    pg.evaluate("(s)=>FieldTalk.load(s)",s); pg.evaluate("FieldTalk.talk('t_guide')"); check('助かった' in msgtxt() and not pg.evaluate("document.querySelector('#msg .talkChoices')"),'restored state: still helped, once-entry not replayed')
    hostile={'seen':['t_intro','evil',5],'cycle':{'t_after':-3,'zz':1,'t_ask':'x'},'flags':{'ok_flag':1,'bad flag!':1}}
    pg.evaluate("(s)=>FieldTalk.load(s)",hostile); r=pg.evaluate("FieldTalk.serialize()")
    check(r['seen']==['t_intro'] and r['cycle']=={} and r['flags']=={'ok_flag':True},'hostile talk save sanitised %s'%json.dumps(r))
    pg.evaluate("FieldTalk.load({})")
    # existing NPCs keep working with a speaker plate (elder, seal branch)
    pg.evaluate("PrologueProgress.seed(0)"); pg.evaluate("FieldTalk.talk('elder')"); check(name()=='長老' and '輝きが弱まっておる' in msgtxt(),'elder closed branch with plate: %s / %s'%(name(),msgtxt()[:20]))
    pg.evaluate("PrologueProgress.seed(3)"); pg.evaluate("FieldTalk.talk('elder')"); check('邪気が晴れ' in msgtxt(),'elder seal-open branch')
    pg.evaluate("PrologueProgress.seed(0)"); pg.evaluate("FieldTalk.talk('emma');FieldTalk.talk('emma')"); pg.evaluate("FieldTalk.talk('emma')")
    check(name()=='フィオナ' and 'エマ' not in msgtxt(),'emma banter starts as フィオナ page'); pg.click('#msg'); check(name()=='エマ','banter continues as エマ page')
    check(pg.evaluate("FieldTalk.talk('nobody')")==False,'unknown NPC returns false and leaves dialogue untouched')
    # real saveGrowthData / loadGrowthData round trip (no DEV sandbox): talk state + inventory ride in the root save
    pg.evaluate("document.querySelector('#menuOpen').click();renderSystemTab('save')")
    pg.evaluate("FieldTalk.load({});FieldTalk.setFlag('t_helped',true);Inventory.add('rune_shard_old',1);document.querySelector('#doSave').click()")
    raw=pg.evaluate("JSON.parse(localStorage.getItem(SAVE_KEY))")
    check(raw['version']==30 and raw['talk']['flags'].get('t_helped') and raw['inventory']['key'].get('rune_shard_old')==1,'saveGrowthData writes v30 with talk + inventory')
    pg.evaluate("FieldTalk.load({});Inventory.reset();loadGrowthData()")
    check(pg.evaluate("FieldTalk.serialize().flags.t_helped")==True and pg.evaluate("Inventory.count('rune_shard_old')")==1,'loadGrowthData restores talk flags + key items')
    check(not errs,'0 console errors %s'%errs[:2]); b.close()
sys.exit(1 if fails else 0)
