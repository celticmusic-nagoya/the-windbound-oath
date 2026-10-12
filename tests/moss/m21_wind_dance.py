# Fiona's 風の舞: gate (not usable before the altar event), learned at the first cast, save/load, old-save sync, no double fire, command visibility behind the feature flag.
import os, sys, json
from playwright.sync_api import sync_playwright
PORT=os.environ.get('PORT','8765'); fails=[]; errs=[]
def ck(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    for flag in (False,True):
        pg=b.new_page(viewport={'width':844,'height':390}); ev=pg.evaluate
        pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and '404' not in m.text and errs.append(m.text))
        pg.goto('http://localhost:%s/index.html?dev=1%s'%(PORT,'&feature=windDanceCommand' if flag else '')); pg.wait_for_timeout(1500); ev('closeDialogue()')
        tag='[flag %s] '%('on' if flag else 'off')
        ev("PrologueProgress.seed(3);Inventory.reset();EquipmentManager.reset();localStorage.removeItem(SAVE_KEY);delete PartyManager.members.fiona.learned;giveStarterSword();syncEquipTab()")
        ck(ev("WindDance.learned()")==False and ev("WindDance.commandVisible()")==False,tag+'before the altar event: not learned, no command')
        ck(ev("WindDance.data().effect.amount")is None and ev("WindDance.data().mp")is None,tag+'undecided numbers stay null (no balance change)')
        ev("document.querySelector('#forestScene').style.display='none';startAltarScene()"); A=ev("altarLines"); d=[i for i,l in enumerate(A) if l.startswith('風の舞――')][0]
        for i in range(1,len(A)):
            ev("document.querySelector('#altarScene').click()")
            if i==d-1: ck(ev("WindDance.learned()")==False,tag+'one page before the first cast: still not learned')
            if i==d: ck(ev("WindDance.learned()")==True,tag+'learned on the first-cast page'); break
        toast=ev("document.querySelector('#storyFlag').textContent")
        ck(('風の舞' in toast)==flag,tag+'learn toast only with the feature on (%s)'%toast)
        ev("document.querySelector('#altarScene').style.display='none'")
        ck(ev("WindDance.learn()")==False,tag+'second learn() is a no-op (no double fire)')
        ck(ev("WindDance.commandVisible()")==flag,tag+'command visible only with the feature flag')
        # normal battle: Fiona's command row
        ev("storyStage=15;startTraining&&0")
        ev("(()=>{normalActor='fiona';})()")
        has=ev("!!document.querySelector('#nWindDance')") and ev("!!document.querySelector('#rbWindDance')")
        ck(has,tag+'command buttons exist (hidden by default)')
        # save / load
        ev("renderSystemTab('save');saveGrowthData()"); sv=json.loads(ev("localStorage.getItem(SAVE_KEY)"))
        ck(sv['members']['fiona'].get('learned',{}).get('wind_dance')==True and sv['version']==30,tag+'save keeps it inside members (format v30 unchanged)')
        ev("delete PartyManager.members.fiona.learned;loadGrowthData()"); ck(ev("WindDance.learned()")==True,tag+'load restores the learned state')
        # old save from after the altar event (no learned key): restored by the story stage
        sv['members']['fiona'].pop('learned',None); pg.evaluate("s=>localStorage.setItem(SAVE_KEY,s)",json.dumps(sv))
        ev("delete PartyManager.members.fiona.learned;loadGrowthData()")
        ck(ev("WindDance.learned()")==(ev("storyStage")>=13),tag+'old save: learned iff past the altar stage (stage %s)'%ev("storyStage"))
        # loading an EARLIER save in the same session must not keep the spell
        early=json.loads(json.dumps(sv)); early['members']['fiona'].pop('learned',None); early['prologue']['storyStage']=5
        pg.evaluate("s=>localStorage.setItem(SAVE_KEY,s)",json.dumps(early)); ev("WindDance.learn();loadGrowthData()")
        ck(ev("WindDance.learned()")==False,tag+'loading an earlier save drops a later-learned spell (stage %s)'%ev("storyStage"))
        pg.close()
    b.close()
print('errors',errs[:4]); print('FAILS',len(fails)); sys.exit(1 if (fails or errs) else 0)
