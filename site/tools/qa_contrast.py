#!/usr/bin/env python3
"""Contrast check for text placed over images (WEBSITE-REBUILD-01).

For each target, the text is made transparent (text-shadow removed too, so the
result is conservative), the area behind it is captured, and the contrast of the
text color against the brightest 1% of background pixels (P99 luminance) is
computed with the WCAG 2.x formula. Threshold: 4.5:1 (normal text), 3:1 for
large text (>= 24px, or >= 18.66px bold).

Usage (repo root served on :8765):  python3 site/tools/qa_contrast.py
"""
import io, json, sys
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

import os
URL = os.environ.get('SITE_URL', 'http://localhost:8765/site/')
TARGETS = ['.hero__catch', '.hero__actions .btn--ghost', '.story__theme', '.story__chapter', '.gallery-item__cap']
VIEWS = [(1440, 900), (1280, 800), (1024, 768), (390, 844), (360, 640), (844, 390)]


def lum(rgb):
    c = rgb / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def ratio(a, b):
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def main():
    rows, fails = [], 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for w, h in VIEWS:
            p = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=w < 800, has_touch=w < 800)
            p.route('**/fonts.g*/**', lambda r: r.abort())
            p.goto(URL)
            p.wait_for_timeout(800)
            p.evaluate("""async()=>{for(let y=0;y<document.body.scrollHeight;y+=300){scrollTo(0,y);await new Promise(r=>setTimeout(r,60))}scrollTo(0,0)}""")
            p.wait_for_timeout(800)
            for sel in TARGETS:
                el = p.query_selector(sel)
                if not el:
                    continue
                el.scroll_into_view_if_needed()
                p.wait_for_timeout(250)
                info = p.evaluate("""(s)=>{const e=document.querySelector(s);const cs=getComputedStyle(e);
                    return {color:cs.color,size:parseFloat(cs.fontSize),weight:parseInt(cs.fontWeight)}}""", sel)
                p.add_style_tag(content=f"{sel}{{color:transparent!important;text-shadow:none!important}}")
                p.wait_for_timeout(100)
                bb = el.bounding_box()
                # Inset 2px so 1px borders/outlines are not counted as text background.
                bb = {'x': bb['x'] + 2, 'y': bb['y'] + 2, 'width': bb['width'] - 4, 'height': bb['height'] - 4}
                shot = Image.open(io.BytesIO(p.screenshot(clip=bb))).convert('RGB')
                p.evaluate("(s)=>document.querySelectorAll('style').forEach(t=>{if(t.textContent.startsWith(s))t.remove()})", sel)
                bg = lum(np.asarray(shot, dtype=float)).ravel()
                rgb = np.array([int(x) for x in info['color'][info['color'].index('(') + 1:-1].split(',')[:3]], dtype=float)
                tl = float(lum(rgb[None, :])[0])
                worst = ratio(tl, float(np.percentile(bg, 99)))
                median = ratio(tl, float(np.median(bg)))
                large = info['size'] >= 24 or (info['size'] >= 18.66 and info['weight'] >= 700)
                need = 3.0 if large else 4.5
                ok = worst >= need
                fails += 0 if ok else 1
                rows.append({'view': f'{w}x{h}', 'target': sel, 'font_px': info['size'], 'need': need,
                             'p99_ratio': round(worst, 2), 'median_ratio': round(median, 2), 'result': 'PASS' if ok else 'FAIL'})
            p.close()
        b.close()
    for r in rows:
        print(f"{r['result']} {r['view']:9s} {r['target']:28s} {r['font_px']:5.1f}px need {r['need']} p99 {r['p99_ratio']:5.2f} median {r['median_ratio']:5.2f}")
    print(f"\n{len(rows) - fails} PASS / {fails} FAIL")
    json.dump(rows, open('/tmp/contrast.json', 'w'), indent=1)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
