#!/usr/bin/env python3
"""Export the Aidan idle v1 runtime assets (candidate; not wired into the game).
usage: export_assets.py MASTER.png OVERLAY_DIR OUT_DIR
  OUT_DIR/aidan_idle_master.png   byte-identical copy of the official MASTER (the MASTER itself is never touched)
  OUT_DIR/eyes/overlay_{L,R}_s{1..4}.png, boxes
  OUT_DIR/weights_{a,b,c}.png     half-res region weights (8-bit RGB): a=torso,head,hair  b=arms-group,cloakL,cloakR  c=flapsL,flapsR,skirt
  OUT_DIR/idle_v1.json            parameters / schedule (the runtime mirrors idle_motion.Idle.field)
"""
import sys, os, json, shutil, hashlib, numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from idle_motion import Idle, smoothstep, YY, P

def main():
    master, ov, out = sys.argv[1:4]
    os.makedirs(out + '/eyes', exist_ok=True)
    shutil.copyfile(master, out + '/aidan_idle_master.png')
    for e in 'LR':
        for s in (1, 2, 3, 4): shutil.copyfile(f'{ov}/overlay_{e}_s{s}.png', f'{out}/eyes/overlay_{e}_s{s}.png')
    M = np.array(Image.open(master).convert('RGBA')); I = Idle(M[..., 3]); W = I.W
    ff = lambda: (1 - smoothstep(930, 1060, YY)); fs = (1 - smoothstep(930, 1020, YY))
    chans = {'a': [I.w_torso, I.w_head, I.w_hair], 'b': [I.w_group, W['cloakL'], W['cloakR']], 'c': [W['flapsL'] * ff(), W['flapsR'] * ff(), W['skirt'] * fs]}
    for k, ch in chans.items():
        a = np.dstack([cv2.resize(np.clip(c, 0, 1), (M.shape[1] // 2, M.shape[0] // 2), interpolation=cv2.INTER_AREA) for c in ch])
        Image.fromarray((a * 255 + 0.5).astype(np.uint8), 'RGB').save(f'{out}/weights_{k}.png', optimize=True)
    meta = {'version': 1, 'master': 'aidan_idle_master.png', 'masterSha256': hashlib.sha256(open(master, 'rb').read()).hexdigest(), 'size': [M.shape[1], M.shape[0]],
            'loopSeconds': P, 'eyeBoxes': json.load(open(f'{ov}/boxes.json')), 'blink': {'seq': [[1, 30], [2, 30], [3, 35], [4, 70], [3, 35], [2, 30], [1, 30]], 'minGap': 3000, 'maxGap': 6000},
            'weights': ['weights_a.png', 'weights_b.png', 'weights_c.png'], 'weightScale': 0.5,
            'foot': [None, None]}
    # foot anchor: bottom-centre of the opaque boots (lowest opaque row; mean x of that row band)
    ys, xs = np.nonzero(M[..., 3] > 128); y0 = int(ys.max()); band = xs[ys > y0 - 6]
    meta['foot'] = [int(band.mean()), y0]
    json.dump(meta, open(out + '/idle_v1.json', 'w'), indent=1)
    print({k: os.path.getsize(f'{out}/{k}') for k in os.listdir(out) if os.path.isfile(f'{out}/{k}')})

if __name__ == '__main__': main()
