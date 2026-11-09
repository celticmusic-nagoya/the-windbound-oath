from playwright.sync_api import sync_playwright
import sys
with sync_playwright() as p:
    b=p.chromium.launch()
    errs=[]
    for name,vp,dpr in (('pc',{'width':1280,'height':900},1),('android',{'width':412,'height':915},2.625)):
        pg=b.new_page(viewport=vp,device_scale_factor=dpr)
        pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(''+sys.argv[1]+''); pg.wait_for_timeout(1200)
        pg.screenshot(path=f'qa69/shot_{name}_loop.png',full_page=False)
        pg.select_option('#mode','seam'); pg.select_option('#bg','dark'); pg.wait_for_timeout(600)
        pg.screenshot(path=f'qa69/shot_{name}_seam_dark.png')
        pg.select_option('#mode','strip'); pg.select_option('#ver','68'); pg.wait_for_timeout(600)
        pg.screenshot(path=f'qa69/shot_{name}_strip.png',full_page=True)
    print('errors',errs)
    b.close()
