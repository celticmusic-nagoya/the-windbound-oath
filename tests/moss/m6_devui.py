# DEV review panel: no stray text, folds to a thin bar on phones, conversations visible in review. needs http.server 8765
import sys
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    for name,vp,mob in [('phone portrait',{'width':390,'height':780},True),('phone landscape',{'width':780,'height':390},True),('desktop',{'width':1280,'height':720},False)]:
        pg=b.new_page(viewport=vp,has_touch=mob,is_mobile=mob)
        pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
        pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(900)
        stray=pg.evaluate("[...document.body.childNodes].filter(n=>n.nodeType===3&&n.textContent.trim()).map(n=>n.textContent.trim())")
        check(stray==[],'%s: no stray text nodes in <body> %s'%(name,stray))
        pg.evaluate("devJump('training')"); pg.wait_for_timeout(300); pg.evaluate("LindFieldReview.open()"); pg.wait_for_timeout(700)
        h=lambda: pg.evaluate("Math.round(document.querySelector('#lindReviewControls').getBoundingClientRect().height)")
        if mob: check(h()<=60,'%s: panel starts folded (%dpx)'%(name,h()))
        else: check(h()>60,'%s: panel starts expanded (%dpx)'%(name,h()))
        pg.click('#lindReviewFold'); a=h(); pg.click('#lindReviewFold'); c=h()
        check(a!=c and min(a,c)<=60,'%s: fold toggle works (%d <-> %d)'%(name,a,c))
        check(pg.evaluate("document.querySelector('#lindReviewFold').getAttribute('aria-expanded')")==('true' if h()>60 else 'false'),'%s: aria-expanded matches'%name)
        pg.evaluate("FieldTalk.talk('elder_woman',{source:'review'})"); pg.wait_for_timeout(150)
        check(pg.evaluate("getComputedStyle(document.querySelector('#msg')).display")=='block','%s: conversation is visible in review mode'%name)
        pg.evaluate("document.querySelector('#msg').click()")
        pg.close()
    check(not errs,'0 console errors %s'%errs[:2]); b.close()
sys.exit(1 if fails else 0)
