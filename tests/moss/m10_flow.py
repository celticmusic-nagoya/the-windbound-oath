# M10 flow: opening -> Fiona -> real training battle -> stage 3 field unlock -> cliff -> back -> stage 15 ruin roam -> elder opens road. needs http.server 8765
import sys
from playwright.sync_api import sync_playwright
fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500); ev=pg.evaluate
    ev("RildeVillage.startOpening()"); pg.wait_for_timeout(2000); ev("closeDialogue()")
    ev("MossForestStory.enterMap('rilde_village','from_aidan')"); pg.wait_for_timeout(1800)
    ev("RildeVillage.hook({hook:'rilde_fiona'},MossForest)"); pg.wait_for_timeout(300); ev("closeDialogue()")
    ev("RildeVillage.hook({hook:'rilde_dummy'},MossForest)"); pg.wait_for_timeout(600)
    for i in range(40):
        if ev("storyStage")>=3: break
        pg.evaluate("(()=>{const s=document.getElementById('skill'),a=document.getElementById('atk');(s&&!s.disabled?s:a).click()})()"); pg.wait_for_timeout(900)
    pg.wait_for_timeout(2500)
    check(ev("storyStage")==3,'training won -> stage 3')
    ev("closeDialogue()"); pg.wait_for_timeout(1500)
    # field must be unlocked again after the overlay
    x0=ev("MossForest.feet.x"); ev("MossForest.goFeet(MossForest.feet.x+120,MossForest.feet.y)"); pg.wait_for_timeout(1800)
    check(abs(ev("MossForest.feet.x")-x0)>40,'field movement unlocked after the training battle')
    ev("RildeVillage.exit({id:'tr_v_to_cliff'})"); pg.wait_for_timeout(2500)
    check(ev("MossForest.mapId")=='cliff_moher_01_spiral_ascent','stage 3: south trail -> cliff')
    ev("RildeVillage.exit({id:'tr_c1_to_lind'})"); pg.wait_for_timeout(2500)
    check(ev("MossForest.mapId")=='rilde_village_01_peace','cliff -> back to the peaceful village')
    # after the prologue
    ev("RildeVillage.afterPrologue()"); pg.wait_for_timeout(2500)
    check(ev("storyStage")==15 and ev("MossForest.mapId").startswith('fort_dunvall'),'afterPrologue: stage 15 at the fort')
    ev("RildeVillage.exit({id:'tr_f1_to_village'})"); pg.wait_for_timeout(2500)
    check(ev("MossForest.mapId")=='rilde_village_01_ruin','fort south gate -> ruined village')
    check(ev("FieldBgm.current")=='bgm_rilde_ruin' and ev("FieldWeather.current")=='smoke','ruin bgm + smoke')
    ev("RildeVillage.exit({id:'tr_v_to_fort'})"); pg.wait_for_timeout(500)
    check(ev("MossForest.mapId")=='rilde_village_01_ruin','road closed before the elder')
    ev("FieldTalk.setFlag('road_dunvall_open',true)"); ev("RildeVillage.exit({id:'tr_v_to_fort'})"); pg.wait_for_timeout(2500)
    check(ev("MossForest.mapId").startswith('fort_dunvall'),'road open -> fort')
    ev("RildeVillage.exit({id:'tr_f1_to_village'})"); pg.wait_for_timeout(1500)
    check(ev("MossForest.mapId")=='rilde_village_01_ruin','round trip stays in ruin village')
    errs=[e for e in errs if 'favicon' not in e]
    check(not errs,'no console errors %s'%errs[:3])
# touch regression (Android): taps inside the training ground must walk, and a tap on the dummy must start the training (not the boy's chatter)
    c2=b.new_context(viewport={'width':450,'height':1000},has_touch=True,is_mobile=True,device_scale_factor=2); t=c2.new_page(); tev=t.evaluate
    t.goto('http://localhost:8765/index.html'); t.wait_for_timeout(1500); tev("devJump('training')"); t.wait_for_timeout(2500)
    moved=0
    for wx,wy in ((1960,1040),(1850,770),(2160,780),(1990,1000)):   # free ground away from every talk / training zone
        f=tev("MossForest.feet"); q=tev("(a)=>FieldCamera.worldToScreen(document.getElementById('forestWorld'),a[0],a[1])",[wx,wy]); t.touchscreen.tap(q['x'],q['y']); t.wait_for_timeout(1300); g=tev("MossForest.feet"); moved+= abs(g['x']-f['x'])+abs(g['y']-f['y'])>20
        tev("closeDialogue()")
    check(moved>=3,'taps inside the training ground walk (%d/4)'%moved)
    tev("MossForest.teleportFeet(1877,860)"); t.wait_for_timeout(500)
    old=tev("(()=>{const q=FieldCamera.worldToScreen(document.getElementById('forestWorld'),1902,935);return q})()"); t.touchscreen.tap(old['x'],old['y']); t.wait_for_timeout(800)
    check(tev('storyStage')==1 and tev("getComputedStyle(document.getElementById('battle')).display")!='block','the dummy next to the boy is scenery (no training)'); tev('closeDialogue()')
    q=tev("(()=>{const q=FieldCamera.worldToScreen(document.getElementById('forestWorld'),2075,875);return q})()"); t.touchscreen.tap(q['x'],q['y']); t.wait_for_function("storyStage===2&&getComputedStyle(document.getElementById('battle')).display==='block'&&!LoadingInput.busy",timeout=15000)
    check(tev("storyStage")==2 and tev("getComputedStyle(document.getElementById('battle')).display")=='block','tap on the training dummy opens the training battle')
    check(tev("(()=>{const e=document.elementFromPoint(225,430);return !!(e&&e.closest('#battle'))})()"),'the training battle is actually on top of the field (not hidden behind it)')
    # far tap on an NPC: walk first, talk only on arrival; tapping elsewhere cancels the pending talk
    d=b.new_page(viewport={'width':1280,'height':720}); dv=d.evaluate; d.goto('http://localhost:8765/index.html'); d.wait_for_timeout(1500); dv("devJump('training')"); d.wait_for_timeout(2500); dv("closeDialogue()")
    dv("MossForest.teleportFeet(1877,1100)"); d.wait_for_timeout(500); xy=dv("FieldCamera.worldToScreen(document.getElementById('forestWorld'),1952,940)")
    d.mouse.click(xy['x'],xy['y']); d.wait_for_timeout(150); check(dv("document.getElementById('msg').style.display")!='block','far NPC tap: no instant dialogue')
    d.wait_for_timeout(2500); check(dv("document.getElementById('msg').style.display")=='block','far NPC tap: dialogue after arriving')
    dv("closeDialogue();MossForest.teleportFeet(1877,1100)"); d.wait_for_timeout(300); d.mouse.click(xy['x'],xy['y']); d.wait_for_timeout(200); d.mouse.click(1100,650); d.wait_for_timeout(3000)
    check(dv("document.getElementById('msg').style.display")!='block','tapping elsewhere cancels the pending talk')
print('FAILS',fails); sys.exit(1 if fails else 0)
