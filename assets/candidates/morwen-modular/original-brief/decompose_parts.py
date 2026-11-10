#!/usr/bin/env python3
"""MORWEN-MODULAR-SPRITE-02: split an approved 96x128 (or 48x64) original into slot parts with a label map, and
prove that re-compositing the parts gives the original back pixel for pixel (initial QA condition).
  python3 decompose_parts.py --still <original.png> --labels <label map.png> --facing down|up --out <dir> --prefix <name>
Label map: same size, one exact colour per slot (PART_LABELS.json), alpha 0 outside the figure. Every opaque pixel of
the original must carry exactly one known label. Parts are written as <prefix>_<Slot>.png (pixels copied unchanged)
with parts_manifest.json (slot, z from equipment_slots.json draw order, bbox, anchor = rig attachment)."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image
ap = argparse.ArgumentParser()
for k in ('still', 'labels', 'out'): ap.add_argument('--' + k, type=Path, required=True)
ap.add_argument('--facing', required=True); ap.add_argument('--prefix', required=True)
ap.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[4])
a = ap.parse_args(); HERE = Path(__file__).resolve().parent
LB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in json.loads((HERE / 'PART_LABELS.json').read_text())['slots'].items()}
ORDER = {'down': ['Cape', 'Legs', 'Feet', 'Bottom', 'Inner', 'Body', 'Accessory', 'Bag', 'Outer', 'Hair', 'Head', 'HairAccessory'],
         'up': ['Cape', 'Legs', 'Feet', 'Bottom', 'Inner', 'Body', 'Bag', 'Outer', 'Hair', 'Accessory', 'Head', 'HairAccessory']}[a.facing]
x = np.array(Image.open(a.still).convert('RGBA')); lab = np.array(Image.open(a.labels).convert('RGBA'))
assert x.shape == lab.shape, 'label map size differs'
op = x[:, :, 3] > 0; known = np.zeros(op.shape, bool); fails = []
a.out.mkdir(parents=True, exist_ok=True); man = []
for z, slot in enumerate(ORDER):
    m = op & np.all(lab[:, :, :3] == LB[slot], axis=2) & (lab[:, :, 3] > 0)
    known |= m
    if not m.any(): continue
    part = np.zeros_like(x); part[m] = x[m]
    fn = f'{a.prefix}_{slot}.png'; Image.fromarray(part, 'RGBA').save(a.out / fn)
    ys, xs = np.where(m); man.append(dict(slot=slot, z=z, file=fn, px=int(m.sum()), bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]))
if (op & ~known).any(): fails.append(f'{int((op & ~known).sum())} opaque pixels without a slot label')
re = np.zeros_like(x)
for e in man:
    p = np.array(Image.open(a.out / e['file']).convert('RGBA')); m = p[:, :, 3] > 0; re[m] = p[m]
same = bool(np.array_equal(re, x)); Image.fromarray(re, 'RGBA').save(a.out / f'{a.prefix}_RECOMPOSITE.png')
if not same: fails.append(f'recomposite differs in {int(np.any(re != x, axis=2).sum())} pixels')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
rep = dict(still=str(a.still), still_sha256=sha(a.still), facing=a.facing, parts=man, recomposite_identical=same, fails=fails,
           result='PASS' if not fails else 'FAIL', rig='data/sprite-rig/morwen_rig_4dir.json', slots='data/sprite-rig/equipment_slots.json')
(a.out / 'parts_manifest.json').write_text(json.dumps(rep, indent=1), encoding='utf-8'); print(rep['result'], fails)
