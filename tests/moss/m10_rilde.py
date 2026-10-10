# M10 Rilde Village: map data, interior warps, peace/ruin state switch (BGM / weather / time of day), story flow, legacy fallback. needs http.server 8765
import json, glob, os, sys
from playwright.sync_api import sync_playwright
fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
maps={os.path.basename(f)[:-5]:json.load(open(f,encoding='utf-8')) for f in glob.glob('data/maps/rilde_*.json')}
check(len(maps)==14,'14 rilde maps (%d)'%len(maps))
INT=[k for k in maps if k.startswith('rilde_in_')]
for k in INT:
    m=maps[k]; tos=[t for t in m.get('transitions',[])]
    check(len(tos)>=1 and 'default' in m['spawns'],'%s has an exit and a default spawn'%k)
for k in ('rilde_village_01_peace','rilde_village_01_ruin'):
    check(maps[k]['audio']['bgm']['id'] in ('bgm_rilde_day','bgm_rilde_ruin'),k+' names a bgm')
check(set(maps['rilde_village_01_peace']['spawns'])==set(maps['rilde_village_01_ruin']['spawns']),'peace/ruin spawn names identical')
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    ev=pg.evaluate
    check(ev("RildeVillage.enabled()"),'new village enabled by default')
    # opening: Aidan's house
    ev("RildeVillage.startOpening()"); pg.wait_for_timeout(2500)
    check(ev("MossForest.mapId")=='rilde_in_aidan','opening starts in Aidan\'s house')
    check(ev("FieldBgm.current")=='bgm_rilde_home','home bgm indoors (%s)'%ev("FieldBgm.current"))
    ev("closeDialogue()")
    # door warp: indoors -> village (peace)
    ev("MossForestStory.enterMap('rilde_village','from_aidan')"); pg.wait_for_timeout(1800)
    check(ev("MossForest.mapId")=='rilde_village_01_peace','from_aidan resolves to peace village')
    check(ev("FieldBgm.current")=='bgm_rilde_day','day bgm outdoors')
    check(ev("FieldTimeOfDay.current")=='day' if ev("typeof FieldTimeOfDay.current")!='undefined' else True,'peace = daytime')
    # Fiona hold at stage 0
    f=ev("(()=>{const a=MossForest.actor('fiona').get();return [a.x,a.y]})()")
    check(f is not None and abs(f[0]-2030)<260,'Fiona waits at the training ground at stage 0 %s'%(f,))
    ev("closeDialogue()"); ev("RildeVillage.hook({hook:'rilde_fiona'},MossForest)"); pg.wait_for_timeout(400)
    check(ev('storyStage')==1,'talking to Fiona -> stage 1'); ev('closeDialogue()')
    ev("RildeVillage.hook({hook:'rilde_dummy'},MossForest)"); pg.wait_for_timeout(800)
    check(ev('storyStage')==2 and ev("getComputedStyle(document.getElementById('battle')).display")=='block','training dummy opens the training battle (stage 2)')
    ev('storyStage=1'); ev('closeDialogue()')
    # every interior is reachable via enterMap and returns
    for k in INT:
        ev("(a)=>MossForestStory.enterMap(a,'default')",k); pg.wait_for_timeout(700)
        check(ev("MossForest.mapId")==k,'enter '+k)
    # state switch
    ev("storyStage=15"); ev("MossForestStory.enterMap('rilde_village','from_plaza')"); pg.wait_for_timeout(2200)
    check(ev("MossForest.mapId")=='rilde_village_01_ruin','stage 15 -> ruin village')
    check(ev("FieldBgm.current")=='bgm_rilde_ruin','ruin bgm')
    check(ev("FieldWeather.current")=='smoke','smoke weather in ruin (%s)'%ev("FieldWeather.current"))
    check(ev("document.querySelectorAll('#forestVista *').length")>0,'fire layers present')
    # exits in ruin
    ev("RildeVillage.exit({id:'tr_v_to_fort'})"); pg.wait_for_timeout(300)
    check(ev("MossForest.mapId")=='rilde_village_01_ruin','road blocked until elder talks (flag)')
    ev("FieldTalk.setFlag&&FieldTalk.setFlag('road_dunvall_open',true)")
    # back to peace
    ev("storyStage=1"); ev("RildeVillage.force(null)"); ev("MossForestStory.enterMap('rilde_village','from_cliff')"); pg.wait_for_timeout(2000)
    check(ev("MossForest.mapId")=='rilde_village_01_peace','stage 1 -> peace village again')
    # legacy fallback
    pg2=b.new_page(); pg2.on('pageerror',lambda e:errs.append('PAGEERR2 '+str(e)))
    pg2.goto('http://localhost:8765/index.html?legacyVillage=1'); pg2.wait_for_timeout(1200)
    check(not pg2.evaluate("RildeVillage.enabled()"),'?legacyVillage=1 disables the new host')
    pg.wait_for_timeout(300)
errs=[e for e in errs if 'favicon' not in e]
check(not errs,'no console errors %s'%errs[:3])
print('FAILS',fails); sys.exit(1 if fails else 0)
