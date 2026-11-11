#!/usr/bin/env python3
"""MORWEN-PRODUCTION-73 DEV preview (single HTML, PC + Android): Morwen 72 right walk vs. provisional left mirror,
scale vs. Aidan / Fiona field idle art, foot anchor, distance stride vs. game speed (foot-slide meter).
  python3 tools/morwen/make_m73_preview.py --out <file.html>"""
import argparse, base64, io, json, os
from PIL import Image
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
def b64(path, crop=None):
    im = Image.open(os.path.join(ROOT, path)).convert('RGBA')
    if crop: im = im.crop(crop)
    buf = io.BytesIO(); im.save(buf, 'PNG'); return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
def asset(js, key):
    import re
    s = open(os.path.join(ROOT, js), encoding='utf-8').read()
    m = re.search(r'"%s": \{\s*"path": "([^"?]+)[^"]*",\s*"width": (\d+),\s*"height": (\d+),\s*"bounds": \[\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\],\s*"anchor": \[\s*(\d+),\s*(\d+)\s*\],\s*"scale": ([\d.]+)' % key, s)
    p, w, h, x0, y0, x1, y1, ax, ay, sc = m.groups()
    return dict(path=p, w=int(w), h=int(h), bounds=[int(x0), int(y0), int(x1), int(y1)], anchor=[int(ax), int(ay)], scale=float(sc))
ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); a = ap.parse_args()
base = 'assets/candidates/morwen-right-walk/72/'
D = {'m48': [b64(base + f'morwen_right_walk_{i:02d}_48x64.png') for i in range(6)],
     'm96': [b64(base + f'morwen_right_walk_{i:02d}_96x128.png') for i in range(6)],
     'ground': b64('img/field/moss/art/ground_moss.png', (0, 0, 384, 192))}
refs = {}
for who, js, key in (('aidan', 'js/field/aidan-field-assets.js', 'aidan_idle_right'), ('fiona', 'js/field/fiona-field-assets.js', 'fiona_idle_right')):
    A = asset(js, key); A['img'] = b64(A['path']); A['charH'] = round((A['bounds'][3] - A['bounds'][1]) * A['scale'], 1); refs[who] = A
html = open(os.path.join(os.path.dirname(__file__), 'm73_preview_template.html'), encoding='utf-8').read()
open(a.out, 'w', encoding='utf-8').write(html.replace('__D__', json.dumps(D)).replace('__REF__', json.dumps(refs)))
print(a.out, {k: (v['charH'], v['scale']) for k, v in refs.items()})
