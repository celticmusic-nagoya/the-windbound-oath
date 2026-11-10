#!/usr/bin/env python3
"""MORWEN-MODULAR-SPRITE-01: still frames 76C (back) / 77C (front), 96x128 and 48x64, plus every part as its own
transparent PNG and a parts manifest (slot, z order, bbox).  python3 build_stills.py --out ..   (writes ../76C, ../77C)"""
import argparse, json, os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import morwen_parts as MP
from partdraw import save_parts

ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True); a = ap.parse_args()
R = MP.ramps()
for view, tag, pre in (('back', '76C', 'morwen_up_76C'), ('front', '77C', 'morwen_down_77C')):
    d = a.out / tag; man = {'task': 'MORWEN-MODULAR-SPRITE-01', 'facing': 'up' if view == 'back' else 'down', 'still': 'neutral',
                           'ramps': R, 'parts': {}}
    for k, s in ((1, '96x128'), (2, '48x64')):
        im, P, order = MP.render(view, k, R)
        Image.fromarray(im, 'RGBA').save(d / f'{pre}_still_{s}.png')
        man['parts'][s] = save_parts(P, order, d / 'parts', pre, k)
    (d / f'parts_manifest_{tag}.json').write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding='utf-8')
    print(tag, len(man['parts']['96x128']), 'parts')
