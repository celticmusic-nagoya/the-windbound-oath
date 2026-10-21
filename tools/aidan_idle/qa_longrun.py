#!/usr/bin/env python3
"""Real-time long-run: rAF interval stalls, blink schedule (gaps 3-6 s, no doubles), no console errors.  usage: qa_longrun.py [SECONDS] [BASE_URL]"""
import sys, json
from playwright.sync_api import sync_playwright
secs = float(sys.argv[1]) if len(sys.argv) > 1 else 60; base = sys.argv[2] if len(sys.argv) > 2 else 'http://127.0.0.1:8790'
JS = """(secs)=>new Promise(res=>{const iv=[],ev=[];let last=null,prev=-1;const c=document.getElementById('c');const t0=performance.now();
 const orig=P.drawAt.bind(P);P.drawAt=(t,e,b)=>{if(e!==prev){ev.push([+t.toFixed(3),e]);prev=e;}return orig(t,e,b)};
 const tick=n=>{if(last!==null)iv.push(n-last);last=n;if((n-t0)/1000<secs)requestAnimationFrame(tick);else res({iv,ev})};requestAnimationFrame(tick)})"""
with sync_playwright() as pw:
    b = pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']); pg = b.new_page(viewport={'width': 800, 'height': 700}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.goto(base + '/tools/aidan_idle/runtime/preview.html'); pg.wait_for_function('window.ready', timeout=60000)
    r = pg.evaluate(JS, secs); iv = sorted(r['iv']); n = len(iv)
    starts = [t for t, e in r['ev'] if e == 1]; gaps = [g for g in (round(b_ - a, 2) for a, b_ in zip(starts, starts[1:])) if g > 1]
    out = {'seconds': secs, 'frames': n, 'median_ms': round(iv[n // 2], 1), 'p99_ms': round(iv[int(n * .99)], 1), 'max_ms': round(iv[-1], 1), 'frames_over_100ms': sum(1 for x in iv if x > 100),
           'blinks': len([1 for t in starts]) // 2, 'blink_gaps_s': gaps, 'errors': errs}
    print(json.dumps(out, indent=1)); json.dump(out, open('/tmp/t01/ai/work/qa/longrun.json', 'w'), indent=1); b.close()
