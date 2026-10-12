# DEV モンスター配置アリーナ + 各マップのモンスター数(3倍)・古樹の聖域への追加
import os, math
from playwright.sync_api import sync_playwright
PORT=os.environ.get('PORT','8765'); fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
MAPS={'moss_forest_01_sunlit_path':{'moss_slime':6,'leafy_boar':6,'goblin':6},
      'moss_forest_02_mossy_ravine':{'moss_slime':6,'leafy_boar':6,'forest_bat':6,'goblin':6},
      'moss_forest_03_ancient_grove':{'moss_slime':3,'forest_bat':3,'leafy_boar':3},
      'road_dunvall_capital_01':{'leafy_boar':6}}
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:%s/index.html?dev=1'%PORT); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=15;enterMossForest()"); pg.wait_for_timeout(2500)
    for mp,want in MAPS.items():
        ev("MossForest.enter({map:'%s'})"%mp); pg.wait_for_timeout(1800)
        L=ev("MossForest.monsters.map(m=>({t:m.type,x:m.x,y:m.y,b:MossForest.blocked(m.x,m.y)}))")
        c={}
        for m in L: c[m['t']]=c.get(m['t'],0)+1
        gap=min(math.hypot(a['x']-q['x'],a['y']-q['y']) for i,a in enumerate(L) for q in L[i+1:])
        check(c==want and not any(m['b'] for m in L),'%s: %s, none blocked'%(mp,c))
        check(gap>=450,'%s: monsters are spread out (closest pair %.0f px)'%(mp,gap))
        if mp.endswith('ancient_grove'):
            sy=ev("MossForest.map.story.prologue.symbols.map(s=>[s.x,s.y])")
            check(all(math.hypot(m['x']-s[0],m['y']-s[1])>600 for m in L for s in sy),'A3 monsters keep clear of the story goblin symbols')
            check(ev("MossForest.symbolsAlive")==3,'A3 story goblin symbols still 3')
    # ---- DEV panel
    check(ev("!!document.querySelector('#devArena')") and ev("!!document.querySelector('[data-jump=\"map:dev_monster_arena\"]')"),'DEV panel has the Monster Arena section and a jump entry')
    ev("document.querySelector('#devPanel').style.display='block'")
    pg.click("#devArena [data-arena=go]"); pg.wait_for_timeout(2500)
    check(ev("MossForest.map.id")=='dev_monster_arena' and ev("MossForest.monsters.length")==0,'arena map loads empty')
    ev("document.querySelector('#devPanel').style.display='block'")
    pg.select_option('#devMonType','moss_slime'); pg.select_option('#devMonCount','6'); pg.click("#devArena [data-arena=place]"); pg.wait_for_timeout(500)
    f=ev("MossForest.feet"); L=ev("MossForest.monsters.map(m=>[m.type,m.x,m.y,MossForest.blocked(m.x,m.y)])")
    check(len(L)==6 and all(m[0]=='moss_slime' and not m[3] for m in L),'placed 6 slimes on free ground')
    check(all(150<math.hypot(m[1]-f['x'],m[2]-f['y'])<900 for m in L),'placed around the player')
    pg.click("#devArena [data-arena=all]"); pg.wait_for_timeout(300)
    check(sorted(set(m['type'] for m in ev("MossForest.monsters")))==sorted(['moss_slime','forest_bat','leafy_boar','goblin']) and ev("MossForest.monsters.length")==10,'"all types" adds one of each (10 total)')
    pg.click("#devArena [data-arena=clear]"); pg.wait_for_timeout(300)
    check(ev("MossForest.monsters.length")==0 and ev("document.querySelectorAll('.forest-monster').length")==0,'clear removes them (and their elements)')
    # ---- freeze + contact + group
    ev("(()=>{window.__starts=[];const _s=startAttackBattle;window.startAttackBattle=function(id){window.__starts.push(id);return _s.apply(this,arguments)};return 1})()")
    pg.select_option('#devMonType','forest_bat'); pg.select_option('#devMonCount','1'); pg.select_option('#devMonGroup','2')
    pg.click("#devArena [data-arena=place]"); pg.click("#devArena [data-arena=freeze]"); pg.wait_for_timeout(300)
    check(ev("FieldMonsters.frozen") and 'ON' in pg.inner_text("#devArena [data-arena=freeze]"),'AI freeze toggles on')
    m=ev("(()=>{const m=MossForest.monsters[0];return [m.x,m.y]})()")
    ev("document.querySelector('#devPanel').style.display='none'")
    ev("MossForest.teleportFeet(%d,%d)"%(m[0]+10,m[1]+30)); pg.wait_for_timeout(1800)
    check(ev("window.__starts.length")==0 and ev("MossForest.monsters[0].state")=='wander','frozen monster neither aggroes nor fights')
    ev("document.querySelector('#devPanel').style.display='block'"); pg.click("#devArena [data-arena=freeze]"); pg.wait_for_timeout(200)
    ev("document.querySelector('#devPanel').style.display='none'")
    check(not ev("FieldMonsters.frozen"),'freeze toggles off')
    ev("MossForest.teleportFeet(%d,%d)"%(m[0]+10,m[1]+30)); pg.wait_for_timeout(2500)
    check(ev("window.__starts")==['mossSlime2'] or ev("window.__starts")==['forestBat2'],'contact starts a battle with the chosen group size %s'%ev("window.__starts"))
    check(not errs,'no page errors %s'%errs[:3])
    b.close()
print('FAILS:',fails); raise SystemExit(1 if fails else 0)
