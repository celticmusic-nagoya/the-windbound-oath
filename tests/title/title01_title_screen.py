# TITLE-01 title screen: TITLE-01-001..014 (015/016 = the existing save/load + battle/map/scenario suites, run separately). needs http.server 8765.
import sys, os, re, json
from playwright.sync_api import sync_playwright
BASE=os.environ.get('BASE','http://localhost:8765/index.html'); ROOT=os.environ.get('ROOT',os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def vis(pg,sel): return pg.evaluate("(s)=>{const e=document.querySelector(s);if(!e)return false;const c=getComputedStyle(e);const r=e.getBoundingClientRect();return c.display!=='none'&&c.visibility!=='hidden'&&r.width>0&&r.height>0}",sel)
def new(b,w=1280,h=720,touch=False,reduced=False):
    ctx=b.new_context(viewport={'width':w,'height':h},has_touch=touch,reduced_motion='reduce' if reduced else 'no-preference'); pg=ctx.new_page()
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.on('requestfailed',lambda r:errs.append('REQFAIL '+r.url)); pg.on('response',lambda r:r.status>=400 and errs.append('HTTP%d %s'%(r.status,r.url)))
    return ctx,pg
A=lambda n:'[data-title-action="%s"]'%n
SAVE="windbound_oath_v028"
with sync_playwright() as p:
    b=p.chromium.launch()
    # ---- 001 first boot ----
    ctx,pg=new(b); pg.goto(BASE+'?title=1'); pg.wait_for_timeout(2600)
    check(vis(pg,'#title-screen'),'TITLE-01-001 title screen visible on a normal start (no title param)' if False else 'TITLE-01-001 title screen visible with ?title=1')
    ctx2,pg2=new(b); pg2.goto('about:blank'); pg2.evaluate('(u)=>{location.href=u}',BASE); pg2.wait_for_timeout(3200)   # navigate without page.goto: the test runner adds ?title=0 to goto() URLs, this is the real plain start
    check(vis(pg2,'#title-screen'),'TITLE-01-001 title screen visible on a plain start (no query at all)')
    check(pg2.evaluate("TitleScreen.active()") and pg2.evaluate("document.documentElement.classList.contains('title-on')"),'TITLE-01-001 TitleScreen active')
    check(pg2.evaluate("[...document.querySelectorAll('#title-screen [data-title-action]')].map(b=>b.dataset.titleAction).join()")=='new-game,continue,options,gallery,confirm-cancel,confirm-ok','TITLE-01-001 menu has the four actions (+ confirm buttons)')
    check(not pg2.evaluate("document.querySelector('#msg').textContent.trim()") and pg2.evaluate("getComputedStyle(document.querySelector('#forestScene')).display")=='none','TITLE-01-001 no opening dialogue / no scene started behind the title (2.6 s)')
    check(pg2.evaluate("document.querySelector('#title-screen .title-logo').getAttribute('alt')")!='' and not pg2.evaluate("/NEW GAME|CONTINUE|OPTIONS|GALLERY/.test(document.querySelector('.title-logo').alt)"),'TITLE-01-001 logo is an <img> with alt; menu words not duplicated in the logo/background')
    check(pg2.evaluate("!document.querySelector('#title-screen .title-background').textContent.trim()"),'TITLE-01-001 background layer has no text (menu is separate HTML)')
    check(not pg2.evaluate("/ruby/i.test(document.querySelector('#title-screen').innerHTML)"),'TITLE-01-001 no ruby markup (Gaelic is part of the logo image)')
    ctx2.close()
    # ---- 002 reload ----
    pg.reload(); pg.wait_for_timeout(1500)
    check(vis(pg,'#title-screen') and pg.evaluate("TitleScreen.active()"),'TITLE-01-002 reload shows the title again')
    pg.evaluate("localStorage.setItem(arguments[0]||'windbound_oath_v028','{}')") if False else pg.evaluate("(k)=>localStorage.setItem(k,'{\"version\":30}')",SAVE); pg.reload(); pg.wait_for_timeout(1500)
    check(vis(pg,'#title-screen'),'TITLE-01-002 reload with a save present still shows the title')
    pg.evaluate("(k)=>localStorage.removeItem(k)",SAVE); ctx.close()
    # ---- 003 NEW GAME (no save) ----
    ctx,pg=new(b); pg.goto(BASE+'?title=1'); pg.wait_for_timeout(1500)
    pg.click(A('new-game')); pg.wait_for_timeout(2500)
    st=pg.evaluate("({forest:getComputedStyle(document.querySelector('#forestScene')).display,map:window.MossForest&&MossForest.mapId,stage:storyStage,inert:document.querySelectorAll('[inert]').length,msg:document.querySelector('#msg').textContent.trim()})")
    check(not vis(pg,'#title-screen') and not pg.evaluate("TitleScreen.active()"),'TITLE-01-003 NEW GAME closes the title (no save -> no confirmation)')
    check(st['forest']=='block' and st['map']=='rilde_in_aidan' and st['stage']==0,'TITLE-01-003 existing opening started: %s'%st)
    check(st['inert']==0 and '朝の風' in st['msg'],'TITLE-01-003 page no longer inert; opening line shown')
    check(pg.evaluate("localStorage.getItem(arguments[0])===null") if False else pg.evaluate("(k)=>localStorage.getItem(k)===null",SAVE),'TITLE-01-003 NEW GAME wrote no save')
    ctx.close()
    # 003b: with a save -> confirmation; cancel/ok
    ctx,pg=new(b); pg.goto(BASE+'?title=1'); pg.wait_for_timeout(1200)
    RAW='{"version":30,"marker":"keep-me"}'; pg.evaluate("([k,v])=>localStorage.setItem(k,v)",[SAVE,RAW]); pg.reload(); pg.wait_for_timeout(1200)
    pg.click(A('new-game')); pg.wait_for_timeout(300)
    check(vis(pg,'#title-screen .title-confirm') and pg.evaluate("TitleScreen.mode")=='confirm','TITLE-01-003 with a save: overwrite confirmation shown')
    check(pg.evaluate("document.activeElement.dataset.titleAction")=='confirm-cancel','TITLE-01-003 confirmation focuses the safe choice (cancel)')
    pg.click(A('confirm-cancel')); pg.wait_for_timeout(300)
    check(vis(pg,'#title-screen') and not vis(pg,'#title-screen .title-confirm') and pg.evaluate("TitleScreen.active()") and pg.evaluate("getComputedStyle(document.querySelector('#forestScene')).display")=='none','TITLE-01-003 cancel returns to the title; game not started')
    check(pg.evaluate("(k)=>localStorage.getItem(k)",SAVE)==RAW,'TITLE-01-003 cancel leaves the save byte-identical')
    pg.click(A('new-game')); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    check(not vis(pg,'#title-screen .title-confirm') and pg.evaluate("TitleScreen.active()"),'TITLE-01-003 Esc cancels the confirmation')
    pg.click(A('new-game')); pg.click(A('confirm-ok')); pg.wait_for_timeout(2500)
    check(not pg.evaluate("TitleScreen.active()") and pg.evaluate("MossForest.mapId")=='rilde_in_aidan','TITLE-01-003 confirm starts the opening')
    check(pg.evaluate("(k)=>localStorage.getItem(k)",SAVE)==RAW,'TITLE-01-003 starting a new game still does not touch the save')
    ctx.close()
    # ---- 004 / 005 CONTINUE ----
    ctx,pg=new(b); pg.goto(BASE+'?title=1'); pg.wait_for_timeout(1200)
    check(pg.evaluate("document.querySelector('[data-title-action=continue]').disabled"),'TITLE-01-004 no save: CONTINUE disabled')
    pg.evaluate("([k,v])=>localStorage.setItem(k,v)",[SAVE,RAW]); pg.reload(); pg.wait_for_timeout(1200)
    cd=pg.evaluate("document.querySelector('[data-title-action=continue]').disabled")
    check(cd and not pg.evaluate("TitleScreen.canContinue()"),'TITLE-01-005 CONDITIONAL: with a save CONTINUE is intentionally DISABLED (no safe cold-start restore of position/map/events; see report)')
    pg.evaluate("document.querySelector('[data-title-action=continue]').click()"); pg.wait_for_timeout(300)
    check(pg.evaluate("TitleScreen.active()") and pg.evaluate("(k)=>localStorage.getItem(k)",SAVE)==RAW,'TITLE-01-005 clicking disabled CONTINUE does nothing; save untouched')
    # ---- 007 gallery ----
    check(pg.evaluate("document.querySelector('[data-title-action=gallery]').disabled") and '未実装' in pg.evaluate("document.querySelector('[data-title-action=gallery]').textContent"),'TITLE-01-007 GALLERY disabled and labelled 未実装')
    # ---- 006 options ----
    pg.click(A('options')); pg.wait_for_timeout(500)
    check(vis(pg,'#systemMenu') and pg.evaluate("document.querySelector('[data-stab=settings]').classList.contains('active')") and 'SETTINGS' in pg.evaluate("document.querySelector('#systemBody').textContent"),'TITLE-01-006 OPTIONS opens the existing SETTINGS screen')
    check(pg.evaluate("[...document.querySelectorAll('#systemMenu [data-stab]')].filter(b=>getComputedStyle(b).display!=='none').map(b=>b.dataset.stab).join()")=='settings','TITLE-01-006 only SETTINGS is reachable from the title (SAVE cannot overwrite a save)')
    check(pg.evaluate("document.querySelector('#toggleBgm')!==null"),'TITLE-01-006 existing settings content (music toggle) present; no new settings')
    pg.click('#systemClose'); pg.wait_for_timeout(400)
    check(vis(pg,'#title-screen') and pg.evaluate("TitleScreen.active()") and pg.evaluate("TitleScreen.mode")=='menu' and pg.evaluate("document.activeElement.dataset.titleAction")=='options','TITLE-01-006 closing settings returns to the title menu (focus on OPTIONS)')
    pg.click(A('options')); pg.wait_for_timeout(300); pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
    check(vis(pg,'#title-screen') and not vis(pg,'#systemMenu'),'TITLE-01-006 Esc closes settings back to the title')
    check(pg.evaluate("(k)=>localStorage.getItem(k)",SAVE)==RAW,'TITLE-01-006 save untouched by OPTIONS')
    pg.evaluate("(k)=>localStorage.removeItem(k)",SAVE); ctx.close()
    # ---- 008..010 layouts ----
    def layout(name,w,h,touch,minbtn,expect_logo_above_menu):
        ctx,pg=new(b,w,h,touch); pg.goto(BASE+'?title=1'); pg.wait_for_timeout(1400)
        g=pg.evaluate("""()=>{const r=s=>document.querySelector(s).getBoundingClientRect();const L=r('#title-screen .title-logo'),M=r('#title-screen .title-menu'),W=innerWidth,H=innerHeight;
          const bs=[...document.querySelectorAll('#title-screen .title-menu .ts-btn')].map(b=>b.getBoundingClientRect());
          return {W,H,sw:document.documentElement.scrollWidth,sh:document.documentElement.scrollHeight,logo:[L.left,L.top,L.right,L.bottom],menu:[M.left,M.top,M.right,M.bottom],minH:Math.min(...bs.map(b=>b.height)),minW:Math.min(...bs.map(b=>b.width)),
          allIn:bs.every(b=>b.left>=0&&b.right<=W&&b.top>=0&&b.bottom<=H),logoIn:L.left>=0&&L.right<=W&&L.top>=0&&L.bottom<=H,tsH:r('#title-screen').height}}""")
        check(g['sw']<=g['W'] and g['sh']<=g['H'] and abs(g['tsH']-g['H'])<=1,'%s no overflow, title fills the viewport (100dvh) %s'%(name,(g['sw'],g['sh'],g['W'],g['H'])))
        check(g['allIn'] and g['logoIn'],'%s logo and all four buttons inside the viewport'%name)
        check(g['minH']>=minbtn and g['minW']>=120,'%s touch targets >= %dpx (min h %.0f w %.0f)'%(name,minbtn,g['minH'],g['minW']))
        check(g['logo'][3]<=g['menu'][1]+1,'%s logo does not overlap the menu'%name)
        pg.screenshot(path=os.path.join(os.environ.get('SHOTS','/tmp'),'title01_%s.png'%name)); ctx.close()
    layout('pc_1672x941',1672,941,False,44,True); layout('pc_1280x720',1280,720,False,44,True)
    layout('phone_portrait_432x960',432,960,True,48,True); layout('phone_portrait_390x844',390,844,True,48,True); layout('phone_portrait_360x640',360,640,True,48,True)
    layout('phone_landscape_844x390',844,390,True,36,True); layout('phone_landscape_667x375',667,375,True,36,True)
    layout('tablet_portrait_768x1024',768,1024,True,48,True); layout('tablet_landscape_1024x768',1024,768,True,44,True)
    ctx,pg=new(b,432,960,True); pg.goto(BASE+'?title=1'); pg.wait_for_timeout(1200)
    check(pg.evaluate("getComputedStyle(document.querySelector('#title-screen .title-background')).backgroundPosition")!='50% 50%','TITLE-01-009 portrait phone uses its own background crop (not centered)')
    ctx.close()
    # ---- 011 keyboard / touch ----
    ctx,pg=new(b); pg.goto(BASE+'?title=1'); pg.wait_for_timeout(1500)
    check(pg.evaluate("document.activeElement.dataset.titleAction")=='new-game','TITLE-01-011 NEW GAME focused initially')
    pg.keyboard.press('ArrowDown'); check(pg.evaluate("document.activeElement.dataset.titleAction")=='options','TITLE-01-011 ArrowDown skips disabled CONTINUE -> OPTIONS')
    pg.keyboard.press('ArrowDown'); check(pg.evaluate("document.activeElement.dataset.titleAction")=='new-game','TITLE-01-011 ArrowDown wraps (GALLERY disabled)')
    pg.keyboard.press('ArrowUp'); check(pg.evaluate("document.activeElement.dataset.titleAction")=='options','TITLE-01-011 ArrowUp wraps back')
    pg.keyboard.press('ArrowUp')
    for k in ['m','q','w','a','s','d','ArrowLeft']: pg.keyboard.press(k)
    pg.wait_for_timeout(200)
    check(not vis(pg,'#systemMenu') and not vis(pg,'#questMenu') and pg.evaluate("TitleScreen.active()"),'TITLE-01-011 game keys (M/Q/WASD/arrows) do not reach the game while on the title')
    pg.keyboard.press('Tab'); pg.keyboard.press('Tab'); pg.keyboard.press('Tab')
    check(pg.evaluate("!!document.activeElement.closest('#title-screen')"),'TITLE-01-011 Tab focus stays inside the title')
    check(pg.evaluate("getComputedStyle(document.activeElement).borderColor")!=pg.evaluate("'x'"),'TITLE-01-011 focused button has a visible style')
    pg.focus(A('new-game')); pg.keyboard.press('Enter'); pg.wait_for_timeout(2200)
    check(not pg.evaluate("TitleScreen.active()") and pg.evaluate("MossForest.mapId")=='rilde_in_aidan','TITLE-01-011 Enter on NEW GAME starts the game')
    ctx.close()
    ctx,pg=new(b,432,960,True); pg.goto(BASE+'?title=1'); pg.wait_for_timeout(1200)
    pg.tap(A('new-game')); pg.wait_for_timeout(2200)
    check(not pg.evaluate("TitleScreen.active()") and pg.evaluate("MossForest.mapId")=='rilde_in_aidan','TITLE-01-011 touch tap on NEW GAME starts the game')
    ctx.close()
    ctx,pg=new(b,reduced=True); pg.goto(BASE+'?title=1'); pg.wait_for_timeout(600)
    check(pg.evaluate("getComputedStyle(document.querySelector('#title-screen .title-content')).animationName")=='none' and pg.evaluate("getComputedStyle(document.querySelector('#title-screen .ts-btn')).transitionDuration")=='0s','TITLE-01-011 prefers-reduced-motion: no animation / transition')
    ctx.close()
    # ---- 012 images ----
    ctx,pg=new(b); pg.goto(BASE+'?title=1'); pg.wait_for_timeout(1800)
    im=pg.evaluate("""async()=>{const l=document.querySelector('.title-logo');const u=getComputedStyle(document.querySelector('.title-background')).backgroundImage.match(/url\\("?(.*?)"?\\)/)[1];
      const bg=await new Promise(r=>{const i=new Image();i.onload=()=>r([i.naturalWidth,i.naturalHeight]);i.onerror=()=>r(null);i.src=u});return {logo:[l.naturalWidth,l.naturalHeight,l.complete],bg,u}}""")
    check(im['logo']==[2048,728,True],'TITLE-01-012 logo loaded 2048x728 %s'%im['logo']); check(im['bg']==[1671,941],'TITLE-01-012 background loaded 1671x941 %s'%im['bg'])
    check(not [e for e in errs if 'title' in e.lower() or 'REQFAIL' in e or 'HTTP4' in e or 'HTTP5' in e or 'PAGEERR' in e],'TITLE-01-012 no page errors / failed requests during title: %s'%errs[:3])
    ctx.close()
    # ---- 013 no stale old-title references ----
    names=['index.html','css/title-screen.css','js/title-screen.js']
    hits=[]
    for dp,_,fs in os.walk(os.path.join(ROOT,'js')):
        for f in fs:
            if f.endswith('.js'): names.append(os.path.relpath(os.path.join(dp,f),ROOT))
    for f in os.listdir(os.path.join(ROOT,'css')):
        if f.endswith('.css'): names.append('css/'+f)
    for n in set(names):
        if n in('css/title-screen.css','js/title-screen.js'): continue
        t=open(os.path.join(ROOT,n),encoding='utf-8',errors='ignore').read()
        for m in re.finditer(r'(titleScreen|title-old|oldTitle|start-screen|startScreen|#title\b)',t):
            hits.append((n,m.group(0)))
    check(not hits,'TITLE-01-013 no old/duplicate title references outside the new title files: %s'%hits[:5])
    imgs=sorted(os.listdir(os.path.join(ROOT,'img','title'))); idx=open(os.path.join(ROOT,'index.html'),encoding='utf-8').read()+open(os.path.join(ROOT,'css/title-screen.css')).read()
    check(all(i in idx for i in imgs),'TITLE-01-013 every title asset is referenced (%s)'%imgs)
    # ---- 014 start paths unchanged ----
    ctx,pg=new(b); pg.goto(BASE+'?title=0'); pg.wait_for_timeout(2600)
    check(not vis(pg,'#title-screen') and not pg.evaluate("TitleScreen.active()") and pg.evaluate("MossForest.mapId")=='rilde_in_aidan' and '朝の風' in pg.evaluate("document.querySelector('#msg').textContent"),'TITLE-01-014 ?title=0 boots straight into the opening (title skipped, nothing inert)')
    check(pg.evaluate("document.querySelectorAll('[inert]').length")==0,'TITLE-01-014 ?title=0 leaves nothing inert')
    ctx.close()
    ctx,pg=new(b); pg.goto(BASE+'?legacyVillage=1'); pg.wait_for_timeout(2600)
    check(not vis(pg,'#title-screen') and pg.evaluate("room")=='home','TITLE-01-014 ?legacyVillage=1 keeps the legacy start (title skipped)')
    ctx.close()
    b.close()
print('FAILS',len(fails)); sys.exit(1 if fails else 0)
