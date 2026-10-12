# PC-side (headless Chromium) frame-time reference for dev_height_proto vs the existing Moss A2 map. NOT a substitute for Android hardware.
# Env: PORT, SECS (per run, default 8), THROTTLE (CPU slowdown, default 1), OUT (json path)
import os, json
from playwright.sync_api import sync_playwright
PORT = os.environ.get('PORT', '8765'); SECS = int(os.environ.get('SECS', '8')); THR = float(os.environ.get('THROTTLE', '1'))
OUT = os.environ.get('OUT', '/tmp/m19_perf.json')
VIEWS = {'pc': (1366, 768), 'portrait': (390, 844), 'landscape': (844, 390)}
JS_METER = """(secs)=>new Promise(res=>{const t=[];let last=performance.now(),end=last+secs*1000;
  function f(n){t.push(n-last);last=n;if(n<end)requestAnimationFrame(f);else{t.shift();t.sort((a,b)=>a-b);const sum=t.reduce((a,b)=>a+b,0),n1=Math.max(1,Math.floor(t.length*.01));
    res({frames:t.length,avgFps:+(1000*t.length/sum).toFixed(1),avgMs:+(sum/t.length).toFixed(2),p99Ms:+t[Math.floor(t.length*.99)].toFixed(2),maxMs:+t[t.length-1].toFixed(2),low1Fps:+(1000/(t.slice(-n1).reduce((a,b)=>a+b,0)/n1)).toFixed(1)});}}
  requestAnimationFrame(f);})"""
res = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    for view, (w, h) in VIEWS.items():
        ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=view != 'pc', has_touch=view != 'pc')
        pg = ctx.new_page(); ev = pg.evaluate
        if THR > 1: pg.context.new_cdp_session(pg).send('Emulation.setCPUThrottlingRate', {'rate': THR})
        pg.goto('http://localhost:%s/index.html?dev=1' % PORT); pg.wait_for_timeout(2500); ev('closeDialogue()')
        ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=15;enterMossForest()"); pg.wait_for_timeout(2500)
        for name, mp, path in (('dev_height_proto', 'dev_height_proto', [(2000, 250), (300, 1250)]), ('moss_a2', 'moss_forest_02_mossy_ravine', None)):
            ev("MossForest.enter({map:'%s'})" % mp); pg.wait_for_timeout(2600)
            ev("document.querySelector('#msg')&&(document.querySelector('#msg').style.display='none')")
            plan_ms = None
            if path:
                ev("MossForest.goFeet(%d,%d)" % path[0]); pg.wait_for_timeout(300)
                plan_ms = ev("FieldNavigation.status.milliseconds"); expanded = ev("FieldNavigation.status.expanded")
            # keep moving during the measurement: hold a key and flip direction every second
            pg.evaluate("window.__mv=setInterval(()=>{const k=['ArrowRight','ArrowDown','ArrowLeft','ArrowUp'];window.__i=((window.__i||0)+1)%4;window.dispatchEvent(new KeyboardEvent('keyup',{key:k[(window.__i+3)%4]}));window.dispatchEvent(new KeyboardEvent('keydown',{key:k[window.__i]}));},1000)")
            m = ev(JS_METER, SECS); ev("clearInterval(window.__mv);['ArrowRight','ArrowDown','ArrowLeft','ArrowUp'].forEach(k=>window.dispatchEvent(new KeyboardEvent('keyup',{key:k})))")
            m['nodes'] = ev("document.querySelectorAll('#forestWorld *').length"); m['heap'] = ev("performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):null")
            if plan_ms is not None: m['longPathPlanMs'] = round(plan_ms, 1); m['longPathExpanded'] = expanded
            res['%s/%s' % (view, name)] = m; print(view, name, m)
        ctx.close()
    b.close()
res['_meta'] = {'throttle': THR, 'secsPerRun': SECS, 'note': 'headless Chromium on a cloud container; reference only, Android hardware is NOT measured'}
json.dump(res, open(OUT, 'w'), indent=1)
