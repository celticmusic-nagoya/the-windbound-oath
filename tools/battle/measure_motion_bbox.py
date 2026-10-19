#!/usr/bin/env python3
"""Write `aspect` (w/h) and `bbox` ([x0,x1] normalised, max over all frames, alpha>128) into the manifest entries of one actor.
BattleMotion uses them (with `scale`) to keep a scaled figure inside the battle screen. Usage: measure_motion_bbox.py goblin_raider"""
import json, sys
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]; MAN = ROOT / 'img/battle/motion-manifest.json'
actor = sys.argv[1]; t = MAN.read_text(); m = json.loads(t); ind = 2 if '\n  "' in t else 4
for st, d in m['motions'][actor].items():
    x0, x1, a = 1.0, 0.0, None
    for n in range(1, d['frames'] + 1):
        im = Image.open((ROOT / m['base'] / d['dir'] / d['pattern'].replace('{n}', '%02d' % n)).resolve()).convert('RGBA'); w, h = im.size; a = round(w / h, 4)
        al = im.getchannel('A').point(lambda v: 255 if v > 128 else 0); bb = al.getbbox()
        if bb: x0 = min(x0, bb[0] / w); x1 = max(x1, bb[2] / w)
    d['aspect'] = a; d['bbox'] = [round(x0, 4), round(x1, 4)]; print(actor, st, d['aspect'], d['bbox'])
MAN.write_text(json.dumps(m, indent=ind, ensure_ascii=False) + ('\n' if t.endswith('\n') else ''))
