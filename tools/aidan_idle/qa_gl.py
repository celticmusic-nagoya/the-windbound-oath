#!/usr/bin/env python3
"""GL runtime vs Python reference + PC / phone viewport checks.  usage: qa_gl.py MASTER OVERLAY_DIR OUT_DIR [BASE_URL]"""
import sys, os, io, json, base64, numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
from idle_motion import Idle, warp
from render_preview import composite_eyes
master, ov, out = sys.argv[1:4]; url = (sys.argv[4] if len(sys.argv) > 4 else 'http://127.0.0.1:8790') + '/tools/aidan_idle/runtime/preview.html?manual=1'
os.makedirs(out, exist_ok=True)
M = np.array(Image.open(master).convert('RGBA')); boxes = json.load(open(f'{ov}/boxes.json')); idle = Idle(M[..., 3]); BG = (56, 98, 82)
res = {'gl_vs_python': []}
def pngdata(page, js):
    d = page.evaluate(js); return np.array(Image.open(io.BytesIO(base64.b64decode(d.split(',')[1]))).convert('RGB'))
with sync_playwright() as pw:
    b = pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': 1400, 'height': 1250}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.goto(url); pg.wait_for_function('window.ready||window.err', timeout=60000); assert pg.evaluate('!window.err'), pg.evaluate('window.err')
    pg.evaluate('(()=>{const c=document.getElementById("c");c.width=1312;c.height=1199;})()')
    for t, eye in [(0, 0), (0.7, 0), (1.3, 0), (2.0, 2), (2.9, 4), (4.1, 0), (6.6, 3), (7.9, 0)]:
        a = pngdata(pg, f'(()=>{{P.drawAt({t},{eye},[{BG[0]},{BG[1]},{BG[2]}]);return document.getElementById("c").toDataURL("image/png")}})()').astype(int)
        base = composite_eyes(M, ov, boxes, eye); dx, dy = idle.field(t); f = warp(base, dx, dy)
        al = f[..., 3:4].astype(float) / 255; ref = (f[..., :3] * al + np.array(BG) * (1 - al)).astype(int)
        d = np.abs(a - ref); res['gl_vs_python'].append({'t': t, 'eye': eye, 'mean': round(float(d.mean()), 3), 'p99.9': int(np.percentile(d, 99.9)), 'max': int(d.max()), 'px>16': int((d.max(-1) > 16).sum())})
    # performance / stall: 300 draws timing (software GL = pessimistic)
    res['swiftshader_ms_per_frame_1312x1199'] = pg.evaluate('(()=>{const t0=performance.now();for(let i=0;i<30;i++){P.drawAt(i*.04,0);}P.gl.finish();return (performance.now()-t0)/30})()')
    # viewports: PC / phone portrait / landscape  (free-running player, real rAF)
    pg.close()
    for name, vp in {'pc': (1280, 720), 'phone_portrait': (390, 844), 'phone_landscape': (844, 390)}.items():
        ctx = b.new_context(viewport={'width': vp[0], 'height': vp[1]}, device_scale_factor=2 if 'phone' in name else 1, is_mobile='phone' in name, has_touch='phone' in name)
        p2 = ctx.new_page(); e2 = []; p2.on('pageerror', lambda e: e2.append(str(e))); p2.on('console', lambda m: e2.append(m.text) if m.type == 'error' else None)
        p2.goto(url.replace('?manual=1', '')); p2.wait_for_function('window.ready||window.err', timeout=60000)
        p2.wait_for_timeout(1200); p2.screenshot(path=f'{out}/vp_{name}_a.png'); p2.wait_for_timeout(1700); p2.screenshot(path=f'{out}/vp_{name}_b.png')
        ca = np.array(Image.open(f'{out}/vp_{name}_a.png').convert('RGB')).astype(int); cb = np.array(Image.open(f'{out}/vp_{name}_b.png').convert('RGB')).astype(int)
        res[name] = {'viewport': vp, 'errors': e2, 'animating(frame diff>0 px)': int((np.abs(ca - cb).max(-1) > 6).sum()), 'nonbg_px': int((np.abs(ca - ca[2, 2]).max(-1) > 10).sum())}
        ctx.close()
    res['errors'] = errs; b.close()
json.dump(res, open(f'{out}/qa_gl.json', 'w'), indent=1); print(json.dumps(res, indent=1))
