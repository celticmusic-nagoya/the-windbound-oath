# Moss Forest prologue scenario (escape cues, arrival conversation, stage-9 journal, A1 village exit, altar cues). needs python3 -m http.server 8765
from playwright.sync_api import sync_playwright
fails=[];errs=[]
def ck(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html?dev=1');pg.wait_for_timeout(2500);pg.evaluate('closeDialogue()')
    ev=pg.evaluate
    # ---- escape scene: lines + timing
    ev("storyStage=8;startEscapeScene()")
    L=ev("escapeLinesNow()");ck(len(L)==10,'escape has 10 lines')
    gob=[];flash=[];tx=[]
    for i in range(len(L)):
        tx.append(ev("document.querySelector('#escapeText').textContent"))
        gob.append(ev("getComputedStyle(document.querySelector('#escapeGob')).display"))
        ev("document.querySelector('#escapeScene').style.filter='none'")
        if i<len(L)-1:
            ev("document.querySelector('#escapeScene').click()")
            flash.append(ev("document.querySelector('#escapeScene').style.filter"))
    print(tx[4],'|',tx[7])
    ck(gob[3]=='none' and gob[4]=='grid','escape goblin appears on line 5 (角笛), not before (%s)'%gob[:6])
    ck('角笛' in tx[4],'line index 4 is the horn line')
    ck('崖の縁が崩れた' in tx[7],'line index 7 is the cliff-collapse line')
    # flash: after the click that lands on index 7, filter = brightness
    ck(flash[6].startswith('brightness') and not any(f.startswith('brightness') for f in flash[:6]),'dark flash fires exactly on the collapse line (%s)'%[f[:12] for f in flash])
    ev("document.querySelector('#escapeScene').click()")   # last -> forest
    pg.wait_for_timeout(3500)
    ck(ev("storyStage")==9 and ev("MossForest.mapId")=='moss_forest_01_sunlit_path','after escape: stage 9 in A1')
    # ---- arrival conversation: 10 pages in order
    pages=[]
    for i in range(10):
        t=ev("document.querySelector('#msg')&&document.querySelector('#msg').style.display!=='none'?document.querySelector('#msg').textContent:null")
        pages.append(t)
        if t is None:break
        ev("FieldTalk.advance?FieldTalk.advance():document.querySelector('#msg').click()")
        pg.wait_for_timeout(120)
    print(pages)
    ck(all(pages) and len(pages)==10,'arrival conversation shows 10 pages')
    ck('冷たい土' in (pages[0] or '') and '手がかりも調べよう' in (pages[9] or ''),'arrival first/last page')
    pg.wait_for_timeout(300)
    ck(ev("document.querySelector('#msg').style.display")=='none','dialogue closes after the last page (%s)'%ev("document.querySelector('#msg').style.display"))
    # ---- journal
    ev("renderJournal()");j=ev("document.querySelector('#journalMain').textContent")
    ck('異常化ゴブリン3体を討伐して結界を解き' in j and '討伐する' in j and '0 / 3' in j,'journal stage 9 text + objective 0/3 ('+j[:30]+')')
    # ---- A1 village-side exit by REAL movement
    ev("closeDialogue()");ev("MossForest.teleportFeet(1400,5800)");pg.wait_for_timeout(300)
    ev("MossForest.goFeet(1400,5985)")
    seen=[]
    for i in range(40):
        pg.wait_for_timeout(100)
        s=ev("[document.querySelector('#forestToast').textContent,document.querySelector('#forestToast').style.display,MossForest.mapId,Math.round(MossForest.feet.y),String(MossForest.status&&MossForest.status.outcome)]")
        if not seen or seen[-1]!=s: seen.append(s)
    print('exit walk:',seen)
    ck(any('崖の上へ戻る道は、もうない' in (s[0] or '') for s in seen) and seen[-1][2]=='moss_forest_01_sunlit_path','A1 village-side exit: message shown, map unchanged')
    # ---- altar
    ev("closeDialogue();document.querySelector('#forestScene').style.display='none'")
    ev("startAltarScene()")
    A=ev("altarLines");ck(len(A)==37,'altar has 37 pages (%d)'%len(A))
    at=lambda k:[i for i,l in enumerate(A) if l.startswith(k)]
    oi=[i for i,l in enumerate(A) if l=='エイダン「……もう、目の前で誰かを失うのは嫌だ。」']
    ck(len(oi)==1,'oath line present once and unchanged (%s)'%oi)
    grip=at('エイダンが柄を握る'); brk=at('だが次の瞬間、乾いた音とともに'); dance=at('風の舞――'); horn=at('森の奥から、地面を震わせる角笛'); lou=at('ルー「今だよ！'); stone=at('古代石の表面を'); parry=at('エイダンは父の剣で奇襲')
    ck(horn and parry and brk and dance and lou and stone and grip and horn[0]<parry[0]<brk[0]<dance[0]<lou[0]<stone[0]<oi[0]<grip[0],'order: Raider -> parry -> sword breaks -> Fiona wind dance -> Lou -> stone -> oath -> contract')
    ck(grip[0]==oi[0]+1,'the contract comes right after the oath line')
    ck(all(len(l)<=62 for l in A),'every page is short enough (max %d chars)'%max(len(l) for l in A))
    ck(not any('裂け目' in l or '落ちて' in l for l in A),'old "sword falls into the rift" beat is gone')
    sw=None;glow=None;wk=[];ld=[]
    for i in range(1,len(A)):
        ev("document.querySelector('#altarScene').click()")
        sword=ev("getComputedStyle(document.querySelector('#oathSword')).display")
        op=ev("document.querySelector('#ag1').style.opacity")
        wk.append((i,ev("EquipmentManager.get('aidan').weapon"))); ld.append((i,ev("WindDance.learned()")))
        if sw is None and sword!='none': sw=i
        if glow is None and op=='0.28': glow=i
        if i==grip[0]: break
    ck(sw==at('――風が集まり')[0],'sword appears on its line (%s)'%sw)
    ck(glow==grip[0],'grip/glow fires on the grip line (index %s)'%glow)
    ck(all(w=='father_sword' for i,w in wk if i<brk[0]) and all(w is None for i,w in wk if brk[0]<=i<grip[0]) and wk[-1][1]=='oath_sword','weapon: father sword -> broken (empty) -> oath sword at the contract')
    ck(all((not l) for i,l in ld if i<dance[0]) and all(l for i,l in ld if i>=dance[0]),'Fiona learns the wind dance exactly on its first cast line')
    print(errs[:4])
print('FAILS',len(fails))
