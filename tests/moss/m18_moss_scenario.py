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
    A=ev("altarLines");ck(len(A)==32,'altar has 32 lines (%d)'%len(A))
    oi=[i for i,l in enumerate(A) if l=='エイダン「……もう、目の前で誰かを失うのは嫌だ。」']
    ck(oi==[26],'oath line unchanged, index 26 (%s)'%oi)
    ck(A[24].startswith('夕日の丘') and A[25]=='エイダン「……強くなりたいなんて言って、村のみんなを守れなかった。」','recall + Aidan line directly before the oath')
    bi=[i for i,l in enumerate(A) if '刀身が折れた' in l]
    ck(bi==[13] and A[11].startswith('小鬼たちの奥から、地面を震わせる角笛') and A[16].startswith('追撃の斧') and A[17].startswith('フィオナ「風よ、お願い'),'order: Raider appears -> father sword breaks (13) -> Lou/Fiona stall (16-17) -> stone reacts')
    sw=None;glow=None;wk=[]
    for i in range(1,len(A)):
        ev("document.querySelector('#altarScene').click()")
        sword=ev("getComputedStyle(document.querySelector('#oathSword')).display")
        op=ev("document.querySelector('#ag1').style.opacity")
        wk.append((i,ev("EquipmentManager.get('aidan').weapon")))
        if sw is None and sword!='none': sw=i
        if glow is None and op=='0.28': glow=i
        if i==27: break
    ck(sw==20,'sword appears on line 20 (%s)'%sw)
    ck(glow==27 and A[27].startswith('エイダンが柄を握る'),'grip/glow fires on the grip line (index %s)'%glow)
    ck(all(w=='father_sword' for i,w in wk if i<27) and wk[-1][1]=='oath_sword','weapon: father sword until the contract line, then the oath sword')
    print(errs[:4])
print('FAILS',len(fails))
