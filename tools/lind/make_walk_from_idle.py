#!/usr/bin/env python3
"""Derive a 6-frame walk cycle from an NPC's own idle art by a displacement warp (keeps the painted look 1:1).
Same canvas as the idle PNG (so install_walk_frames.py accepts it), feet baseline unchanged, RGBA.
  body bob (upper rows), alternating foot lift + fore/aft step (lower rows, split left/right at the leg gap), light counter-sway.
usage: make_walk_from_idle.py <npc_id> <out_dir> [--frames 6]
Per-NPC geometry below (idle pixel coordinates). Add an entry for another painted idle to reuse it."""
import os, sys, math
import numpy as np, cv2
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
VIL = os.path.join(ROOT, 'img/field/lind/npc/villagers')
# split_x: x of the gap between the legs; top: y where the legs start to separate; bottom: foot baseline;
# bob/lift/step: peak displacement in idle px (drawn at ~0.04 scale: lift 70px ~ 2.7 screen px).
GEOM = {'merchant': dict(split_x=655, top=900, bottom=1127, bob=26, lift=64, lift_near=26, step=34, sway=7)}
def smooth(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
def frame(img, g, k, n):
    h, w = img.shape[:2]; ph = 2 * math.pi * k / n
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    s = math.sin(ph); c = math.cos(ph)
    wl = smooth((yy - g['top']) / (g['bottom'] - g['top']))             # 0 above the legs -> 1 at the feet
    wu = 1 - wl                                                         # upper body follows the bob
    side = smooth((xx - (g['split_x'] - 40)) / 80)                      # 0 = viewer-left leg, 1 = right leg
    lift_l = max(0, s) * g.get('lift_near', g['lift'])   # the near foot is the idle baseline: keep it within the hop tolerance
    lift_l = lift_l; lift_r = max(0, -s) * g['lift']     # foot that is off the ground
    step_l = s * g['step']; step_r = -s * g['step']                     # fore/aft
    bob = -abs(c if False else s) * g['bob']
    dy = bob * wu + wl * (-(lift_l * (1 - side) + lift_r * side))
    dx = wl * (step_l * (1 - side) + step_r * side) + wu * s * g['sway'] * smooth((g['top'] + 200 - yy) / 600)
    mx, my = xx - dx, yy - dy
    pm = img.astype(np.float32); pm[..., :3] *= pm[..., 3:4] / 255.0
    out = cv2.remap(pm, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = out[..., 3:4]; out[..., :3] = np.where(a > 0, out[..., :3] * 255.0 / np.maximum(a, 1e-3), 0)
    return np.clip(out, 0, 255).astype(np.uint8)
def main():
    if len(sys.argv) < 3: print(__doc__); sys.exit(2)
    npc, out = sys.argv[1], sys.argv[2]; n = int(sys.argv[sys.argv.index('--frames') + 1]) if '--frames' in sys.argv else 6
    img = cv2.cvtColor(cv2.imread(os.path.join(VIL, npc + '_idle.png'), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
    os.makedirs(out, exist_ok=True)
    for k in range(n):
        f = frame(img, GEOM[npc], k, n); cv2.imwrite(os.path.join(out, '%s_walk_%02d.png' % (npc, k + 1)), cv2.cvtColor(f, cv2.COLOR_RGBA2BGRA))
    print('wrote', n, 'frames to', out)
if __name__ == '__main__': main()
